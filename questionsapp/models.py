from sqlalchemy import ForeignKey

from database import db
import datetime


class User(db.Model):

    __tablename__ = 'userpg'
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    firstname = db.Column(db.String(1000))
    lastname = db.Column(db.String(1000))
    secondname = db.Column(db.String(1000))
    phone = db.Column(db.String(255))
    mail = db.Column(db.String(255))
    created_at = db.Column(db.TIMESTAMP, nullable=False,default=datetime.datetime.now)

    def __init__(self, firstname, lastname, secondname, phone, mail):
        self.firstname = firstname
        self.lastname = lastname
        self.secondname = secondname
        self.phone = phone
        self.mail = mail

class UserEmiasInfo(db.Model):
    __tablename__ = 'user_emiasinfo'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userid = db.Column(db.Integer, nullable=False, default=0)
    emiaslogin = db.Column(db.String(255))

    def __init__(self, userid, emiaslogin):
        self.userid = userid
        self.emiaslogin = emiaslogin


class UserWikiInfo(db.Model):
    __tablename__ = 'user_wikiinfo'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userid = db.Column(db.Integer, nullable=False, default=0)
    login = db.Column(db.String(255))

    def __init__(self, userid, login):
        self.userid = userid
        self.login = login

class AccessToken(db.Model):
    __tablename__ = 'access_token'
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    userid = db.Column(db.Integer, nullable=False, default=0)
    token = db.Column(db.String(1000), nullable=False, default='')
    created_at = db.Column(db.TIMESTAMP, nullable=False,default=datetime.datetime.now)

    def __init__(self, userid, token):
        self.userid = userid
        self.token = token


class AppConfig(db.Model):
    __tablename__ = 'appconfig'
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    token_expire = db.Column(db.Integer)
    botname = db.Column(db.String(255), nullable=False, default='')
    webappurl = db.Column(db.String(), nullable=False, default='')
    uploadsize = db.Column(db.Integer, nullable=False, default=1)
    maxfiles = db.Column(db.Integer, nullable=False, default=0)
    anonymuserid = db.Column(db.Integer, nullable=False, default=0)
    ispublicactive = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.TIMESTAMP, nullable=False,default=datetime.datetime.now)

    def __init__(self, token_expire, botname, webappurl, uploadsize, maxfiles, anonymuserid, ispublicactive):
        self.token_expire = token_expire
        self.botname = botname
        self.webappurl = webappurl
        self.uploadsize = uploadsize
        self.maxfiles = maxfiles
        self.anonymuserid = anonymuserid
        self.ispublicactive = ispublicactive

class UserTelegramInfo(db.Model):
    __tablename__ = 'user_telegraminfo'
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    userid = db.Column(db.Integer, nullable=False, default=0)
    tlgmname = db.Column(db.String(255), nullable=False, default='')
    tlgmid = db.Column(db.String(1000), nullable=False, default='')
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, userid, tlgmname, tlgmid):
        self.userid = userid
        self.tlgmname = tlgmname
        self.tlgmid = tlgmid

class OrderMess(db.Model):
    __tablename__ = 'ordermess'
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    userid = db.Column(db.Integer, nullable=False, default=0)
    text = db.Column(db.String(4000), nullable=False, default='')
    created_at = db.Column(db.TIMESTAMP, nullable=False,default=datetime.datetime.now)
    modified_at= db.Column(db.TIMESTAMP, nullable=False,default=datetime.datetime.now)

    def __init__(self, userid, text):
        self.userid = userid
        self.text = text

class OrderPublic(db.Model):
    __tablename__ = 'order_public'
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    orderid = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.TIMESTAMP, nullable=False,default=datetime.datetime.now)

    def __init__(self, orderid):
        self.orderid = orderid

class AnonymOrder(db.Model):

    __tablename__ = 'anonymorder'
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    fingerprint = db.Column(db.String(1000))
    orderid = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.datetime.now)
    modified_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, fingerprint, orderid):
        self.fingerprint = fingerprint
        self.orderid = orderid

class AnonymOrderInfo(db.Model):

    __tablename__ = 'anonymorderinfo'
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    orderid = db.Column(db.Integer, nullable=False, default=0)
    anonymorderid = db.Column(db.Integer, nullable=False, default=0)
    fio = db.Column(db.String(1000), nullable=False, default='')
    mail = db.Column(db.String(255), nullable=False, default='')
    phone = db.Column(db.String(255), nullable=False, default='')
    telusername = db.Column(db.String(1000), nullable=False, default='')
    tlgmid = db.Column(db.String(1000), nullable=False, default='')
    muname = db.Column(db.String(1000), nullable=False, default='')
    speciality = db.Column(db.String(2000), nullable=False, default='')
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.datetime.now)
    modified_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, orderid, anonymorderid, fio, mail, phone, telusername, tlgmid, muname, speciality):
        self.orderid = orderid
        self.anonymorderid = anonymorderid
        self.fio = fio
        self.mail = mail
        self.phone = phone
        self.telusername = telusername
        self.tlgmid = tlgmid
        self.muname = muname
        self.speciality = speciality

