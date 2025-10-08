from database import db
from questionsapp.models import UserManualInfo, UserBaseRole, AccessToken
import bcrypt, secrets
from flask import current_app as app
from questionsapp.services.user.userinfo import set_user_info


def enter_admin(login, password, userid):
    if login and password and userid:
        check_admin = UserManualInfo.query.filter_by(login=login).first()
        if check_admin and check_admin.userid == int(userid):
            if bcrypt.checkpw(password.encode(app.config['DEFAULT_FORMAT']), check_admin.password.encode('UTF-8')):
                check_role = UserBaseRole.query.filter_by(userid=check_admin.userid).first()
                check_role.roleid = 1
                db.session.add(check_role)
                access_token = secrets.token_urlsafe(16)
                del_token = AccessToken.query.filter_by(userid=check_admin.userid).first()
                if del_token is not None:
                    db.session.delete(del_token)
                    db.session.commit()
                new_token = AccessToken(userid=check_admin.userid, token=access_token)
                db.session.add(new_token)
                userinfo = {'token': access_token}
                user_info = set_user_info(check_admin.userid)
                userinfo.update(user_info)
                userinfo['userrole'] = {'id': 1, 'name': 'Администратор'}
                db.session.commit()
                return {'status': 'ok', 'info': userinfo}
            else:
                return {'status': 'not_match', 'error_mess': 'WARN: Data is incorrect'}
        else:
            return {'status': 'not_found', 'error_mess': 'WARN: Login not found'}
    else:
        return {'status': 'error', 'error_mess': 'WARN: No params'}