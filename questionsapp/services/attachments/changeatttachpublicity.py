from database import db
from questionsapp.models import Attachment

def change_attach_publicity(attachid, publicflag):
    if attachid:
        check_attach = Attachment.query.filter_by(id=int(attachid)).first()

        if check_attach is not None:
            check_attach.public = int(publicflag)
            db.session.commit()
            return {'status': 'ok'}

        else:
            return {'status': 'error', 'error_mess': 'WARN: No attachment with attachid'}

    else:
        return {'status': 'error', 'error_mess': 'WARN: No attachid'}