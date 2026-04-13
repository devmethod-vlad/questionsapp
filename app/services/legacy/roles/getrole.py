from flask import current_app as app

def get_role(roleid):
    for item in app.config['BASE_ROLE']:
        if app.config['BASE_ROLE'][item]['id'] == int(roleid):
            return item
    return None

