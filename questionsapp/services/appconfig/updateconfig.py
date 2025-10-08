from database import db
from questionsapp.models import AppConfig

def update_app_config(params):
    if params['tokenlifetime'] and params['botname'] and params['uploadsize']:
        try:
            config_rec = AppConfig.query.first()
            AppConfig.query.filter_by(id=config_rec.id).update(
                {'token_expire': int(params['tokenlifetime']), 'botname': params['botname'], 'uploadsize': int(params['uploadsize'])})
            db.session.commit()
            return {'status': 'ok'}
        except Exception as e:
            db.session.rollback()
            print(str(e))
            return {'status': 'error', 'error_mess': str(e)}
    else:
        return {'status': 'params_error', 'error_mess': 'WARN: No params'}