from sqlalchemy import Column, ForeignKey, Integer, String, TIMESTAMP

from app.db.base import Base
import datetime


class User(Base):

    __tablename__ = 'userpg'
    id = Column(Integer, primary_key = True, autoincrement=True)
    firstname = Column(String(1000))
    lastname = Column(String(1000))
    secondname = Column(String(1000))
    phone = Column(String(255))
    mail = Column(String(255))
    created_at = Column(TIMESTAMP, nullable=False,default=datetime.datetime.now)

    def __init__(self, firstname, lastname, secondname, phone, mail):
        self.firstname = firstname
        self.lastname = lastname
        self.secondname = secondname
        self.phone = phone
        self.mail = mail

class UserEmiasInfo(Base):
    __tablename__ = 'user_emiasinfo'
    id = Column(Integer, primary_key=True, autoincrement=True)
    userid = Column(Integer, nullable=False, default=0)
    emiaslogin = Column(String(255))

    def __init__(self, userid, emiaslogin):
        self.userid = userid
        self.emiaslogin = emiaslogin


class UserWikiInfo(Base):
    __tablename__ = 'user_wikiinfo'
    id = Column(Integer, primary_key=True, autoincrement=True)
    userid = Column(Integer, nullable=False, default=0)
    login = Column(String(255))

    def __init__(self, userid, login):
        self.userid = userid
        self.login = login

class AccessToken(Base):
    __tablename__ = 'access_token'
    id = Column(Integer, primary_key = True, autoincrement=True)
    userid = Column(Integer, nullable=False, default=0)
    token = Column(String(1000), nullable=False, default='')
    created_at = Column(TIMESTAMP, nullable=False,default=datetime.datetime.now)

    def __init__(self, userid, token):
        self.userid = userid
        self.token = token


class AppConfig(Base):
    __tablename__ = 'appconfig'
    id = Column(Integer, primary_key = True, autoincrement=True)
    token_expire = Column(Integer)
    botname = Column(String(255), nullable=False, default='')
    webappurl = Column(String(), nullable=False, default='')
    uploadsize = Column(Integer, nullable=False, default=1)
    maxfiles = Column(Integer, nullable=False, default=0)
    anonymuserid = Column(Integer, nullable=False, default=0)
    ispublicactive = Column(Integer, nullable=False, default=0)
    created_at = Column(TIMESTAMP, nullable=False,default=datetime.datetime.now)

    def __init__(self, token_expire, botname, webappurl, uploadsize, maxfiles, anonymuserid, ispublicactive):
        self.token_expire = token_expire
        self.botname = botname
        self.webappurl = webappurl
        self.uploadsize = uploadsize
        self.maxfiles = maxfiles
        self.anonymuserid = anonymuserid
        self.ispublicactive = ispublicactive

class UserTelegramInfo(Base):
    __tablename__ = 'user_telegraminfo'
    id = Column(Integer, primary_key = True, autoincrement=True)
    userid = Column(Integer, nullable=False, default=0)
    tlgmname = Column(String(255), nullable=False, default='')
    tlgmid = Column(String(1000), nullable=False, default='')
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, userid, tlgmname, tlgmid):
        self.userid = userid
        self.tlgmname = tlgmname
        self.tlgmid = tlgmid

class OrderMess(Base):
    __tablename__ = 'ordermess'
    id = Column(Integer, primary_key = True, autoincrement=True)
    userid = Column(Integer, nullable=False, default=0)
    text = Column(String(4000), nullable=False, default='')
    created_at = Column(TIMESTAMP, nullable=False,default=datetime.datetime.now)
    modified_at= Column(TIMESTAMP, nullable=False,default=datetime.datetime.now)

    def __init__(self, userid, text):
        self.userid = userid
        self.text = text

class OrderPublic(Base):
    __tablename__ = 'order_public'
    id = Column(Integer, primary_key = True, autoincrement=True)
    orderid = Column(Integer, nullable=False, default=0)
    created_at = Column(TIMESTAMP, nullable=False,default=datetime.datetime.now)

    def __init__(self, orderid):
        self.orderid = orderid

