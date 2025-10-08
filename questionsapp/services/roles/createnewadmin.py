from database import db
import bcrypt
from flask import current_app as app
from questionsapp.models import UserWikiInfo, UserManualInfo, UserBaseRole

def create_new_admin(edulogin, adminlogin, adminpass):
    if edulogin and adminlogin and adminpass:
        try:
            checkWikiInfo = UserWikiInfo.query.filter_by(login=edulogin).first()
            if checkWikiInfo is not None:
                checkExistAdmin = UserManualInfo.query.filter_by(userid=checkWikiInfo.userid).first()
                if checkExistAdmin is None:
                    checkUserRole = UserBaseRole.query.filter_by(userid=checkWikiInfo.userid).first()
                    if checkUserRole.roleid == 3:
                        checkExistLogin = UserManualInfo.query.filter_by(login=adminlogin).first()
                        if checkExistLogin is None:
                            if len(adminlogin) > 4:
                                hashed = bcrypt.hashpw(adminpass.encode(app.config['DEFAULT_FORMAT']), bcrypt.gensalt())
                                newManUserInfo = UserManualInfo(userid=checkWikiInfo.userid, login=adminlogin,
                                                                password=hashed.decode(app.config['DEFAULT_FORMAT']))
                                db.session.add(newManUserInfo)
                                db.session.commit()
                                return {'status': 'ok'}
                            else:
                                return {'status': 'error', 'error_mess': 'WARN: login less then 4 symbols',
                                        'info': 'Логин администратора должен состоять как минимум из 4 символов'}
                        else:
                            return {'status': 'error', 'error_mess': 'WARN: login already exist',
                                    'info': 'Пользователь с таким логином уже зарегистрирован в качестве администратора'}
                    else:
                        return {'status': 'error', 'error_mess': 'WARN: incorrect user role',
                                'info': 'Пользователь c данной ролью не может быть зарегистрирован в качесте администратора'}
                else:
                    return {'status': 'error', 'error_mess': 'WARN: admin already exist',
                            'info': 'Пользователь с таким логином уже зарегистрирован в качестве администратора'}
            else:
                return {'status': 'error', 'error_mess': 'WARN: No wiki info',
                        'info': 'Пользователь с таким логином никогда не пользовался функционалом Вопросов/Ответов'}
        except Exception as e:
            db.session.rollback()
            print(str(e))
            return {'status': 'error', 'error_mess': str(e)}
    else:
        return {'status': 'params_error', 'error_mess': 'WARN: No params'}