from flask import current_app as app

def tranform_status_list(status_name_list):
    status_id_list = []

    for item in status_name_list:
        if item in app.config['QUESTION_STATUS']:
            status_id_list.append(app.config['QUESTION_STATUS'][item]['id'])

    return status_id_list