class AnonymOrder(Base):

    __tablename__ = 'anonymorder'
    id = Column(Integer, primary_key = True, autoincrement=True)
    fingerprint = Column(String(1000))
    orderid = Column(Integer, nullable=False, default=0)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)
    modified_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, fingerprint, orderid):
        self.fingerprint = fingerprint
        self.orderid = orderid

class AnonymOrderInfo(Base):

    __tablename__ = 'anonymorderinfo'
    id = Column(Integer, primary_key = True, autoincrement=True)
    orderid = Column(Integer, nullable=False, default=0)
    anonymorderid = Column(Integer, nullable=False, default=0)
    fio = Column(String(1000), nullable=False, default='')
    mail = Column(String(255), nullable=False, default='')
    phone = Column(String(255), nullable=False, default='')
    telusername = Column(String(1000), nullable=False, default='')
    tlgmid = Column(String(1000), nullable=False, default='')
    muname = Column(String(1000), nullable=False, default='')
    speciality = Column(String(2000), nullable=False, default='')
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)
    modified_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)

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

class AnswerMess(Base):
    __tablename__ = 'answermess'
    id = Column(Integer, primary_key = True, autoincrement=True)
    userid = Column(Integer, nullable=False, default=0)
    orderid = Column(Integer, nullable=False, default=0)
    text = Column(String(4000), nullable=False, default='')
    created_at = Column(TIMESTAMP, nullable=False,default=datetime.datetime.now)
    modified_at= Column(TIMESTAMP, nullable=False,default=datetime.datetime.now)

    def __init__(self, userid, orderid, text):
        self.userid = userid
        self.orderid = orderid
        self.text = text


class OrderStatus(Base):

    __tablename__ = 'order_status'
    id = Column(Integer, primary_key=True, autoincrement=True)
    orderid = Column(Integer, nullable=False, default=0)
    statusid = Column(Integer, nullable=False, default=0)
    created_at = Column(TIMESTAMP, nullable=False,default=datetime.datetime.now)
    modified_at = Column(TIMESTAMP, nullable=False,default=datetime.datetime.now)

    def __init__(self, orderid, statusid):
        self.orderid = orderid
        self.statusid = statusid

class UserManualInfo(Base):

    __tablename__ = 'user_manualinfo'
    id = Column(Integer, primary_key=True, autoincrement=True)
    userid = Column(Integer, nullable=False, default=0)
    login = Column(String(255), nullable=False, default='')
    password = Column(String(1000), nullable=False, default='')
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, userid, login, password):
        self.userid = userid
        self.login = login
        self.password = password

class BaseRole(Base):
    __tablename__ = 'baserole'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(1000), nullable=False, default='')

    def __init__(self, name):
        self.name = name

class UserBaseRole(Base):

    __tablename__ = 'user_baserole'
    id = Column(Integer, primary_key=True, autoincrement=True)
    userid = Column(Integer, nullable=False, default=0)
    roleid = Column(Integer, nullable=False, default=0)
    created_at = Column(TIMESTAMP, nullable=False,default=datetime.datetime.now)
    modified_at = Column(TIMESTAMP, nullable=False,default=datetime.datetime.now)

    def __init__(self, userid, roleid):
        self.userid = userid
        self.roleid = roleid

class Attachment(Base):

    __tablename__ = 'attachment'
    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(255), nullable=False, default='')
    path = Column(String(1000), nullable=False, default='')
    caption = Column(String, nullable=False, default='')
    public = Column(Integer, nullable=False, default=1)

    def __init__(self, type, path, caption, public):
        self.type = type
        self.path = path
        self.caption = caption
        self.public = public

class OrderAttachment(Base):

    __tablename__ = 'order_attachment'
    id = Column(Integer, primary_key=True, autoincrement=True)
    attachid = Column(Integer, nullable=False, default=0)
    orderid = Column(Integer, nullable=False, default=0)
    created_at = Column(TIMESTAMP, nullable=False,default=datetime.datetime.now)

    def __init__(self, attachid, orderid):
        self.attachid = attachid
        self.orderid = orderid

