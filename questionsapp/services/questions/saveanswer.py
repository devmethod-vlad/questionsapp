import os, requests, json
from questionsapp.models import OrderMess, OrderStatus, OrderSpace, UserBaseRole, AnswerAttachment, AnonymOrderInfo
from questionsapp.models import AppConfig, OrdersInWork, AnswerMess, UserTelegramInfo, Attachment, AnonymOrder
from questionsapp.models import TelegramTempMess
from flask import current_app as app
from database import db
from questionsapp.services.roles.getrole import get_role


def save_answer(params):
    # try:

        userid = params["userid"]

        orderid = params["orderid"]

        message = params["answer_text"]

        uploaded_files = params["answer_files"]

        if userid and orderid and message:
            is_answer_text_change = False

            new_flag = 0

            check_order = OrderMess.query.filter_by(id=int(orderid)).first()

            check_author_userrole = UserBaseRole.query.filter_by(userid=int(userid)).first()

            author_user_role = get_role(check_author_userrole.roleid)

            check_answer = AnswerMess.query.filter(AnswerMess.orderid == int(orderid)).first()

            check_inwork = OrdersInWork.query.filter(OrdersInWork.orderid == int(orderid)).first()

            order_status_rec = OrderStatus.query.filter(OrderStatus.orderid == int(orderid)).first()

            order_space_rec = OrderSpace.query.filter_by(orderid=int(orderid)).first()

            if check_answer is None:
                new_flag = 1

                if check_inwork is None:
                    new_answer = AnswerMess(orderid=int(orderid), userid=int(userid), text=message)
                    answer_userid = int(userid)
                else:
                    if author_user_role == 'admin':
                        new_answer = AnswerMess(orderid=int(orderid), userid=int(check_inwork.userid), text=message)
                        answer_userid = check_inwork.userid
                    else:
                        new_answer = AnswerMess(orderid=int(orderid), userid=int(userid), text=message)
                        answer_userid = int(userid)

                db.session.add(new_answer)

                new_status_id = app.config['QUESTION_STATUS']['received_answer']['id']

                if params["fastformflag"]:
                    if int(params["fastformflag"]) == 1:
                        new_status_id = app.config['QUESTION_STATUS']['archive']['id']

                order_status_rec.statusid = new_status_id
                db.session.commit()
                answer_id = new_answer.id
                answer_created_at = new_answer.created_at

                if check_inwork is not None:
                    db.session.delete(check_inwork)
                    db.session.commit()
            else:
                answer_id = check_answer.id
                answer_userid = check_answer.userid
                answer_created_at = check_answer.created_at
                if check_answer.text != message:
                    is_answer_text_change = True
                    check_answer.text = message
                    db.session.commit()

            answer_user_telinfo = UserTelegramInfo.query.filter_by(userid=int(userid)).first()

            if answer_user_telinfo is not None:
                answer_user_telid = answer_user_telinfo.tlgmid
            else:
                answer_user_telid = ''

            if len(uploaded_files) == 0:
                fileflag = 'notexist'
            else:
                app_conf_rec = AppConfig.query.first()

                fileflag = 'exist'

                if not os.path.isdir(app.config['ANSWER_ATTACHMENTS']):
                    os.mkdir(app.config['ANSWER_ATTACHMENTS'])

                user_path = os.path.join(app.config['ANSWER_ATTACHMENTS'], str(answer_userid))

                if not os.path.isdir(user_path):
                    os.mkdir(user_path)

                user_answer_path = os.path.join(user_path, str(orderid))

                if not os.path.isdir(user_answer_path):
                    os.mkdir(user_answer_path)

                dirfiles = os.listdir(user_answer_path)

                for file_item in uploaded_files:
                    filename = file_item.filename
                    filename = filename.strip().replace(" ", "_")
                    file_size = round(file_item.content_length / 10000000, 3)
                    file_ext = filename.split('.')[-1].lower()
                    if file_size < int(app_conf_rec.uploadsize):
                        if filename in dirfiles:
                            filename = 'copy-' + filename
                        file_item.save(os.path.join(user_answer_path, filename))
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
                        new_answer_attach = AnswerAttachment(attachid=new_attach.id, answerid=answer_id)
                        db.session.add(new_answer_attach)
                        db.session.commit()

            attachments = []

            for at_item in AnswerAttachment.query.filter(AnswerAttachment.answerid == answer_id).all():
                attach_rec = Attachment.query.filter(Attachment.id == at_item.attachid).first()
                attachments.append(
                    {'type': attach_rec.type, 'path': attach_rec.path, 'created_at': at_item.created_at,
                     'attachid': attach_rec.id})

            send_tel_notify = 'not_sent'

            send_resp = {}

            send_telid = ''

            check_anonym_quest = AnonymOrder.query.filter_by(orderid=int(orderid)).first()

            if check_anonym_quest is not None:

                anon_quest_info = AnonymOrderInfo.query.filter_by(orderid=int(orderid)).first()

                if new_flag == 1:
                    message = '✅ <b>На ваш вопрос </b><em>...' + check_order.text[0:20] + '...</em><b> был получен ответ! Вы можете посмотреть содержание в телеграмме или открыв в веб-версии. Веб-версия может не работать на устройствах со старой версией приложения. В этом случае воспользуйтесь просмотром в телеграмме</b>'
                else:
                    message = '⚡ <b>Исполнитель обновил ответ на вопрос </b><em>...' + check_order.text[0:20] + '...</em><b>! Вы можете посмотреть содержание в телеграмме или открыв в веб-версии. Веб-версия может не работать на устройствах со старой версией приложения. В этом случае воспользуйтесь просмотром в телеграмме</b>'

                if anon_quest_info is not None:
                    if app.config['TEL_SEND_ANSWERMESS'] and (new_flag == 1 or is_answer_text_change or len(uploaded_files) != 0):
                        try:
                            markup = json.dumps({'inline_keyboard': [
                                [{"text": "👁 В телеграмме", "callback_data": "OrderShower-" + str(orderid)}],
                                [{"text": "👁 В веб-версии", "web_app": {
                                    "url": app.config['WEB_APP_ORDERSHOWER'] + "?webappquestionid=" + str(orderid)}}],
                            ]})
                            req = requests.post(app.config['TEL_SENDMESS_URL'],
                                          json={'chat_id': anon_quest_info.tlgmid, 'text': message,
                                                'reply_markup': markup, 'parse_mode': 'HTML'})
                            send_tel_notify = 'sent'

                            send_resp = req.json()

                            send_telid = str(anon_quest_info.tlgmid)
                        except Exception as e:
                            print(str(e))
            else:
                check_tel_info = UserTelegramInfo.query.filter_by(userid=check_order.userid).first()

                check_status = OrderStatus.query.filter_by(orderid=check_order.id).first()

                if check_tel_info is not None:
                    if app.config['TEL_SEND_ANSWERMESS']:
                        send_mess_flag = True

                        if check_order.userid == answer_userid:
                            if not app.config['NOTIFY_SELF_ORDER']:
                                send_mess_flag = False

                        if new_flag !=1 and not is_answer_text_change and len(uploaded_files) == 0:
                            send_mess_flag = False

                        if send_mess_flag:
                            try:

                                if new_flag == 1:
                                    message = '✅ <b>На ваш вопрос №' + str(orderid) + ' был получен ответ!</b>'
                                else:
                                    message = '⚡ <b>Исполнитель обновил ответ на вопрос №' + str(orderid) + '</b>!'

                                markup = json.dumps({'inline_keyboard': [
                                    [{"text": "Открыть вопрос",
                                      "callback_data": "ShowDetails-1-" + str(check_status.statusid) + "-" + str(
                                          orderid) + "-💡-myAnsweredOrders-" + str(order_space_rec.spaceid) + "-1"}],
                                ]})
                                req = requests.post(app.config['TEL_SENDMESS_URL'],
                                              json={'chat_id': check_tel_info.tlgmid, 'text': message,
                                                    'reply_markup': markup, 'parse_mode': 'HTML'})
                                send_tel_notify = 'sent'

                                send_resp = req.json()

                                send_telid = str(check_tel_info.tlgmid)
                            except Exception as e:
                                pass

            # print(send_resp)
            if 'ok' in send_resp:
                if send_resp['ok']:
                    messid = send_resp['result']['message_id']

                    new_mess = TelegramTempMess(telid=send_telid, messid=str(messid))
                    db.session.add(new_mess)
                    db.session.commit()

            return {'status': 'ok',
                    'info': {'files': {'flag': fileflag}, 'is_answer_new': new_flag, 'orderid': orderid,
                             'text': message, 'answerid': answer_id,
                             'answeruserid': answer_userid, 'created_at': answer_created_at, 'attachments': attachments,
                             'answerusertelid': answer_user_telid, 'send_notification': send_tel_notify}}
        else:
            return {'status': 'error', 'error_mess': 'WARN: No params'}


    # except Exception as e:
    #     db.session.rollback()
    #     print(str(e))
    #     return {'status': 'error', 'error_mess': str(e)}