class AnswerMess(db.Model):
    __tablename__ = 'answermess'
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    userid = db.Column(db.Integer, nullable=False, default=0)
    orderid = db.Column(db.Integer, nullable=False, default=0)
    text = db.Column(db.String(4000), nullable=False, default='')
    created_at = db.Column(db.TIMESTAMP, nullable=False,default=datetime.datetime.now)
    modified_at= db.Column(db.TIMESTAMP, nullable=False,default=datetime.datetime.now)

    def __init__(self, userid, orderid, text):
        self.userid = userid
        self.orderid = orderid
        self.text = text


class OrderStatus(db.Model):

    __tablename__ = 'order_status'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    orderid = db.Column(db.Integer, nullable=False, default=0)
    statusid = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.TIMESTAMP, nullable=False,default=datetime.datetime.now)
    modified_at = db.Column(db.TIMESTAMP, nullable=False,default=datetime.datetime.now)

    def __init__(self, orderid, statusid):
        self.orderid = orderid
        self.statusid = statusid

class UserManualInfo(db.Model):

    __tablename__ = 'user_manualinfo'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userid = db.Column(db.Integer, nullable=False, default=0)
    login = db.Column(db.String(255), nullable=False, default='')
    password = db.Column(db.String(1000), nullable=False, default='')
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, userid, login, password):
        self.userid = userid
        self.login = login
        self.password = password

class BaseRole(db.Model):
    __tablename__ = 'baserole'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(1000), nullable=False, default='')

    def __init__(self, name):
        self.name = name

class UserBaseRole(db.Model):

    __tablename__ = 'user_baserole'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userid = db.Column(db.Integer, nullable=False, default=0)
    roleid = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.TIMESTAMP, nullable=False,default=datetime.datetime.now)
    modified_at = db.Column(db.TIMESTAMP, nullable=False,default=datetime.datetime.now)

    def __init__(self, userid, roleid):
        self.userid = userid
        self.roleid = roleid

class Attachment(db.Model):

    __tablename__ = 'attachment'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type = db.Column(db.String(255), nullable=False, default='')
    path = db.Column(db.String(1000), nullable=False, default='')
    caption = db.Column(db.String, nullable=False, default='')
    public = db.Column(db.Integer, nullable=False, default=1)

    def __init__(self, type, path, caption, public):
        self.type = type
        self.path = path
        self.caption = caption
        self.public = public

class OrderAttachment(db.Model):

    __tablename__ = 'order_attachment'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    attachid = db.Column(db.Integer, nullable=False, default=0)
    orderid = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.TIMESTAMP, nullable=False,default=datetime.datetime.now)

    def __init__(self, attachid, orderid):
        self.attachid = attachid
        self.orderid = orderid

class AnswerAttachment(db.Model):

    __tablename__ = 'answer_attachment'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    attachid = db.Column(db.Integer, nullable=False, default=0)
    answerid = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.TIMESTAMP, nullable=False,default=datetime.datetime.now)

    def __init__(self, attachid, answerid):
        self.attachid = attachid
        self.answerid = answerid

class TelegramAttachment(db.Model):

    __tablename__ = 'telegram_attachment'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type = db.Column(db.String(255), nullable=False, default='')
    uniqid = db.Column(db.String(1000), nullable=False, default='')
    caption = db.Column(db.String(), nullable=False, default='')
    path = db.Column(db.String(), nullable=False, default='')

    def __init__(self, type, uniqid, caption, path):
        self.type = type
        self.uniqid = uniqid
        self.caption = caption
        self.path = path

class AnswerTelegramAttachment(db.Model):

    __tablename__ = 'answer_tlgm_attachment'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    attachid = db.Column(db.Integer, nullable=False, default=0)
    answerid = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.TIMESTAMP, nullable=False,default=datetime.datetime.now)

    def __init__(self, attachid, answerid):
        self.attachid = attachid
        self.answerid = answerid


class OrderTelegramAttachment(db.Model):

    __tablename__ = 'order_tlgm_attachment'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    attachid = db.Column(db.Integer, nullable=False, default=0)
    orderid = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, attachid, orderid):
        self.attachid = attachid
        self.orderid = orderid


