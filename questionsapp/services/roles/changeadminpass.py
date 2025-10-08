from database import db
import bcrypt
from flask import current_app as app
from questionsapp.models import UserManualInfo

def change_admin_pass(userid, adminpass):
    if adminpass and userid:
        try:
            checkManualRec = UserManualInfo.query.filter_by(userid=int(userid)).first()
            if checkManualRec is None:
                return {"status": "error", "error_mess": "Admin doesn't exist"}
            else:
                hashed = bcrypt.hashpw(adminpass.encode(app.config['DEFAULT_FORMAT']), bcrypt.gensalt())
                checkManualRec.password = hashed.decode(app.config['DEFAULT_FORMAT'])
                db.session.commit()
                return {'status': 'ok'}
        except Exception as e:
            db.session.rollback()
            print(str(e))
            return {'status': 'error', 'error_mess': str(e)}
    else:
        return {'status': 'params_error', 'error_mess': 'WARN: No params'}