class AnswerAttachment(Base):

    __tablename__ = 'answer_attachment'
    id = Column(Integer, primary_key=True, autoincrement=True)
    attachid = Column(Integer, nullable=False, default=0)
    answerid = Column(Integer, nullable=False, default=0)
    created_at = Column(TIMESTAMP, nullable=False,default=datetime.datetime.now)

    def __init__(self, attachid, answerid):
        self.attachid = attachid
        self.answerid = answerid

class TelegramAttachment(Base):

    __tablename__ = 'telegram_attachment'
    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(255), nullable=False, default='')
    uniqid = Column(String(1000), nullable=False, default='')
    caption = Column(String(), nullable=False, default='')
    path = Column(String(), nullable=False, default='')

    def __init__(self, type, uniqid, caption, path):
        self.type = type
        self.uniqid = uniqid
        self.caption = caption
        self.path = path

class AnswerTelegramAttachment(Base):

    __tablename__ = 'answer_tlgm_attachment'
    id = Column(Integer, primary_key=True, autoincrement=True)
    attachid = Column(Integer, nullable=False, default=0)
    answerid = Column(Integer, nullable=False, default=0)
    created_at = Column(TIMESTAMP, nullable=False,default=datetime.datetime.now)

    def __init__(self, attachid, answerid):
        self.attachid = attachid
        self.answerid = answerid


class OrderTelegramAttachment(Base):

    __tablename__ = 'order_tlgm_attachment'
    id = Column(Integer, primary_key=True, autoincrement=True)
    attachid = Column(Integer, nullable=False, default=0)
    orderid = Column(Integer, nullable=False, default=0)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, attachid, orderid):
        self.attachid = attachid
        self.orderid = orderid


class SyncAttachments(Base):

    __tablename__ = 'sync_attachments'
    id = Column(Integer, primary_key=True, autoincrement=True)
    webattachid = Column(Integer, nullable=False, default=0)
    telattachid = Column(Integer, nullable=False, default=0)
    created_at = Column(TIMESTAMP, nullable=False,default=datetime.datetime.now)

    def __init__(self, webattachid, telattachid):
        self.webattachid = webattachid
        self.telattachid = telattachid

class OrdersInWork(Base):

    __tablename__ = 'orders_inwork'
    id = Column(Integer, primary_key=True, autoincrement=True)
    userid = Column(Integer, nullable=False, default=0)
    orderid = Column(Integer, nullable=False, default=0)
    created_at = Column(TIMESTAMP, nullable=False,default=datetime.datetime.now)

    def __init__(self, userid, orderid):
        self.userid = userid
        self.orderid = orderid

class Spaces(Base):

    __tablename__ = 'infospace'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(1000), nullable=False, default='')
    spacekey = Column(String(255), nullable=False, default='')

    def __init__(self, title, spacekey):
        self.title = title
        self.spacekey = spacekey

class TelChatInfoSpace(Base):

    __tablename__ = 'telchat_infospace'
    id = Column(Integer, primary_key=True, autoincrement=True)
    spaceid = Column(Integer, nullable=False, default=0)
    chatid = Column(String(500), nullable=False, default='')

    def __init__(self, spaceid, chatid):
        self.spaceid = spaceid
        self.chatid = chatid

class OrderSpace(Base):

    __tablename__ = 'order_infospace'
    id = Column(Integer, primary_key=True, autoincrement=True)
    orderid = Column(Integer, nullable=False, default=0)
    spaceid = Column(Integer, nullable=False, default=0)

    def __init__(self, orderid, spaceid):
        self.orderid = orderid
        self.spaceid = spaceid

