from questionsapp.models import AppConfig

def get_appconfig_info():
    check_config = AppConfig.query.first()

    if check_config is not None:
        return {'status': 'ok', 'info': {
            'token_expire': check_config.token_expire,
            'botname': check_config.botname,
            'uploadsize': check_config.uploadsize,
            'maxfiles': check_config.maxfiles,
            'anonymuserid': check_config.anonymuserid,
            'ispublicactive': check_config.ispublicactive
        }}
    else:
        return {'status': 'error', 'error_mess': 'WARN: No config'}