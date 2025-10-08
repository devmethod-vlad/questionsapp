from database import db
import datetime
import os
import requests
from questionsapp.models import OrderMess, OrderStatus, OrderSpace, Spaces, TelChatInfoSpace, OrderUnionRole
from questionsapp.models import AppConfig, AnswerMess, UserTelegramInfo, Attachment
from questionsapp.models import OrderAttachment, SpaceUnionRole, UnionRole, UserBaseRole, SpaceUnionRoleActive
from questionsapp.models import TelegramTempMess, FeedbackQuestion
from flask import current_app as app
from pytz import timezone
from questionsapp.services.roles.getrole import get_role

east = timezone('Europe/Moscow')

def save_question(params):

    try:
        orderid = params["orderid"]
        userid = params["userid"]
        spacekey = params["spacekey"]
        message = params["question_text"]
        unionroleid = params["unionroleid"]
        uploaded_files = params["question_files"]
        isfeedback = params["isfeedback"]

        if message and userid:
            check_role = UserBaseRole.query.filter_by(userid=int(userid)).first()

            role = get_role(check_role.roleid)

            question_id = 0

            question_userid = 0

            new_flag = False

            is_question_text_change = False

            if orderid is not None:
                check_order = OrderMess.query.filter(OrderMess.id == int(orderid)).first()
                if check_order is not None:
                    question_id = check_order.id
                    question_userid = check_order.userid

                    if check_order.text != message:
                        is_question_text_change = True
                        check_order.text = message
                        db.session.add(check_order)
                        db.session.commit()
            else:

                new_question = OrderMess(userid=int(userid), text=message)
                db.session.add(new_question)
                db.session.commit()

                if isfeedback:
                    if int(isfeedback) == 1:
                        new_fq = FeedbackQuestion(orderid=new_question.id)
                        db.session.add(new_fq)
                        db.session.commit()

                new_flag = True
                question_userid = int(userid)
                question_id = new_question.id
                if int(isfeedback) == 1:
                    new_quest_status = OrderStatus(orderid=new_question.id,
                                                   statusid=app.config['QUESTION_STATUS']['archive']['id'])
                else:
                    new_quest_status = OrderStatus(orderid=new_question.id,
                                                   statusid=app.config['QUESTION_STATUS']['create']['id'])
                db.session.add(new_quest_status)
                db.session.commit()

            is_space_change = False

            check_space = OrderSpace.query.filter_by(orderid=int(question_id)).first()

            space_id = int(app.config['NULLSPACE']['id'])
            space_title = app.config['NULLSPACE']['title']

            if spacekey:
                # print("if spacekey")
                if spacekey != '0':
                    # print("if spacekey != '0'")
                    space_rec = Spaces.query.filter_by(spacekey=spacekey.strip()).first()
                    space_id = space_rec.id
                    # print("space_id: ", space_id)
                    space_title = space_rec.title
                    # print("space_title: ", space_title)

                if check_space:
                    # print("if check_space")

                    if not new_flag and int(space_id) != check_space.spaceid:
                            is_space_change = True

                    check_space.spaceid = int(space_id)
                    db.session.commit()
                else:
                    new_quest_space = OrderSpace(orderid=int(question_id), spaceid=int(space_id))
                    db.session.add(new_quest_space)
                    db.session.commit()
                    if not new_flag:
                        is_space_change = True

            else:
                if check_space is None:
                    new_quest_space = OrderSpace(orderid=int(question_id), spaceid=space_id)
                    db.session.add(new_quest_space)
                    db.session.commit()
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
                    db.session.commit()
                    space_active = True

            check_unionrole = OrderUnionRole.query.filter_by(orderid=question_id).first()

            if space_active:

                question_unionrole_id = app.config['NULLROLE']['id']

                if int(unionroleid) in space_unionroles_id:
                    question_unionrole_id = int(unionroleid)

                if check_unionrole is not None:
                    check_unionrole.unionroleid = question_unionrole_id
                    db.session.commit()
                else:

                    new_quest_unionrole = OrderUnionRole(orderid=question_id, unionroleid=question_unionrole_id)
                    db.session.add(new_quest_unionrole)
                    db.session.commit()
            else:
                if space_id == int(app.config['NULLSPACE']['id']) and new_flag:
                    if unionroleid:
                        if int(unionroleid) != 0 and role == 'personal':
                            check_unionrole = UnionRole.query.filter_by(id=int(unionroleid)).first()
                            if check_unionrole is not None:
                                new_unionrole = OrderUnionRole(orderid=question_id, unionroleid=int(unionroleid))
                                db.session.add(new_unionrole)
                                db.session.commit()
                else:
                    if check_unionrole is not None:
                        db.session.delete(check_unionrole)
                        db.session.commit()

            quest_user_role_rec = UserBaseRole.query.filter_by(userid=int(question_userid)).first()

            question_user_role = get_role(quest_user_role_rec.roleid)

            if new_flag:
                send_mess_flag = True
                if app.config['TEL_SEND_NEWMESS']:
                    if question_user_role == 'admin' or question_user_role == 'redactor':
                        if not app.config['NOTIFY_SELF_ORDER']:
                            send_mess_flag = False
                else:
                    send_mess_flag = False

                if send_mess_flag:
                    check_tel_chat = TelChatInfoSpace.query.filter_by(spaceid=space_id).first()
                    now_time = datetime.datetime.now(east)

                    if int(isfeedback) != 1:
                        tel_message = '💡 <b>Новый вопрос </b><em>' + str(question_id) + '</em><b> :</b>\n\n🗂 <b>По разделу: </b><em>' + space_title + '</em>\n🎯 <b>Источник: </b><em>Веб-версия</em>\n<b>Время: </b><em>' + now_time.strftime("%d-%m-%Y, %H:%M") + '</em> \n\n<b><a href = "' + app.config['QUESTIONS_MAIN_PAGE'] + '">Перейти</a></b>'
                    else:
                        tel_message = '💡 <b>Новое сообщение с обратной связью </b><em>' + str(question_id) + '</em><b> :</b>\n\n🎯 <b>Источник: </b><em>Веб-версия</em>\n<b>Время: </b><em>' + now_time.strftime("%d-%m-%Y, %H:%M") + '</em> \n\n<b><a href = "' + app.config['QUESTIONS_MAIN_PAGE'] + '">Перейти</a></b>'
                    try:
                        requests.post(app.config['TEL_SENDMESS_URL'],
                                      json={'chat_id': app.config['TEL_INFO_CHAT'], 'text': tel_message,
                                            'parse_mode': 'HTML'})

                    except Exception as e:
                        print(str(e))
                    if check_tel_chat is not None:
                        try:
                            requests.post(app.config['TEL_SENDMESS_URL'],
                                          json={'chat_id': check_tel_chat.chatid, 'text': tel_message,
                                                'parse_mode': 'HTML'})
                        except Exception as e:
                            print(str(e))

            else:
                notify_userid = 0

                check_status = OrderStatus.query.filter_by(orderid=int(question_id)).first()

                check_answer = AnswerMess.query.filter_by(orderid=question_id).first()

                if check_status.statusid == int(app.config['QUESTION_STATUS']['back_in_work']['id']):
                    if is_question_text_change or len(uploaded_files) != 0:
                        if int(userid) == question_userid and check_answer is not None:
                            notify_userid = check_answer.userid

                if notify_userid != 0:

                    if question_user_role != 'admin' and question_user_role != 'redactor':
                        check_user_telinfo = UserTelegramInfo.query.filter_by(userid=notify_userid).first()

                        if check_user_telinfo is not None and app.config['TEL_SEND_UPDTMESS']:
                            user_message = '💡 <b>Пользователь обновил вопрос № ' + str(question_id) + '</b>'
                            try:
                                req = requests.post(app.config['TEL_SENDMESS_URL'],
                                              json={'chat_id': check_user_telinfo.tlgmid, 'text': user_message,
                                                    'parse_mode': 'HTML'})
                                send_resp = req.json()

                                if 'ok' in send_resp:
                                    if send_resp['ok']:
                                        messid = send_resp['result']['message_id']

                                        new_mess = TelegramTempMess(telid=str(check_user_telinfo.tlgmid),
                                                                    messid=str(messid))
                                        db.session.add(new_mess)
                                        db.session.commit()

                            except Exception as e:
                                print(str(e))

            if len(uploaded_files) == 0:
                fileflag = 'notexist'
            else:
                app_conf_rec = AppConfig.query.first()
                fileflag = 'exist'
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
                    file_size = round(file_item.content_length / 10000000, 3)
                    file_ext = filename.split('.')[-1].lower()
                    if file_size < int(app_conf_rec.uploadsize):
                        if filename in dirfiles:
                            filename = 'copy-' + filename

                        file_item.save(os.path.join(user_order_path, filename))

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
                        db.session.commit()
                        new_quest_attach = OrderAttachment(attachid=new_attach.id, orderid=question_id)
                        db.session.add(new_quest_attach)

            attachments = []

            for at_item in OrderAttachment.query.filter(OrderAttachment.orderid == int(question_id)).all():
                attach_rec = Attachment.query.filter(Attachment.id == at_item.attachid).first()
                attachments.append({'type': attach_rec.type, 'path': attach_rec.path, 'created_at': at_item.created_at,
                                    'attachid': attach_rec.id})

            db.session.commit()

            # print("is_space_change: ", is_space_change)

            if is_space_change:
                try:
                    user_message = '💡 <b>Вопрос № ' + str(question_id) + '\nПривязан к пространству: <em>'+space_title+'</em></b>\n\n<a href = "' + app.config['QUESTIONS_MAIN_PAGE'] + '">Перейти</a>'
                    requests.post(app.config['TEL_SENDMESS_URL'],
                                        json={'chat_id': app.config['TEL_INFO_CHAT'], 'text': user_message,
                                              'parse_mode': 'HTML'})
                    # print(req.json())
                except Exception as e:
                    print(str(e))

            return {'status': 'ok', 'info': {'files': {'flag': fileflag}, 'messid': question_id, 'text': message,
                                             'attachments': attachments}}
        else:
            return {'status': 'error', 'error_mess': 'WARN: No params'}

    except Exception as e:
        # db.session.rollback()
        print(str(e))
        return {'status': 'ok', 'error_mess': str(e)}