class TelPhrazeStats(Base):

    __tablename__ = 'telphrazestats'
    id = Column(Integer, primary_key=True, autoincrement=True)
    userid = Column(Integer, nullable=False, default=0)
    searchphrase = Column(String(4000), nullable=False, default='')
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, userid, searchphrase):
        self.userid = userid
        self.searchphrase = searchphrase

class UnionRole(Base):

    __tablename__ = 'unionrole'
    id = Column(Integer, primary_key=True, autoincrement=True)
    emiasid = Column(Integer, nullable=False, default=0)
    name = Column(String(3000), nullable=False, default='')
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)
    modified_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, emiasid, name):
        self.emiasid = emiasid
        self.name = name

class SpaceUnionRole(Base):

    __tablename__ = 'infospace_unionrole'
    id = Column(Integer, primary_key=True, autoincrement=True)
    spaceid = Column(Integer, nullable=False, default=0)
    unionroleid = Column(Integer, nullable=False, default=0)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)
    modified_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, spaceid, unionroleid):
        self.spaceid = spaceid
        self.unionroleid = unionroleid

class SpaceUnionRoleActive(Base):

    __tablename__ = 'spaceunionrole_isactive'
    id = Column(Integer, primary_key=True, autoincrement=True)
    spaceid = Column(Integer, nullable=False, default=0)
    active = Column(Integer, nullable=False, default=0)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)
    modified_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, spaceid, active):
        self.spaceid = spaceid
        self.active = active

class UserUnionRole(Base):

    __tablename__ = 'user_unionrole'
    id = Column(Integer, primary_key=True, autoincrement=True)
    userid = Column(Integer, nullable=False, default=0)
    unionroleid = Column(Integer, nullable=False, default=0)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)
    modified_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, userid, unionroleid):
        self.userid = userid
        self.unionroleid = unionroleid

class OrderUnionRole(Base):

    __tablename__ = 'order_unionrole'
    id = Column(Integer, primary_key=True, autoincrement=True)
    orderid = Column(Integer, nullable=False, default=0)
    unionroleid = Column(Integer, nullable=False, default=0)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)
    modified_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, orderid, unionroleid):
        self.orderid = orderid
        self.unionroleid = unionroleid

class TelegramTempMess(Base):

    __tablename__ = 'telegram_tempmess'
    id = Column(Integer, primary_key=True, autoincrement=True)
    telid = Column(String(1000), nullable=False, default='')
    messid = Column(String(1000), nullable=False, default='')
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, telid, messid):
        self.telid = telid
        self.messid = messid


class FeedbackQuestion(Base):

    __tablename__ = 'feedback_question'
    id = Column(Integer, primary_key=True, autoincrement=True)
    orderid = Column(Integer, nullable=False, default=0)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, orderid):
        self.orderid = orderid

class BotSpaces(Base):

    __tablename__ = 'infospace_bot'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(1000), nullable=False, default='')
    spacekey = Column(String(255), nullable=False, default='')

    def __init__(self, title, spacekey):
        self.title = title
        self.spacekey = spacekey

class SendMethodInfo(Base):
    __tablename__ = 'sendmethodsinfo'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False, default='')
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)
    modified_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, title):
        self.title = title

class TelBotInfo(Base):
    __tablename__ = 'telbotinfo'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(500), nullable=False, default='')
    botident = Column(String(500), nullable=False, default='')
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)
    modified_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, name, botident):
        self.name = name
        self.botident = botident

class ServiceMailInfo(Base):
    __tablename__ = 'servicemailinfo'
    id = Column(Integer, primary_key=True, autoincrement=True)
    address = Column(String(500), nullable=False, default='')
    server = Column(String(500), nullable=False, default='')
    port = Column(Integer, nullable=False, default=25)
    username = Column(String(500), nullable=False, default='')
    passw = Column(String(500), nullable=False, default='')
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)
    modified_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, address, server, port, username, passw):
        self.address = address
        self.server = server
        self.port = port
        self.username = username
        self.passw = passw


