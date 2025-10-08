from database import db
from questionsapp.models import AppConfig, OrderPublic, UserBaseRole
from questionsapp.services.questions.savequestion import save_question
from questionsapp.services.questions.saveanswer import save_answer
from questionsapp.services.roles.getrole import get_role
from tasks.publicorder import publicOrder
import os

def save_combine(params):

    app_conf_rec = AppConfig.query.first()

    if params["publicorder"]:
        if int(params["publicorder"]) == 1 and app_conf_rec.ispublicactive == 1:
            return {'status': 'publicactive'}

    save_quest = save_question(params)


    if save_quest['status'] == 'ok':

        question_id = save_quest['info']['messid']

        params['orderid'] = question_id

        check_role = UserBaseRole.query.filter_by(userid=int(params['userid'])).first()

        role = get_role(check_role.roleid)

        if isinstance(params['answer_text'], str):
            if params['answer_text'] != '':
                save_quest_answer = save_answer(params)

                if save_quest_answer['status'] == 'ok':
                    if params["publicorder"]:
                        if int(params["publicorder"]) == 1:
                            check_public = OrderPublic.query.filter_by(orderid=int(question_id)).first()

                            if check_public:
                                db.session.delete(check_public)
                                db.session.commit()

                            new_public = OrderPublic(orderid=int(question_id))
                            db.session.add(new_public)
                            db.session.commit()

                            if int(os.getenv('PROD')) == 1:
                                publicOrder.delay(question_id)
                            else:
                                print("PUBLIC QUESTION!!!")

                    return {'status': 'ok', 'info': {'order_info': {'files': save_quest['info']['files'],
                                                                    'messid': save_quest['info']['messid'],
                                                                    'text': save_quest['info']['text'],
                                                                    'attachments': save_quest['info'][
                                                                        'attachments']}}}
                else:
                    return {'status': 'error_answer', 'error_mess': 'WARN: save answer error'}

            else:
                if role == 'admin':
                    return save_quest
        return save_quest

    else:
        return save_quest