class SyncAttachments(db.Model):

    __tablename__ = 'sync_attachments'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    webattachid = db.Column(db.Integer, nullable=False, default=0)
    telattachid = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.TIMESTAMP, nullable=False,default=datetime.datetime.now)

    def __init__(self, webattachid, telattachid):
        self.webattachid = webattachid
        self.telattachid = telattachid

class OrdersInWork(db.Model):

    __tablename__ = 'orders_inwork'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userid = db.Column(db.Integer, nullable=False, default=0)
    orderid = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.TIMESTAMP, nullable=False,default=datetime.datetime.now)

    def __init__(self, userid, orderid):
        self.userid = userid
        self.orderid = orderid

class Spaces(db.Model):

    __tablename__ = 'infospace'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(1000), nullable=False, default='')
    spacekey = db.Column(db.String(255), nullable=False, default='')

    def __init__(self, title, spacekey):
        self.title = title
        self.spacekey = spacekey

class TelChatInfoSpace(db.Model):

    __tablename__ = 'telchat_infospace'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    spaceid = db.Column(db.Integer, nullable=False, default=0)
    chatid = db.Column(db.String(500), nullable=False, default='')

    def __init__(self, spaceid, chatid):
        self.spaceid = spaceid
        self.chatid = chatid

class OrderSpace(db.Model):

    __tablename__ = 'order_infospace'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    orderid = db.Column(db.Integer, nullable=False, default=0)
    spaceid = db.Column(db.Integer, nullable=False, default=0)

    def __init__(self, orderid, spaceid):
        self.orderid = orderid
        self.spaceid = spaceid

class TelPhrazeStats(db.Model):

    __tablename__ = 'telphrazestats'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userid = db.Column(db.Integer, nullable=False, default=0)
    searchphrase = db.Column(db.String(4000), nullable=False, default='')
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, userid, searchphrase):
        self.userid = userid
        self.searchphrase = searchphrase

class UnionRole(db.Model):

    __tablename__ = 'unionrole'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    emiasid = db.Column(db.Integer, nullable=False, default=0)
    name = db.Column(db.String(3000), nullable=False, default='')
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.datetime.now)
    modified_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, emiasid, name):
        self.emiasid = emiasid
        self.name = name

class SpaceUnionRole(db.Model):

    __tablename__ = 'infospace_unionrole'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    spaceid = db.Column(db.Integer, nullable=False, default=0)
    unionroleid = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.datetime.now)
    modified_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, spaceid, unionroleid):
        self.spaceid = spaceid
        self.unionroleid = unionroleid

class SpaceUnionRoleActive(db.Model):

    __tablename__ = 'spaceunionrole_isactive'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    spaceid = db.Column(db.Integer, nullable=False, default=0)
    active = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.datetime.now)
    modified_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, spaceid, active):
        self.spaceid = spaceid
        self.active = active

class UserUnionRole(db.Model):

    __tablename__ = 'user_unionrole'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userid = db.Column(db.Integer, nullable=False, default=0)
    unionroleid = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.datetime.now)
    modified_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, userid, unionroleid):
        self.userid = userid
        self.unionroleid = unionroleid

class OrderUnionRole(db.Model):

    __tablename__ = 'order_unionrole'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    orderid = db.Column(db.Integer, nullable=False, default=0)
    unionroleid = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.datetime.now)
    modified_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, orderid, unionroleid):
        self.orderid = orderid
        self.unionroleid = unionroleid

class TelegramTempMess(db.Model):

    __tablename__ = 'telegram_tempmess'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    telid = db.Column(db.String(1000), nullable=False, default='')
    messid = db.Column(db.String(1000), nullable=False, default='')
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, telid, messid):
        self.telid = telid
        self.messid = messid


class FeedbackQuestion(db.Model):

    __tablename__ = 'feedback_question'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    orderid = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, orderid):
        self.orderid = orderid

class BotSpaces(db.Model):

    __tablename__ = 'infospace_bot'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(1000), nullable=False, default='')
    spacekey = db.Column(db.String(255), nullable=False, default='')

    def __init__(self, title, spacekey):
        self.title = title
        self.spacekey = spacekey

class SendMethodInfo(db.Model):
    __tablename__ = 'sendmethodsinfo'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(500), nullable=False, default='')
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.datetime.now)
    modified_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, title):
        self.title = title

