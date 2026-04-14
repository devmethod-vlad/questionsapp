from app.db.legacy_db import db
import bcrypt
from app.core.runtime_config import get_default_format
from questionsapp.models import UserManualInfo

def change_admin_pass(userid, adminpass):
    if adminpass and userid:
        try:
            checkManualRec = UserManualInfo.query.filter_by(userid=int(userid)).first()
            if checkManualRec is None:
                return {"status": "error", "error_mess": "Admin doesn't exist"}
            else:
                hashed = bcrypt.hashpw(adminpass.encode(get_default_format()), bcrypt.gensalt())
                checkManualRec.password = hashed.decode(get_default_format())
                db.session.commit()
                return {'status': 'ok'}
        except Exception as e:
            db.session.rollback()
            print(str(e))
            return {'status': 'error', 'error_mess': str(e)}
    else:
        return {'status': 'params_error', 'error_mess': 'WARN: No params'}
