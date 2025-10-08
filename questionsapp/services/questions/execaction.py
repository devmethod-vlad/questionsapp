import shutil
import requests
from database import db
import os
import json
from sqlalchemy import desc
from flask import current_app as app
from questionsapp.models import AnswerMess, OrderMess, OrderStatus, OrdersInWork, TelegramTempMess
from questionsapp.models import OrderSpace, AnonymOrder, AnonymOrderInfo, UserBaseRole
from questionsapp.models import AnswerTelegramAttachment, Attachment, AnswerAttachment
from questionsapp.models import TelegramAttachment, SyncAttachments, OrderAttachment
from questionsapp.models import OrderTelegramAttachment, UserTelegramInfo, OrderPublic, AppConfig
from tasks.publicorder import publicOrder

def exec_action(action, orderid, userid):
    # try:
        TOKEN = app.config['TEL_TOKEN']
        print("exec_action TOKEN: ", os.getenv('PG_CONTAINER'))
        SEND_URL = f'https://api.telegram.org/bot{TOKEN}/sendMessage'

        answerCheckRec = AnswerMess.query.filter_by(orderid=int(orderid)).first()
        orderCheckRec = OrderMess.query.filter_by(id=int(orderid)).first()
        orderStatusRec = OrderStatus.query.filter_by(orderid=int(orderid)).first()
        orderInWorkRec = OrdersInWork.query.filter_by(orderid=int(orderid)).first()
        orderSpaceRec = OrderSpace.query.filter_by(orderid=int(orderid)).first()
        checkAnonymOrder = AnonymOrder.query.filter_by(orderid=int(orderid)).first()
        anonymOrderInfo = AnonymOrderInfo.query.filter_by(orderid=int(orderid)).first()
        checkRoleRec = UserBaseRole.query.filter(UserBaseRole.userid == int(userid)).first()

        if action == 'to_trash':
            orderStatusRec.statusid = 5
            db.session.commit()
            return {'status': 'ok'}
        elif action == 'back_in_work':
            orderStatusRec.statusid = 7
            db.session.commit()
            return {'status': 'ok'}
        elif action == 'delete':
            if answerCheckRec is not None:
                answerAttachsIds = []
                answerTelAttachsIds = []
                answerTelAttachs = AnswerTelegramAttachment.query.filter(
                    AnswerTelegramAttachment.answerid == answerCheckRec.id).all()
                answerAttachsRecs = AnswerAttachment.query.filter(
                    AnswerAttachment.answerid == answerCheckRec.id).all()
                if answerAttachsRecs is not None:
                    for answAttachsItem in answerAttachsRecs:
                        answerAttachsIds.append(answAttachsItem.attachid)
                if answerTelAttachs is not None:
                    for answTelAtItem in answerTelAttachs:
                        answerTelAttachsIds.append(answTelAtItem.attachid)
                if not len(answerAttachsIds) == 0:
                    Attachment.query.filter(Attachment.id.in_(answerAttachsIds)).delete(synchronize_session='fetch')
                    AnswerAttachment.query.filter(AnswerAttachment.answerid == answerCheckRec.id).delete(
                        synchronize_session='fetch')
                    SyncAttachments.query.filter(SyncAttachments.webattachid.in_(answerAttachsIds)).delete(
                        synchronize_session='fetch')
                if not len(answerTelAttachsIds) == 0:
                    TelegramAttachment.query.filter(TelegramAttachment.id.in_(answerTelAttachsIds)).delete(
                        synchronize_session='fetch')
                    AnswerTelegramAttachment.query.filter(
                        AnswerTelegramAttachment.answerid == answerCheckRec.id).delete(synchronize_session='fetch')
                    SyncAttachments.query.filter(SyncAttachments.telattachid.in_(answerTelAttachsIds)).delete(
                        synchronize_session='fetch')
                db.session.commit()
                answersUserPart = os.path.join(app.config['ANSWER_ATTACHMENTS'], str(answerCheckRec.userid))
                answersUserOrderPart = os.path.join(answersUserPart, str(orderid))

                try:
                    shutil.rmtree(answersUserOrderPart)
                except:
                    pass

            orderAttachsRecs = OrderAttachment.query.filter(OrderAttachment.orderid == orderid).all()
            if orderAttachsRecs is not None:
                orderAttachsIds = []
                for attItem in orderAttachsRecs:
                    orderAttachsIds.append(attItem.attachid)
                if not len(orderAttachsIds) == 0:
                    Attachment.query.filter(Attachment.id.in_(orderAttachsIds)).delete(synchronize_session='fetch')
                    OrderAttachment.query.filter(OrderAttachment.orderid == orderid).delete(synchronize_session='fetch')
                    SyncAttachments.query.filter(SyncAttachments.webattachid.in_(orderAttachsIds)).delete(
                        synchronize_session='fetch')
            orderTelAttachsRecs = OrderTelegramAttachment.query.filter(OrderTelegramAttachment.orderid == orderid).all()
            if orderTelAttachsRecs is not None:
                orderTelAttachsIds = []
                for attItem in orderTelAttachsRecs:
                    orderTelAttachsIds.append(attItem.attachid)
                if not len(orderTelAttachsIds) == 0:
                    TelegramAttachment.query.filter(TelegramAttachment.id.in_(orderTelAttachsIds)).delete(
                        synchronize_session='fetch')
                    OrderTelegramAttachment.query.filter(OrderAttachment.orderid == orderid).delete(
                        synchronize_session='fetch')
                    SyncAttachments.query.filter(SyncAttachments.telattachid.in_(orderTelAttachsIds)).delete(
                        synchronize_session='fetch')
            db.session.commit()
            ordersUserPart = os.path.join(app.config['QUESTION_ATTACHMENTS'], str(orderCheckRec.userid))
            orderPathTodelete = os.path.join(ordersUserPart, str(orderid))
            try:
                shutil.rmtree(orderPathTodelete)
            except:
                pass
            OrderMess.query.filter(OrderMess.id == int(orderid)).delete(synchronize_session='fetch')
            AnswerMess.query.filter(AnswerMess.orderid == int(orderid)).delete(synchronize_session='fetch')
            OrderStatus.query.filter(OrderStatus.orderid == int(orderid)).delete(synchronize_session='fetch')
            OrdersInWork.query.filter(OrdersInWork.orderid == int(orderid)).delete(synchronize_session='fetch')
            db.session.commit()
            return {'status': 'ok'}
        elif action == 'from_trash':
            if answerCheckRec is None and orderInWorkRec is None:
                orderStatusRec.statusid = 1
                db.session.commit()
            elif answerCheckRec is None and orderInWorkRec is not None:
                orderStatusRec.statusid = 2
                db.session.commit()
            elif answerCheckRec is not None:
                orderStatusRec.statusid = 4
                db.session.commit()
            return {'status': 'ok'}

        elif action == 'in_work':
            if not userid:
                return {'status': 'error', 'error_mess': 'WARN: No params'}
            else:
                new_order_inwork = OrdersInWork(userid=int(userid), orderid=int(orderid))
                db.session.add(new_order_inwork)
                orderStatusRec.statusid = 2
                db.session.add(orderStatusRec)
                db.session.commit()

                send_notification = 'not_sent'

                send_resp = {}

                save_telid = ''

                if checkAnonymOrder is not None:
                    if anonymOrderInfo is None:
                        return {'status': 'ok', 'info': {'send_notofication': send_notification}}
                    else:
                        if anonymOrderInfo.tlgmid != '':
                            try:
                                message = '✅ <b>Ваш вопрос ...</b><em>' + orderCheckRec.text[
                                                                          0:20] + '</em><b>... был взят в работу!</b>'
                                req = requests.post(SEND_URL, json={'chat_id': anonymOrderInfo.tlgmid, 'text': message,
                                                              'parse_mode': 'HTML'})
                                send_resp = req.json()
                                send_notification = 'sent'
                                save_telid = str(anonymOrderInfo.tlgmid)
                            except Exception as e:
                                print(str(e))
                else:

                    check_telegram_info = UserTelegramInfo.query.filter_by(userid=orderCheckRec.userid).first()

                    if check_telegram_info is not None:
                        if app.config['TEL_SEND_MESSINWORK']:
                            sendMessFlag = True
                            if checkRoleRec.roleid == 1 or checkRoleRec.roleid == 3:
                                if int(userid) == orderCheckRec.userid:
                                    if not app.config['NOTIFY_SELF_ORDER']:
                                        sendMessFlag = False

                            if sendMessFlag:
                                try:

                                    message = '✅ <b>Ваш вопрос №' + str(orderid) + ' был взят в работу!</b>'
                                    markup = json.dumps({'inline_keyboard': [
                                        [{"text": "Открыть вопрос", "callback_data": "ShowDetails-0-2-" + str(
                                            orderid) + "-🛠-myOrdersInWork-" + str(orderSpaceRec.spaceid) + "-1"}]
                                    ]})

                                    req = requests.post(SEND_URL,
                                                        json={'chat_id': check_telegram_info.tlgmid, 'text': message,
                                                              'reply_markup': markup, 'parse_mode': 'HTML'})

                                    send_resp = req.json()

                                    save_telid = str(check_telegram_info.tlgmid)

                                    send_notification = 'sent'

                                except Exception as e:
                                    print(str(e))

                if 'ok' in send_resp:
                    if send_resp['ok']:
                        messid = send_resp['result']['message_id']

                        new_mess = TelegramTempMess(telid=save_telid, messid=str(messid))
                        db.session.add(new_mess)
                        db.session.commit()

                return {'status': 'ok', 'info': {'send_notofication': send_notification}}

        elif action == 'from_work' or action == 'from_work_admin':
            # print("GetOrderOutFromWork")
            user_inwork_todelete = 0
            if orderInWorkRec is not None:
                user_inwork_todelete = orderInWorkRec.userid
                db.session.delete(orderInWorkRec)
            orderStatusRec.statusid = 1
            db.session.add(orderStatusRec)
            db.session.commit()
            send_notification = 'not_sent'

            send_resp = {}

            save_telid = ''

            if checkAnonymOrder is not None:
                if anonymOrderInfo is None:
                    return {'status': 'ok', 'info': {'send_notofication': send_notification}}
                else:
                    if len(anonymOrderInfo.tlgmid) > 2:
                        try:
                            message = '✅ <b>Исполнитель вернул ваш вопрос...</b><em>' + orderCheckRec.text[
                                                                                        0:20] + '</em><b>... без ответа! Подождите, кто-нибудь еще возмет его в работу!</b>'
                            req = requests.post(SEND_URL, json={'chat_id': anonymOrderInfo.tlgmid, 'text': message,
                                                          'parse_mode': 'HTML'})
                            send_notification = 'sent'

                            send_resp = req.json()
                            save_telid = str(anonymOrderInfo.tlgmid)

                        except Exception as e:
                            print(str(e))

            else:
                check_tel_info = UserTelegramInfo.query.filter_by(userid=orderCheckRec.userid).first()

                if check_tel_info is not None:

                    if app.config['TEL_SEND_MESSINWORK']:
                        sendMessFlag = True
                        if checkRoleRec.roleid == 1 or checkRoleRec.roleid == 3:
                            if user_inwork_todelete != 0:
                                if int(orderCheckRec.userid) == user_inwork_todelete:
                                    if not app.config['NOTIFY_SELF_ORDER']:
                                        sendMessFlag = False
                        if sendMessFlag:
                            try:
                                message = '🔔 <b>Исполнитель вернул вопрос <u>№ ' + str(
                                    orderid) + '</u> без ответа. Подождите, кто-нибудь еще возмет его в работу!</b>'
                                req = requests.post(SEND_URL, json={'chat_id': check_tel_info.tlgmid, 'text': message,
                                                              'parse_mode': 'HTML'})
                                send_notification = 'sent'

                                send_resp = req.json()

                                save_telid = str(check_tel_info.tlgmid)
                            except Exception as e:
                                print(str(e))

            if 'ok' in send_resp:
                if send_resp['ok']:
                    messid = send_resp['result']['message_id']

                    new_mess = TelegramTempMess(telid=save_telid, messid=str(messid))
                    db.session.add(new_mess)
                    db.session.commit()

            return {'status': 'ok', 'info': {'send_notofication': send_notification}}

        elif action == 'to_archive':
            orderStatusRec.statusid = 4
            db.session.commit()
            sendTelegramNotification = 'not_sent'
            if answerCheckRec:
                checkTelegramInfo = UserTelegramInfo.query.filter_by(userid=answerCheckRec.userid).first()
                if checkTelegramInfo:
                    if app.config['TEL_SEND_MESSUSERCLOSED']:
                        sendMessFlag = True
                        if checkRoleRec.roleid == 1 or checkRoleRec.roleid == 3:
                            if int(userid) == answerCheckRec.userid:
                                if not app.config['NOTIFY_SELF_ORDER']:
                                    sendMessFlag = False
                        if sendMessFlag:
                            try:
                                message = '🔔 <b>Вопрос <u>№ ' + str(orderid) + '</u> был закрыт пользователем!</b>'
                                requests.post(SEND_URL, json={'chat_id': checkTelegramInfo.tlgmid, 'text': message,
                                                              'parse_mode': 'HTML'})
                                # bot = telebot.TeleBot(app.config['TEL_TOKEN'], parse_mode='HTML')
                                # bot.send_message(checkTelegramInfo.tlgmid, message)
                                sendTelegramNotification = 'sent'
                            except:
                                pass

            return {'status': 'ok', 'info': {'send_notofication': sendTelegramNotification}}

        elif action == 'RestoreFromArchive':
            orderStatusRec.statusid = 3
            db.session.commit()
            return {'status': 'ok'}

        elif action == 'public':
            appConfRec = AppConfig.query.order_by(desc('created_at')).limit(1).first()

            if appConfRec.ispublicactive == 1:
                return {'status': 'publicactive'}
            else:
                checkPublicOrder = OrderPublic.query.filter_by(orderid=int(orderid)).first()
                if checkPublicOrder:
                    db.session.delete(checkPublicOrder)
                    db.session.commit()
                newPublicOrderRec = OrderPublic(orderid=int(orderid))
                db.session.add(newPublicOrderRec)
                db.session.commit()

                if int(os.getenv('PROD')) == 1:
                    publicOrder.delay(orderid)
                else:
                    print("PUBLIC QUESTION!!!")

                return {'status': 'ok'}

        elif action == 'from_public':
            appConfRec = AppConfig.query.order_by(desc('created_at')).limit(1).first()

            if appConfRec.ispublicactive == 1:
                return {'status': 'publicactive'}
            else:
                checkPublicOrder = OrderPublic.query.filter_by(orderid=int(orderid)).first()
                if checkPublicOrder:
                    db.session.delete(checkPublicOrder)
                    db.session.commit()

                    if int(os.getenv('PROD')) == 1:
                        publicOrder.delay(orderid)
                    else:
                        print("PUBLIC QUESTION!!!")
                    print("PUBLIC!!!!")

                return {'status': 'ok'}

    # except Exception as e:
    #     print(str(e))
    #     print("ERROR")
    #     db.session.rollback()
    #     return {'status': 'error', 'error_mess': str(e)}