from database import db
import os
from questionsapp.models import Attachment, OrderAttachment, SyncAttachments
from questionsapp.models import TelegramAttachment, OrderTelegramAttachment
from questionsapp.models import AnswerAttachment, AnswerTelegramAttachment
from flask import current_app as app

def delete_attachment(attach_target, attachid, orderid, userid):

    if attachid and attach_target and orderid and userid:
        try:
            if attach_target == 'question':
                atachRec = Attachment.query.filter_by(id=int(attachid)).first()
                if atachRec:
                    attachPath = atachRec.path
                    db.session.delete(atachRec)
                    ordersUserPart = os.path.join(app.config['QUESTION_ATTACHMENTS'], str(userid))
                    ordersUserOrderPart = os.path.join(ordersUserPart, str(orderid))
                    filePath = os.path.join(ordersUserOrderPart, str(attachPath))
                    try:
                        os.remove(filePath)
                    except:
                        pass
                orderAttRec = OrderAttachment.query.filter_by(attachid=int(attachid)).first()
                if orderAttRec:
                    db.session.delete(orderAttRec)
                syncRec = SyncAttachments.query.filter_by(webattachid=int(attachid)).first()
                if syncRec is not None:
                    telAttach = TelegramAttachment.query.filter_by(attachid=syncRec.telattachid).first()
                    if telAttach:
                        db.session.delete(telAttach)
                    telOrdAttach = OrderTelegramAttachment.query.filter_by(attachid=telAttach.id).first()
                    if telOrdAttach:
                        db.session.delete(telOrdAttach)
                    db.session.delete(syncRec)
                db.session.commit()
                return {'status': 'ok'}
            elif attach_target == 'answer':
                atachRec = Attachment.query.filter_by(id=int(attachid)).first()
                if atachRec:
                    attachPath = atachRec.path
                    db.session.delete(atachRec)
                    db.session.commit()
                    answersUserPart = os.path.join(app.config['ANSWER_ATTACHMENTS'], str(userid))
                    answersUserOrderPart = os.path.join(answersUserPart, str(orderid))
                    filePath = os.path.join(answersUserOrderPart, str(attachPath))
                    try:
                        os.remove(filePath)
                    except:
                        pass
                answerAttRec = AnswerAttachment.query.filter_by(attachid=int(attachid)).first()
                if answerAttRec:
                    db.session.delete(answerAttRec)
                    db.session.commit()
                syncRec = SyncAttachments.query.filter_by(webattachid=int(attachid)).first()
                if syncRec is not None:
                    telAttach = TelegramAttachment.query.filter_by(attachid=syncRec.telattachid).first()
                    if telAttach:
                        db.session.delete(telAttach)
                        db.session.commit()
                    telOrdAttach = AnswerTelegramAttachment.query.filter_by(attachid=telAttach.id).first()
                    if telOrdAttach:
                        db.session.delete(telOrdAttach)
                        db.session.commit()
                    db.session.delete(syncRec)
                db.session.commit()
                return {'status': 'ok'}
        except Exception as e:
            db.session.rollback()
            print(str(e))
            return {'status': 'error', 'error_mess': str(e)}
    else:
        return {'status': 'error', 'error_mess': 'WARN: No params'}