class SupportRequest(Base):

    __tablename__ = 'support_request'
    id = Column(Integer, primary_key = True, autoincrement=True)
    userid = Column(Integer, ForeignKey("userpg.id"),nullable=False, default=0)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)
    modified_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, userid):
        self.userid = userid

class SupportText(Base):

    __tablename__ = 'support_text'
    id = Column(Integer, primary_key = True, autoincrement=True)
    support_id = Column(Integer, ForeignKey("support_request.id"),nullable=False, default=0)
    text = Column(String(), nullable=False, default='')
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)
    modified_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, support_id, text):
        self.support_id = support_id
        self.text = text

class SupportItPointInput(Base):

    __tablename__ = 'support_itpoint_input'
    id = Column(Integer, primary_key = True, autoincrement=True)
    support_id = Column(Integer, ForeignKey("support_request.id"),nullable=False, default=0)
    input = Column(String(255), nullable=False, default='')
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)
    modified_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, support_id, input):
        self.support_id = support_id
        self.input = input

class SupportTelegramAttach(Base):

    __tablename__ = 'support_telegram_attach'
    id = Column(Integer, primary_key = True, autoincrement=True)
    support_id = Column(Integer, ForeignKey("support_request.id"),nullable=False, default=0)
    uniqid = Column(String(1000), nullable=False, default='')
    caption = Column(String(1000), nullable=False, default='')
    type = Column(String(255), nullable=False, default='')
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)
    modified_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, support_id, uniqid, caption, type):
        self.support_id = support_id
        self.uniqid = uniqid
        self.caption = caption
        self.type = type

class SupportProblem(Base):

    __tablename__ = 'support_problem'
    id = Column(Integer, primary_key = True, autoincrement=True)
    support_id = Column(Integer, ForeignKey("support_request.id"),nullable=False, default=0)
    global_id = Column(String(500), nullable=False, default='')
    system_object_id = Column(String(500), nullable=False, default='')
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)
    modified_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, support_id, global_id, system_object_id):
        self.support_id = support_id
        self.global_id = global_id
        self.system_object_id = system_object_id


class SupportService(Base):

    __tablename__ = 'support_service'
    id = Column(Integer, primary_key = True, autoincrement=True)
    support_id = Column(Integer, ForeignKey("support_request.id"),nullable=False, default=0)
    global_id = Column(String(500), nullable=False, default='')
    system_object_id = Column(String(500), nullable=False, default='')
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)
    modified_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, support_id, global_id, system_object_id):
        self.support_id = support_id
        self.global_id = global_id
        self.system_object_id = system_object_id

class SupportUnionRole(Base):

    __tablename__ = 'support_unionrole'
    id = Column(Integer, primary_key = True, autoincrement=True)
    support_id = Column(Integer, ForeignKey("support_request.id"),nullable=False, default=0)
    unionrole_id = Column(Integer, ForeignKey("unionrole.id"), nullable=False, default=0)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)
    modified_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, support_id, unionrole_id):
        self.support_id = support_id
        self.unionrole_id = unionrole_id

class SupportAttempt(Base):

    __tablename__ = 'support_attempt'
    id = Column(Integer, primary_key = True, autoincrement=True)
    support_id = Column(Integer, ForeignKey("support_request.id"),nullable=False, default=0)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)
    modified_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, support_id):
        self.support_id = support_id

class StatusSupport(Base):

    __tablename__ = 'status_support'
    id = Column(Integer, primary_key = True, autoincrement=True)
    name = Column(String(255), nullable=False, default='')
    db_name = Column(String(255), nullable=False, default='')
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)
    modified_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, name, db_name):
        self.name = name
        self.db_name = db_name


class SupportToStatus(Base):

    __tablename__ = 'support_to_status'
    id = Column(Integer, primary_key = True, autoincrement=True)
    support_id = Column(Integer, ForeignKey("support_request.id"),nullable=False, default=0)
    status_id = Column(Integer, ForeignKey("status_support.id"), nullable=False, default=0)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)
    modified_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)

    def __init__(self, support_id, status_id):
        self.support_id = support_id
        self.status_id = status_id




