from questionsapp.models import UserBaseRole
from database import db
from app.core.legacy_runtime import app

def exit_admin(userid):
    if userid:
        try:
            check_role = UserBaseRole.query.filter_by(userid=int(userid)).first()

            if check_role is not None:
                if check_role.roleid == int(app.config['BASE_ROLE']['admin']['id']):
                    check_role.roleid = int(app.config['BASE_ROLE']['redactor']['id'])
                    db.session.commit()
                return {'status': 'ok'}
            else:
                return {'status': 'error', 'error_mess': 'WARN: No user role rec'}
        except Exception as e:
            print(str(e))
            return {'status_info': {'status': 'error', 'error_mess': str(e)}}
    else:
        return {'status': 'error', 'error_mess': 'WARN: No userid'}