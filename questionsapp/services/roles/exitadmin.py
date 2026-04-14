from questionsapp.models import UserBaseRole
from database import db
from app.core.runtime_config import get_base_roles

def exit_admin(userid):
    if userid:
        try:
            check_role = UserBaseRole.query.filter_by(userid=int(userid)).first()

            if check_role is not None:
                base_roles = get_base_roles()
                if check_role.roleid == int(base_roles['admin']['id']):
                    check_role.roleid = int(base_roles['redactor']['id'])
                    db.session.commit()
                return {'status': 'ok'}
            else:
                return {'status': 'error', 'error_mess': 'WARN: No user role rec'}
        except Exception as e:
            print(str(e))
            return {'status_info': {'status': 'error', 'error_mess': str(e)}}
    else:
        return {'status': 'error', 'error_mess': 'WARN: No userid'}