class TelBotInfo(db.Model):
    __tablename__ = 'telbotinfo'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(500), nullable=False, default='')
    botident = db.Column(db.String(500), nullable=False, default='')
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.datetime.now)
    modified_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, name, botident):
        self.name = name
        self.botident = botident

class ServiceMailInfo(db.Model):
    __tablename__ = 'servicemailinfo'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    address = db.Column(db.String(500), nullable=False, default='')
    server = db.Column(db.String(500), nullable=False, default='')
    port = db.Column(db.Integer, nullable=False, default=25)
    username = db.Column(db.String(500), nullable=False, default='')
    passw = db.Column(db.String(500), nullable=False, default='')
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.datetime.now)
    modified_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, address, server, port, username, passw):
        self.address = address
        self.server = server
        self.port = port
        self.username = username
        self.passw = passw


class SupportRequest(db.Model):

    __tablename__ = 'support_request'
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    userid = db.Column(db.Integer, ForeignKey("userpg.id"),nullable=False, default=0)
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.datetime.now)
    modified_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, userid):
        self.userid = userid

class SupportText(db.Model):

    __tablename__ = 'support_text'
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    support_id = db.Column(db.Integer, ForeignKey("support_request.id"),nullable=False, default=0)
    text = db.Column(db.String(), nullable=False, default='')
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.datetime.now)
    modified_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, support_id, text):
        self.support_id = support_id
        self.text = text

class SupportItPointInput(db.Model):

    __tablename__ = 'support_itpoint_input'
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    support_id = db.Column(db.Integer, ForeignKey("support_request.id"),nullable=False, default=0)
    input = db.Column(db.String(255), nullable=False, default='')
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.datetime.now)
    modified_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, support_id, input):
        self.support_id = support_id
        self.input = input

class SupportTelegramAttach(db.Model):

    __tablename__ = 'support_telegram_attach'
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    support_id = db.Column(db.Integer, ForeignKey("support_request.id"),nullable=False, default=0)
    uniqid = db.Column(db.String(1000), nullable=False, default='')
    caption = db.Column(db.String(1000), nullable=False, default='')
    type = db.Column(db.String(255), nullable=False, default='')
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.datetime.now)
    modified_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, support_id, uniqid, caption, type):
        self.support_id = support_id
        self.uniqid = uniqid
        self.caption = caption
        self.type = type

class SupportProblem(db.Model):

    __tablename__ = 'support_problem'
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    support_id = db.Column(db.Integer, ForeignKey("support_request.id"),nullable=False, default=0)
    global_id = db.Column(db.String(500), nullable=False, default='')
    system_object_id = db.Column(db.String(500), nullable=False, default='')
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.datetime.now)
    modified_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, support_id, global_id, system_object_id):
        self.support_id = support_id
        self.global_id = global_id
        self.system_object_id = system_object_id


class SupportService(db.Model):

    __tablename__ = 'support_service'
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    support_id = db.Column(db.Integer, ForeignKey("support_request.id"),nullable=False, default=0)
    global_id = db.Column(db.String(500), nullable=False, default='')
    system_object_id = db.Column(db.String(500), nullable=False, default='')
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.datetime.now)
    modified_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, support_id, global_id, system_object_id):
        self.support_id = support_id
        self.global_id = global_id
        self.system_object_id = system_object_id

class SupportUnionRole(db.Model):

    __tablename__ = 'support_unionrole'
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    support_id = db.Column(db.Integer, ForeignKey("support_request.id"),nullable=False, default=0)
    unionrole_id = db.Column(db.Integer, ForeignKey("unionrole.id"), nullable=False, default=0)
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.datetime.now)
    modified_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, support_id, unionrole_id):
        self.support_id = support_id
        self.unionrole_id = unionrole_id

class SupportAttempt(db.Model):

    __tablename__ = 'support_attempt'
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    support_id = db.Column(db.Integer, ForeignKey("support_request.id"),nullable=False, default=0)
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.datetime.now)
    modified_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, support_id):
        self.support_id = support_id

class StatusSupport(db.Model):

    __tablename__ = 'status_support'
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False, default='')
    db_name = db.Column(db.String(255), nullable=False, default='')
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.datetime.now)
    modified_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, name, db_name):
        self.name = name
        self.db_name = db_name


class SupportToStatus(db.Model):

    __tablename__ = 'support_to_status'
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    support_id = db.Column(db.Integer, ForeignKey("support_request.id"),nullable=False, default=0)
    status_id = db.Column(db.Integer, ForeignKey("status_support.id"), nullable=False, default=0)
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.datetime.now)
    modified_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, support_id, status_id):
        self.support_id = support_id
        self.status_id = status_id




