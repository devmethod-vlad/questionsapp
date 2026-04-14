from app.db.legacy_db import db
from app.db.models import AppConfig, User, Spaces, OrderMess
from app.db.models import OrderStatus, OrderSpace, AnonymOrder, AnonymOrderInfo
from app.db.models import OrderUnionRole
from app.services.common.telegram import tg_post
import datetime
from app.core.constants import EXT_DICT, NULLROLE, NULLSPACE, QUESTION_STATUS
from app.core.settings import get_settings
from pytz import timezone

settings = get_settings()

east = timezone('Europe/Moscow')
DUPLICATE_LOOKBACK_SECONDS = 2


def check_string_param(param):
    flag = True
    if isinstance(param, str):
        if param == '':
            flag = False
    else:
        flag = False
    return flag


def check_anonym_quest_params(params):
    check = True

    if not check_string_param(params['userfingerprintid']):
        check = False

    if not check_string_param(params['muname']):
        check = False

    if not check_string_param(params['fio']):
        check = False

    if not check_string_param(params['question_text']):
        check = False

    check_mail = True
    check_phone = True

    if not check_string_param(params['mail']):
        check_mail = False

    if not check_string_param(params['phone']):
        check_phone = False

    if not check_mail and not check_phone:
        check = False

    return check


def _normalize_optional_int(value):
    if value in (None, '', 'None', 'null'):
        return None
    return int(value)


def _resolve_space(spacekey):
    space_id = NULLSPACE['id']
    space_title = NULLSPACE['title']

    if spacekey:
        if spacekey != '':
            check_space = db.session.query(Spaces).filter_by(spacekey=spacekey).first()

            if check_space:
                space_id = check_space.id
                space_title = check_space.title

    return space_id, space_title


def _find_recent_duplicate_anonym_question(anonym_user_id, question_text, userfingerprintid, space_id):
    threshold = datetime.datetime.now() - datetime.timedelta(seconds=DUPLICATE_LOOKBACK_SECONDS)
    candidates = (
        db.session.query(OrderMess)
        .filter(
            OrderMess.userid == int(anonym_user_id),
            OrderMess.text == question_text,
            OrderMess.created_at >= threshold,
        )
        .order_by(OrderMess.id.desc())
        .all()
    )

    for candidate in candidates:
        check_anonym_order = db.session.query(AnonymOrder).filter_by(orderid=int(candidate.id), fingerprint=userfingerprintid).first()
        if check_anonym_order is None:
            continue

        check_space = db.session.query(OrderSpace).filter_by(orderid=int(candidate.id)).first()
        if check_space is None or int(check_space.spaceid) != int(space_id):
            continue

        return candidate

    return None


def _build_response(question_id, question_text):
    return {
        'status': 'ok',
        'info': {
            'files': {'flag': 'notexist'},
            'messid': question_id,
            'text': question_text,
            'attachments': []
        }
    }


def _send_new_anonym_question_notification(new_question_id, space_title):
    now_time = datetime.datetime.now(east)

    if True:
        tel_message = '💡 <b>Новый вопрос </b><em>' + str(new_question_id) + '</em><b> :</b>\n\n🗂 <b>По разделу: </b><em>' + space_title + '</em>\n<b>Время: </b><em>' + now_time.strftime(
            "%d-%m-%Y, %H:%M") + '</em> \n\n<b><a href = "' + settings.questions_main_page + '">Перейти</a></b>'
        try:
            tg_post(
                settings.tel_send_message_url,
                json_body={
                    'chat_id': settings.tel_info_chat,
                    'text': tel_message,
                    'parse_mode': 'HTML'
                },
                timeout=(10.0, 40.0),
                socks_proxy=settings.tel_socks_proxy,
            )

        except Exception as e:
            print(str(e))


def save_anonym_question(params):

    if check_anonym_quest_params(params):
        userfingerprintid = params['userfingerprintid']
        muname = params['muname']
        fio = params['fio']
        question_text = params['question_text']
        mail = params['mail']
        phone = params['phone']
        spacekey = params['spacekey']
        unionroleid = _normalize_optional_int(params['unionroleid'])

        app_conf_rec = db.session.query(AppConfig).first()

        if app_conf_rec is not None:

            check_anonym_user = db.session.query(User).filter_by(id=int(app_conf_rec.anonymuserid)).first()

            if check_anonym_user:
                send_new_question_notify = False
                created_question_id = None
                space_title = NULLSPACE['title']

                try:
                    # The session already autobegins on earlier SELECTs, so avoid nested begin().
                    db.session.query(User).filter_by(id=int(check_anonym_user.id)).with_for_update().first()

                    space_id, space_title = _resolve_space(spacekey)
                    duplicate_question = _find_recent_duplicate_anonym_question(
                        anonym_user_id=check_anonym_user.id,
                        question_text=question_text,
                        userfingerprintid=userfingerprintid,
                        space_id=space_id,
                    )

                    if duplicate_question is not None:
                        created_question_id = duplicate_question.id
                    else:
                        new_question = OrderMess(userid=check_anonym_user.id, text=question_text)
                        db.session.add(new_question)
                        db.session.flush()

                        created_question_id = new_question.id
                        send_new_question_notify = True

                        new_status = OrderStatus(
                            orderid=new_question.id,
                            statusid=QUESTION_STATUS['create']['id']
                        )
                        db.session.add(new_status)

                        new_space = OrderSpace(orderid=new_question.id, spaceid=space_id)
                        db.session.add(new_space)

                        new_anonym_quest = AnonymOrder(orderid=new_question.id, fingerprint=userfingerprintid)
                        db.session.add(new_anonym_quest)
                        db.session.flush()

                        anonym_quest_info = AnonymOrderInfo(
                            orderid=new_question.id,
                            anonymorderid=new_anonym_quest.id,
                            fio=fio,
                            mail=mail,
                            phone=phone,
                            telusername='',
                            tlgmid='',
                            muname=muname,
                            speciality=''
                        )
                        db.session.add(anonym_quest_info)

                        if unionroleid is not None and int(unionroleid) != 0:
                            new_quest_unionrole = OrderUnionRole(orderid=new_question.id, unionroleid=int(unionroleid))
                            db.session.add(new_quest_unionrole)
                        else:
                            new_quest_unionrole = OrderUnionRole(orderid=new_question.id, unionroleid=int(NULLROLE['id']))
                            db.session.add(new_quest_unionrole)

                    db.session.commit()

                    if send_new_question_notify:
                        _send_new_anonym_question_notification(created_question_id, space_title)

                    return _build_response(created_question_id, question_text)

                except Exception as e:
                    db.session.rollback()
                    print(str(e))
                    return {'status': 'error', 'error_mess': str(e)}

            else:
                return {'status': 'error', 'error_mess': 'ERROR: AnonymUser is None'}

        else:
            return {'status': 'error', 'error_mess': 'ERROR: appConfRec is None'}


    else:
        return {'status': 'params_error', 'error_mess': 'WARN: No params'}
