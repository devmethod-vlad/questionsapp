from questionsapp.models import UserTelegramInfo, UserBaseRole, UserManualInfo, BaseRole
from questionsapp.models import UserEmiasInfo, UserWikiInfo, User

#Изменения:
#-Изменено название функции setterUserInfo на set_user_info
#-Изменен аргумент onlytelstatus на onlyreginfo. Изменилсь поведение в связи с этим
#при указании этого аргумента выводится информация о том в каких приложениях зарегистрирован пользователь
#Соответсвенно, меняется ответ с telstatus на appreginfо:{'telegram':1(0)}
#-manual login заменен на adminlogin
def set_user_info(userid, onlyreginfo=False):
    #Здесь должна быть проверка на регистрацию пользователя в разных приложениях
    check_telegram = UserTelegramInfo.query.filter_by(userid=userid).first()

    if check_telegram is None:
        tel_reg = 0
    else:
        tel_reg = 1

    if onlyreginfo:
        return {'appreginfо':{'telegram':tel_reg}}

    else:
        user_role_rec = UserBaseRole.query.filter_by(userid=userid).first()
        if user_role_rec is not None:
            role_rec = BaseRole.query.filter_by(id=user_role_rec.roleid).first()
            userrole = {'id': user_role_rec.roleid, 'name': role_rec.name}
        else:
            userrole = {'id': 0, 'name': ''}

        user_admin_rec = UserManualInfo.query.filter_by(userid=userid).first()

        if user_admin_rec is not None:
            adminlogin = user_admin_rec.login
        else:
            adminlogin = ''

        user_emias_rec = UserEmiasInfo.query.filter_by(userid=userid).first()
        if user_emias_rec is not None:
            emiaslogin = user_emias_rec.emiaslogin
        else:
            emiaslogin = ''

        user_wiki_rec = UserWikiInfo.query.filter_by(userid=userid).first()
        if user_wiki_rec is not None:
            wikilogin = user_wiki_rec.login
        else:
            wikilogin = ''

        user_rec = User.query.filter_by(id=userid).first()

        return {'userid': userid, 'appreginfo':{'telegram':tel_reg}, 'wikilogin': wikilogin, 'userlastname': user_rec.lastname,
                'userfirstname': user_rec.firstname, 'emiaslogin': emiaslogin, 'usersecondname': user_rec.secondname,
                'userrole': userrole,
                'adminlogin': adminlogin}

def getUserInfo(userid):
    userRec = User.query.filter_by(id=userid).first()

    userEmiasRec = UserEmiasInfo.query.filter_by(userid=userid).first()
    if userEmiasRec is not None:
        emiaslogin = userEmiasRec.emiaslogin
    else:
        emiaslogin = ''

    telegramRec = UserTelegramInfo.query.filter_by(userid=userid).first()
    if telegramRec is None:
        telId = ''
        telName = ''
    else:
        telId = str(telegramRec.tlgmid)
        telName = telegramRec.tlgmname

    userWikiRec = UserWikiInfo.query.filter_by(userid=userid).first()
    if userWikiRec is not None:
        wikilogin = userWikiRec.login
    else:
        wikilogin = ''

    return {'telinfo': {'telid':telId, 'telName':telName}, 'wikilogin': wikilogin, 'userlastname': userRec.lastname,
            'userfirstname': userRec.firstname, 'emiaslogin': emiaslogin, 'usersecondname': userRec.secondname}