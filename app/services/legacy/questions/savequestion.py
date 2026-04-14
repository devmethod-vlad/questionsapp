from app.db.legacy_db import db
import datetime
import os
from questionsapp.models import OrderMess, OrderStatus, OrderSpace, Spaces, TelChatInfoSpace, OrderUnionRole
from questionsapp.models import AppConfig, AnswerMess, UserTelegramInfo, Attachment, User
from questionsapp.models import OrderAttachment, SpaceUnionRole, UnionRole, UserBaseRole, SpaceUnionRoleActive
from questionsapp.models import TelegramTempMess, FeedbackQuestion
from app.services.common.telegram import tg_post
from app.core.legacy_runtime import legacy_app as app
from pytz import timezone
from app.services.legacy.roles.getrole import get_role
from app.services.files.uploads import UploadLike

east = timezone('Europe/Moscow')

DUPLICATE_LOOKBACK_SECONDS = 2


def _normalize_optional_int(value):
    if value in (None, '', 'None', 'null'):
        return None
    return int(value)


def _normalize_int_flag(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalize_spacekey(value):
    if isinstance(value, str):
        value = value.strip()
        if value == '':
            return None
        return value
    return None


def _build_attachments(question_id):
    attachments = []
    for at_item in OrderAttachment.query.filter(OrderAttachment.orderid == int(question_id)).all():
        attach_rec = Attachment.query.filter(Attachment.id == at_item.attachid).first()
        if attach_rec is not None:
            attachments.append({
                'type': attach_rec.type,
                'path': attach_rec.path,
                'created_at': at_item.created_at,
                'attachid': attach_rec.id,
            })
    return attachments


def _resolve_space(spacekey):
    space_id = int(app.config['NULLSPACE']['id'])
    space_title = app.config['NULLSPACE']['title']

    if spacekey and spacekey != '0':
        space_rec = Spaces.query.filter_by(spacekey=spacekey).first()
        if space_rec is not None:
            space_id = space_rec.id
            space_title = space_rec.title

    return space_id, space_title


def _question_feedback_flag(orderid):
    return FeedbackQuestion.query.filter_by(orderid=int(orderid)).first() is not None


def _find_recent_duplicate_question(userid, message, space_id, isfeedback):
    threshold = datetime.datetime.now() - datetime.timedelta(seconds=DUPLICATE_LOOKBACK_SECONDS)
    candidates = (
        OrderMess.query
        .filter(
            OrderMess.userid == int(userid),
            OrderMess.text == message,
            OrderMess.created_at >= threshold,
        )
        .order_by(OrderMess.id.desc())
        .all()
    )

    for candidate in candidates:
        order_space = OrderSpace.query.filter_by(orderid=int(candidate.id)).first()
        if order_space is None or int(order_space.spaceid) != int(space_id):
            continue

        if _question_feedback_flag(candidate.id) != (int(isfeedback) == 1):
            continue

        return candidate

    return None


def _send_new_question_notifications(question_id, question_user_role, space_id, space_title, isfeedback):
    send_mess_flag = True
    if app.config['TEL_SEND_NEWMESS']:
        if question_user_role == 'admin' or question_user_role == 'redactor':
            if not app.config['NOTIFY_SELF_ORDER']:
                send_mess_flag = False
    else:
        send_mess_flag = False

    if not send_mess_flag:
        return

    check_tel_chat = TelChatInfoSpace.query.filter_by(spaceid=space_id).first()
    now_time = datetime.datetime.now(east)

    if int(isfeedback) != 1:
        tel_message = '💡 <b>Новый вопрос </b><em>' + str(question_id) + '</em><b> :</b>\n\n🗂 <b>По разделу: </b><em>' + space_title + '</em>\n🎯 <b>Источник: </b><em>Веб-версия</em>\n<b>Время: </b><em>' + now_time.strftime("%d-%m-%Y, %H:%M") + '</em> \n\n<b><a href = "' + app.config['QUESTIONS_MAIN_PAGE'] + '">Перейти</a></b>'
    else:
        tel_message = '💡 <b>Новое сообщение с обратной связью </b><em>' + str(question_id) + '</em><b> :</b>\n\n🎯 <b>Источник: </b><em>Веб-версия</em>\n<b>Время: </b><em>' + now_time.strftime("%d-%m-%Y, %H:%M") + '</em> \n\n<b><a href = "' + app.config['QUESTIONS_MAIN_PAGE'] + '">Перейти</a></b>'

    try:
        tg_post(
            app.config['TEL_SENDMESS_URL'],
            json_body={
                'chat_id': app.config['TEL_INFO_CHAT'],
                'text': tel_message,
                'parse_mode': 'HTML'
            },
            timeout=(10.0, 40.0),
            socks_proxy=app.config['TEL_SOCKS_PROXY'],
        )
    except Exception as e:
        print(str(e))

    if check_tel_chat is not None:
        try:
            tg_post(
                app.config['TEL_SENDMESS_URL'],
                json_body={
                    'chat_id': check_tel_chat.chatid,
                    'text': tel_message,
                    'parse_mode': 'HTML'
                },
                timeout=(10.0, 40.0),
                socks_proxy=app.config['TEL_SOCKS_PROXY'],
            )
        except Exception as e:
            print(str(e))


def _send_question_update_notification(notify_userid, question_user_role, question_id):
    if notify_userid == 0:
        return

    if question_user_role == 'admin' or question_user_role == 'redactor':
        return

    check_user_telinfo = UserTelegramInfo.query.filter_by(userid=notify_userid).first()
    if check_user_telinfo is None or not app.config['TEL_SEND_UPDTMESS']:
        return

    user_message = '💡 <b>Пользователь обновил вопрос № ' + str(question_id) + '</b>'
    try:
        req = tg_post(
            app.config['TEL_SENDMESS_URL'],
            json_body={
                'chat_id': check_user_telinfo.tlgmid,
                'text': user_message,
                'parse_mode': 'HTML'
            },
            timeout=(10.0, 40.0),
            socks_proxy=app.config['TEL_SOCKS_PROXY'],
        )
        send_resp = req.json()

        if 'ok' in send_resp:
            if send_resp['ok']:
                messid = send_resp['result']['message_id']
                new_mess = TelegramTempMess(telid=str(check_user_telinfo.tlgmid), messid=str(messid))
                db.session.add(new_mess)
                db.session.commit()

    except Exception as e:
        print(str(e))


def _send_space_change_notification(question_id, space_title):
    try:
        user_message = '💡 <b>Вопрос № ' + str(question_id) + '\nПривязан к пространству: <em>' + space_title + '</em></b>\n\n<a href = "' + app.config['QUESTIONS_MAIN_PAGE'] + '">Перейти</a>'
        tg_post(
            app.config['TEL_SENDMESS_URL'],
            json_body={
                'chat_id': app.config['TEL_INFO_CHAT'],
                'text': user_message,
                'parse_mode': 'HTML'
            },
            timeout=(10.0, 40.0),
            socks_proxy=app.config['TEL_SOCKS_PROXY'],
        )
    except Exception as e:
        print(str(e))


def save_question(params):

    try:
        orderid = _normalize_optional_int(params["orderid"])
        userid = _normalize_optional_int(params["userid"])
        spacekey = _normalize_spacekey(params["spacekey"])
        message = params["question_text"]
        unionroleid = _normalize_int_flag(params["unionroleid"], default=0)
        uploaded_files: list[UploadLike] = params["question_files"] or []
        isfeedback = _normalize_int_flag(params["isfeedback"], default=0)

        if message and userid:
            fileflag = 'notexist' if len(uploaded_files) == 0 else 'exist'

            check_role = UserBaseRole.query.filter_by(userid=int(userid)).first()
            role = get_role(check_role.roleid)

            question_id = 0
            question_userid = 0
            new_flag = False
            is_question_text_change = False
            is_space_change = False
            notify_userid = 0
            send_new_question_notify = False
            send_update_notify = False
            question_user_role = ''
            space_id = int(app.config['NULLSPACE']['id'])
            space_title = app.config['NULLSPACE']['title']

            # Session in Flask-SQLAlchemy/SQLAlchemy 2.x usually enters a transaction on the first query.
            # Because of that we do not open an explicit begin() block here and instead rely on a single
            # commit()/rollback() pair for the whole save flow.
            User.query.filter_by(id=int(userid)).with_for_update().first()

            if orderid is not None:
                check_order = OrderMess.query.filter(OrderMess.id == int(orderid)).first()
                if check_order is not None:
                    question_id = check_order.id
                    question_userid = check_order.userid

                    if check_order.text != message:
                        is_question_text_change = True
                        check_order.text = message
                        db.session.add(check_order)
            else:
                space_id, space_title = _resolve_space(spacekey)
                duplicate_question = _find_recent_duplicate_question(userid=userid, message=message,
                                                                    space_id=space_id,
                                                                    isfeedback=isfeedback)
                if duplicate_question is not None:
                    question_id = duplicate_question.id
                    question_userid = duplicate_question.userid
                else:
                    new_question = OrderMess(userid=int(userid), text=message)
                    db.session.add(new_question)
                    db.session.flush()

                    if isfeedback == 1:
                        new_fq = FeedbackQuestion(orderid=new_question.id)
                        db.session.add(new_fq)

                    new_flag = True
                    question_userid = int(userid)
                    question_id = new_question.id
                    if isfeedback == 1:
                        new_quest_status = OrderStatus(orderid=new_question.id,
                                                       statusid=app.config['QUESTION_STATUS']['archive']['id'])
                    else:
                        new_quest_status = OrderStatus(orderid=new_question.id,
                                                       statusid=app.config['QUESTION_STATUS']['create']['id'])
                    db.session.add(new_quest_status)

            check_space = OrderSpace.query.filter_by(orderid=int(question_id)).first()

            if orderid is not None or not new_flag:
                space_id, space_title = _resolve_space(spacekey)

            if spacekey:
                if check_space:
                    if not new_flag and int(space_id) != check_space.spaceid:
                        is_space_change = True

                    check_space.spaceid = int(space_id)
                    db.session.add(check_space)
                else:
                    new_quest_space = OrderSpace(orderid=int(question_id), spaceid=int(space_id))
                    db.session.add(new_quest_space)
                    if not new_flag:
                        is_space_change = True
            else:
                if check_space is None:
                    new_quest_space = OrderSpace(orderid=int(question_id), spaceid=space_id)
                    db.session.add(new_quest_space)
                    if not new_flag:
                        is_space_change = True

            space_unionroles_id = []
            for item in SpaceUnionRole.query.filter(SpaceUnionRole.spaceid == space_id).all():
                space_unionroles_id.append(item.unionroleid)

            space_active = False
            check_space_active = SpaceUnionRoleActive.query.filter_by(spaceid=space_id).first()

            if check_space_active is not None:
                if check_space_active.active == 1:
                    space_active = True
            else:
                if len(space_unionroles_id) > 0:
                    new_space_active = SpaceUnionRoleActive(spaceid=space_id, active=1)
                    db.session.add(new_space_active)
                    space_active = True

            check_unionrole = OrderUnionRole.query.filter_by(orderid=question_id).first()

            if space_active:
                question_unionrole_id = app.config['NULLROLE']['id']

                if int(unionroleid) in space_unionroles_id:
                    question_unionrole_id = int(unionroleid)

                if check_unionrole is not None:
                    check_unionrole.unionroleid = question_unionrole_id
                    db.session.add(check_unionrole)
                else:
                    new_quest_unionrole = OrderUnionRole(orderid=question_id, unionroleid=question_unionrole_id)
                    db.session.add(new_quest_unionrole)
            else:
                if space_id == int(app.config['NULLSPACE']['id']) and new_flag:
                    if unionroleid:
                        if int(unionroleid) != 0 and role == 'personal':
                            check_unionrole = UnionRole.query.filter_by(id=int(unionroleid)).first()
                            if check_unionrole is not None:
                                new_unionrole = OrderUnionRole(orderid=question_id, unionroleid=int(unionroleid))
                                db.session.add(new_unionrole)
                else:
                    if check_unionrole is not None:
                        db.session.delete(check_unionrole)

            quest_user_role_rec = UserBaseRole.query.filter_by(userid=int(question_userid)).first()
            question_user_role = get_role(quest_user_role_rec.roleid)

            if new_flag:
                send_new_question_notify = True
            else:
                check_status = OrderStatus.query.filter_by(orderid=int(question_id)).first()
                check_answer = AnswerMess.query.filter_by(orderid=question_id).first()

                if check_status is not None and check_status.statusid == int(app.config['QUESTION_STATUS']['back_in_work']['id']):
                    if is_question_text_change or len(uploaded_files) != 0:
                        if int(userid) == question_userid and check_answer is not None:
                            notify_userid = check_answer.userid

                if notify_userid != 0:
                    send_update_notify = True

            if len(uploaded_files) != 0:
                app_conf_rec = AppConfig.query.first()
                if not os.path.isdir(app.config['QUESTION_ATTACHMENTS']):
                    os.mkdir(app.config['QUESTION_ATTACHMENTS'])
                user_path = os.path.join(app.config['QUESTION_ATTACHMENTS'], str(userid))
                if not os.path.isdir(user_path):
                    os.mkdir(user_path)
                user_order_path = os.path.join(user_path, str(question_id))
                if not os.path.isdir(user_order_path):
                    os.mkdir(user_order_path)

                dirfiles = os.listdir(user_order_path)
                for file_item in uploaded_files:
                    filename = file_item.filename
                    filename = filename.strip().replace(" ", "_")
                    file_size = round(file_item.size_bytes / 10000000, 3)
                    file_ext = filename.split('.')[-1].lower()
                    if file_size < int(app_conf_rec.uploadsize):
                        if filename in dirfiles:
                            filename = 'copy-' + filename

                        file_item.save_to(os.path.join(user_order_path, filename))

                        attach_type = ''
                        if file_ext in app.config['EXT_DICT']['imageExtension']:
                            attach_type = 'image'
                        elif file_ext in app.config['EXT_DICT']['wordExtension']:
                            attach_type = 'word'
                        elif file_ext in app.config['EXT_DICT']['textDocExtension']:
                            attach_type = 'textdoc'
                        elif file_ext in app.config['EXT_DICT']['excelExtension']:
                            attach_type = 'excel'
                        elif file_ext in app.config['EXT_DICT']['videoExtension']:
                            attach_type = 'video'
                        elif file_ext in app.config['EXT_DICT']['audioExtension']:
                            attach_type = 'audio'
                        elif file_ext in app.config['EXT_DICT']['pdfExtensions']:
                            attach_type = 'pdf'
                        elif file_ext in app.config['EXT_DICT']['animExtension']:
                            attach_type = 'animation'
                        new_attach = Attachment(type=attach_type, path=filename, caption='', public=1)
                        db.session.add(new_attach)
                        db.session.flush()
                        new_quest_attach = OrderAttachment(attachid=new_attach.id, orderid=question_id)
                        db.session.add(new_quest_attach)

            db.session.commit()

            attachments = _build_attachments(question_id)

            if send_new_question_notify:
                _send_new_question_notifications(question_id=question_id, question_user_role=question_user_role,
                                                 space_id=space_id, space_title=space_title,
                                                 isfeedback=isfeedback)
            elif send_update_notify:
                _send_question_update_notification(notify_userid=notify_userid,
                                                   question_user_role=question_user_role,
                                                   question_id=question_id)

            if is_space_change:
                _send_space_change_notification(question_id=question_id, space_title=space_title)

            return {'status': 'ok', 'info': {'files': {'flag': fileflag}, 'messid': question_id, 'text': message,
                                             'attachments': attachments}}
        else:
            return {'status': 'error', 'error_mess': 'WARN: No params'}

    except Exception as e:
        db.session.rollback()
        print(str(e))
        return {'status': 'ok', 'error_mess': str(e)}
