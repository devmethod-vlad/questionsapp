from database import db
from questionsapp.models import AppConfig, User, Spaces, OrderMess
from questionsapp.models import OrderStatus, OrderSpace, AnonymOrder, AnonymOrderInfo
from questionsapp.models import OrderUnionRole
import datetime, requests
from flask import current_app as app
from pytz import timezone

east = timezone('Europe/Moscow')

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

def save_anonym_question(params):

    if check_anonym_quest_params(params):
        userfingerprintid = params['userfingerprintid']
        muname = params['muname']
        fio = params['fio']
        question_text = params['question_text']
        mail = params['mail']
        phone = params['phone']
        spacekey = params['spacekey']
        unionroleid = params['unionroleid']

        app_conf_rec = AppConfig.query.first()

        if app_conf_rec is not None:

            check_anonym_user = User.query.filter_by(id=int(app_conf_rec.anonymuserid)).first()

            if check_anonym_user:

                space_id = app.config['NULLSPACE']['id']
                space_title = app.config['NULLSPACE']['title']

                if spacekey:
                    if spacekey != '':
                        check_space = Spaces.query.filter_by(spacekey=spacekey).first()

                        if check_space:
                            space_id = check_space.id
                            space_title = check_space.title

                new_question = OrderMess(userid=check_anonym_user.id, text=question_text)
                db.session.add(new_question)
                db.session.commit()
                new_status = OrderStatus(orderid=new_question.id, statusid=app.config['QUESTION_STATUS']['create']['id'])
                db.session.add(new_status)
                db.session.commit()
                new_space = OrderSpace(orderid=new_question.id, spaceid=space_id)
                db.session.add(new_space)
                db.session.commit()
                new_anonym_quest = AnonymOrder(orderid=new_question.id, fingerprint=userfingerprintid)
                db.session.add(new_anonym_quest)
                db.session.commit()
                anonym_quest_info = AnonymOrderInfo(orderid=new_question.id, anonymorderid=new_anonym_quest.id,
                                                  fio=fio, mail=mail, phone=phone, telusername='', tlgmid='',
                                                  muname=muname, speciality='')
                db.session.add(anonym_quest_info)
                db.session.commit()

                if unionroleid:
                    if int(unionroleid) != 0:
                        new_quest_unionrole = OrderUnionRole(orderid=new_question.id,unionroleid=int(unionroleid))
                        db.session.add(new_quest_unionrole)
                        db.session.commit()
                else:

                    new_quest_unionrole = OrderUnionRole(orderid=new_question.id, unionroleid=int(app.config['NULLROLE']['id']))
                    db.session.add(new_quest_unionrole)
                    db.session.commit()

                now_time = datetime.datetime.now(east)

                if app.config['TEL_SEND_NEWMESS']:
                    tel_message = '💡 <b>Новый вопрос </b><em>' + str(new_question.id) + '</em><b> :</b>\n\n🗂 <b>По разделу: </b><em>' + space_title + '</em>\n<b>Время: </b><em>' + now_time.strftime(
                        "%d-%m-%Y, %H:%M") + '</em> \n\n<b><a href = "' + app.config['QUESTIONS_MAIN_PAGE'] + '">Перейти</a></b>'
                    try:
                        requests.post(app.config['TEL_SENDMESS_URL'], json={'chat_id': app.config['TEL_INFO_CHAT'], 'text': tel_message,
                                                      'parse_mode': 'HTML'})

                    except Exception as e:
                        print(str(e))
                return {'status': 'ok',
                        'info': {'files': {'flag': 'notexist'}, 'messid': new_question.id, 'text': params['question_text'],
                                 'attachments': []}}

            else:
                return {'status': 'error', 'error_mess': 'ERROR: AnonymUser is None'}

        else:
            return {'status': 'error', 'error_mess': 'ERROR: appConfRec is None'}


    else:
        return {'status': 'params_error', 'error_mess': 'WARN: No params'}