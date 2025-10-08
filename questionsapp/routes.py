from flask import current_app as app, render_template
from pytz import timezone
import requests
from questionsapp.models import UserTelegramInfo, OrderMess, AnonymOrder
from flask import request, send_from_directory
from questionsapp.services.questionslist.formquestionslist import form_questions_list, find_question_in_list
from questionsapp.services.auxillary.getrolesbyspace import get_roles_by_space
from questionsapp.services.questions.savequestion import save_question
from questionsapp.services.questions.execaction import exec_action
from questionsapp.services.questions.savecombine import save_combine
from questionsapp.services.questions.saveanonymquestion import save_anonym_question
from questionsapp.services.attachments.changeatttachpublicity import change_attach_publicity
from questionsapp.services.attachments.deleteattachment import delete_attachment
from questionsapp.services.roles.createnewadmin import create_new_admin
from questionsapp.services.roles.changeadminpass import change_admin_pass
from questionsapp.services.appconfig.updateconfig import update_app_config
from questionsapp.services.stats.bot.getnewuser import get_newuser_stat
from questionsapp.services.stats.bot.getphrazestat import get_phraze_stat
from questionsapp.services.stats.bot.phrazesperdaystat import get_perdayphrazes_stat
from questionsapp.services.roles.enteradmin import enter_admin
from questionsapp.services.appconfig.getappconfig import get_appconfig_info
from questionsapp.services.roles.exitadmin import exit_admin
from tasks.getfollowers import get_followers_excel
from tasks.getsuppinfo import get_supp_info
from tasks.updatespaceinfo import update_spaces_info
from tasks.updatespaceinfo_new import update_spaces_info_ref


east = timezone('Europe/Moscow')

@app.route(app.config['URL_PREFIX']+"/test/")
def index():
    return 'Test success!!!'


# ОСНОВНАЯ ЛОГИКА
@app.route(app.config['URL_PREFIX']+"/questionslist/", methods = ['POST'])
def form_list():
    if request.method == 'POST':
        data = request.json
        params = {
            'userid': data.get('userid'),
            'roleid': data.get('roleid'),
            'orderid': data.get('orderid'),
            'spaceid': data.get('spaceid'),
            'statusid': data.get('statusid'),
            'perpagecount': data.get('perpagecount'),
            'activepage': data.get('activepage'),
            'datesort': data.get('datesort'),
            'searchinput': data.get('searchinput'),
            'enablesearch': data.get('enablesearch'),
            'isfeedback': data.get('isfeedback'),
            "showonlypublic": data.get('showonlypublic'),
            'usertoken': data.get('usertoken'),
            'forsynchroflag': data.get('forsynchroflag'),
            'findquestioninlist': data.get('findquestioninlist')
        }

        if params['findquestioninlist']:
            return find_question_in_list(params)
        else:
            return form_questions_list(params)

    else:
        return {'status': 'error', 'error_mess': 'WARN: Incorrect request method'}

@app.route(app.config['URL_PREFIX']+"/updatespace_old/", methods = ['GET'])
def update_spaces_old():
    # return update_spaces_info.delay()
    return update_spaces_info()

@app.route(app.config['URL_PREFIX']+"/updatespace_new/", methods = ['GET'])
def update_spaces_new():
    # return update_spaces_info.delay()
    return update_spaces_info_ref()


@app.route(app.config['URL_PREFIX']+"/spaceandroles/", methods = ['POST'])
def space_and_roles():
    if request.method == 'POST':
        data = request.json
        action = data.get('action')
        spaceid = data.get('spaceid')
        roleid = data.get('roleid')
        userid = data.get('userid')

        if action:
            if action == 'getrolesbyspace':
                return get_roles_by_space(spaceid, roleid, userid)
            else:
                return {'status': 'error', 'error_mess': 'WARN: No valid action param'}
        else:
            return {'status': 'error', 'error_mess': 'WARN: No action param'}

    else:
        return {'status': 'error', 'error_mess': 'WARN: Incorrect request method'}

@app.route(app.config['URL_PREFIX']+"/saveorupdate/", methods = ['POST'])
def save_or_update():
    if request.method == 'POST':
        action = request.form.get('action')

        params = {
            "spacekey": request.form.get('spacekey'),
            "orderid": request.form.get('orderid'),
            "userid": request.form.get('userid'),
            "unionroleid": request.form.get('unionroleid'),
            "question_text": request.form.get('question_text'),
            "answer_text": request.form.get('answer_text'),
            "question_files": request.files.getlist("question_files[]"),
            "answer_files": request.files.getlist("answer_files[]"),
            "publicorder": request.form.get('publicorder'),
            "fastformflag": request.form.get('fastformflag'),
            "userfingerprintid": request.form.get('userfingerprintid'),
            "fio": request.form.get('fio'),
            "login": request.form.get('login'),
            "muname": request.form.get('muname'),
            "phone": request.form.get('phone'),
            "mail": request.form.get('mail'),
            "isfeedback": request.form.get('isfeedback')
        }

        # print(params)

        if action:
            if action == 'save_question':
                return save_question(params)
            elif action == 'save_combine':
                return save_combine(params)
            elif action == 'save_anonym_question':
                return save_anonym_question(params)
            else:
                return {'status': 'error', 'error_mess': 'WARN: No valid action param'}
        else:
            return {'status': 'error', 'error_mess': 'WARN: No action param'}

    else:
        return {'status': 'error', 'error_mess': 'WARN: Incorrect request method'}


@app.route(app.config['URL_PREFIX']+"/service/", methods = ['POST'])
def questions_service():
    if request.method == 'POST':
        data = request.json
        action = data.get('action')
        orderid = data.get('orderid')
        userid = data.get('userid')
        attachid = data.get('attachid')
        execute_action = data.get('execute_action')
        publicflag = data.get('publicflag')
        attach_target = data.get('attach_target')
        edulogin = data.get('edulogin')
        adminlogin = data.get('adminlogin')
        adminpass = data.get('adminpass')

        app_params = {
            'tokenlifetime': data.get('tokenlifetime'),
            'botname': data.get('botname'),
            'uploadsize': data.get('uploadsize'),
        }

        if action:

            if action == 'execaction':
                return exec_action(execute_action, orderid, userid)
            elif action == 'changefilepublicity':
                return change_attach_publicity(attachid, publicflag)
            elif action == 'deleteattachment':
                return delete_attachment(attach_target, attachid, orderid, userid)
            elif action == 'createnewadmin':
                return create_new_admin(edulogin, adminlogin, adminpass)
            elif action == 'changeadminpass':
                return change_admin_pass(userid, adminpass)
            elif action == 'updateappconfig':
                return update_app_config(app_params)
            elif action == 'getappconfiginfo':
                return get_appconfig_info()
            elif action == 'enteradmin':
                return enter_admin(adminlogin, adminpass, userid)
            elif action == 'exitadmin':
                return exit_admin(userid)
            elif action == 'updtspacesbyconfl':
                update_spaces_info.delay()
                return {'status': 'ok'}
            else:
                return {'status': 'error', 'error_mess': 'WARN: No valid action param'}
        else:
            return {'status': 'error', 'error_mess': 'WARN: No action param'}

    else:
        return {'status': 'error', 'error_mess': 'WARN: Incorrect request method'}

@app.route(app.config['URL_PREFIX']+"/statistic/", methods = ['POST'])
def questions_statistic():
    if request.method == 'POST':
        data = request.json
        action = data.get('action')
        botstatskind = data.get('botstatskind')
        botimeperiod = data.get('botimeperiod')
        botdownloadflag = data.get('botdownloadflag')

        if action:
            if action == 'getbotstat':
                if botstatskind and botimeperiod:
                    delta = ""
                    if int(botimeperiod) == 7:
                        delta = "7day"
                    elif int(botimeperiod) == 30:
                        delta = "30day"

                    if botstatskind == "newusers":
                        return get_newuser_stat(delta, botdownloadflag)
                    elif botstatskind == "phrazestats":
                        return get_phraze_stat(delta, botdownloadflag)
                    elif botstatskind == "phrazesperday":
                        return get_perdayphrazes_stat(delta, botdownloadflag)

                return {'status': 'error', 'error_mess': 'WARN: No params'}

            else:
                return {'status': 'error', 'error_mess': 'WARN: No valid action param'}
        else:
            return {'status': 'error', 'error_mess': 'WARN: No action param'}

    else:
        return {'status': 'error', 'error_mess': 'WARN: Incorrect request method'}

@app.route(app.config['URL_PREFIX']+"/botexcel/", methods = ['POST'])
def bot_get_excel():
    if request.method == 'POST':
        data = request.json
        action = data.get('action')
        chatid = data.get('chatid')

        if action and chatid:
            if action == 'getfollowersexcel':

                data = {"chat_id": chatid,
                        "text": '⚠ <b>Запрос принят. Ожидайте ваш файл с результатами</b>',
                        'parse_mode': 'html'}

                requests.post(app.config['TEL_SENDMESS_URL'], data=data)

                if app.config['FLASK_ENV'] == 'production':
                    get_followers_excel.delay(chatid)
                else:
                    get_followers_excel(chatid)
                return {'status': 'ok'}
            elif action == 'getsuppinfo':
                print("getsuppinfo")
                data = {"chat_id": chatid,
                        "text": '⚠ <b>Запрос принят. Ожидайте ваш файл с результатами</b>',
                        'parse_mode': 'html'}

                requests.post(app.config['TEL_SENDMESS_URL'], data=data)

                if app.config['FLASK_ENV'] == 'production':
                    get_supp_info(chatid)
                else:
                    get_supp_info(chatid)
                return {'status': 'ok'}
            else:
                return {'status': 'error', 'error_mess': 'WARN: No valid action param'}
        else:
            return {'status': 'error', 'error_mess': 'WARN: No params'}

    else:
        return {'status': 'error', 'error_mess': 'WARN: Incorrect request method'}

# РАБОТА СО СТАТИКОЙ
@app.route(app.config['URL_PREFIX']+'/static/main/js/<path:filename>')
def questions_static_main_js(filename):
    return send_from_directory(app.config['MAIN_JS_FOLDER'],filename, as_attachment=True)

@app.route(app.config['URL_PREFIX']+'/static/main/css/<path:filename>')
def questions_static_main_css(filename):
    return send_from_directory(app.config['MAIN_CSS_FOLDER'],filename, as_attachment=True)


@app.route(app.config['URL_PREFIX']+'/static/main/imgs/<path:filename>')
def questions_static_main_imgs(filename):
    return send_from_directory(app.config['MAIN_IMGS_FOLDER'],filename, as_attachment=True)

@app.route(app.config['URL_PREFIX']+'/static/webappauth/js/<path:filename>')
def webappauth_static_js(filename):
    return send_from_directory(app.config['WEBAPPAUTH_JS_FOLDER'],filename, as_attachment=True)

@app.route(app.config['URL_PREFIX']+'/static/webappauth/css/<path:filename>')
def webappauth_static_css(filename):
    return send_from_directory(app.config['WEBAPPAUTH_CSS_FOLDER'],filename, as_attachment=True)


@app.route(app.config['URL_PREFIX']+'/static/webappauth/imgs/<path:filename>')
def webappauth_static_imgs(filename):
    return send_from_directory(app.config['WEBAPPAUTH_IMGS_FOLDER'],filename, as_attachment=True)

@app.route(app.config['URL_PREFIX']+'/static/webapp/js/<path:filename>')
def webapp_static_js(filename):
    return send_from_directory(app.config['WEBAPPMAIN_JS_FOLDER'],filename, as_attachment=True)

@app.route(app.config['URL_PREFIX']+'/static/webapp/css/<path:filename>')
def webapp_static_css(filename):
    return send_from_directory(app.config['WEBAPPMAIN_CSS_FOLDER'],filename, as_attachment=True)


@app.route(app.config['URL_PREFIX']+'/static/webapp/imgs/<path:filename>')
def webapp_static_imgs(filename):
    return send_from_directory(app.config['WEBAPPMAIN_IMGS_FOLDER'],filename, as_attachment=True)

@app.route(app.config['URL_PREFIX']+'/static/webappanonymviewer/js/<path:filename>')
def wappanonymviewer_static_js(filename):
    return send_from_directory(app.config['WAPPANONYMVIEWER_JS_FOLDER'],filename, as_attachment=True)

@app.route(app.config['URL_PREFIX']+'/static/webappanonymviewer/css/<path:filename>')
def wappanonymviewer_static_css(filename):
    return send_from_directory(app.config['WAPPANONYMVIEWER_CSS_FOLDER'],filename, as_attachment=True)


@app.route(app.config['URL_PREFIX']+'/static/webappanonymviewer/imgs/<path:filename>')
def wappanonymviewer_static_imgs(filename):
    return send_from_directory(app.config['WAPPANONYMVIEWER_IMGS_FOLDER'],filename, as_attachment=True)


@app.route(app.config['URL_PREFIX']+'/static/js/<path:filename>')
def questions_static_js(filename):
    return send_from_directory(app.config['JS_FOLDER'],filename, as_attachment=True)

@app.route(app.config['URL_PREFIX']+'/static/fonts/<path:filename>')
def questions_static_fonts(filename):
    return send_from_directory(app.config['FONTS_FOLDER'],filename, as_attachment=True)


@app.route(app.config['URL_PREFIX']+'/static/css/<path:filename>')
def questions_static_css(filename):
    return send_from_directory(app.config['CSS_FOLDER'],filename, as_attachment=True)


@app.route(app.config['URL_PREFIX']+'/static/imgs/<path:filename>')
def questions_static_imgs(filename):
    return send_from_directory(app.config['IMGS_SRC'],filename, as_attachment=True)

@app.route(app.config['URL_PREFIX']+'/static/attachments/orders/<int:userid>/<int:orderid>/<path:filename>')
def show_orders_attachments(userid, orderid, filename):
    return send_from_directory(app.config['QUESTION_ATTACHMENTS']+'/'+str(userid)+"/"+str(orderid)+"/",filename, as_attachment=True)

@app.route(app.config['URL_PREFIX']+'/static/attachments/answers/<int:userid>/<int:orderid>/<path:filename>')
def show_answers_attachments(userid, orderid, filename):
    return send_from_directory(app.config['ANSWER_ATTACHMENTS']+'/'+str(userid)+"/"+str(orderid)+"/",filename, as_attachment=True)


# РЕНДЕР ШАБЛОНОВ

@app.route(app.config['URL_PREFIX']+"/main/", methods = ['GET'])
def show_questions():
    if request.method == 'GET':
        data = {
            'css_path': app.config['URL_PREFIX'] + '/static/main/css/app.css',
            'js_path': app.config['URL_PREFIX'] + '/static/main/js/app.js',
        }
        return render_template('questions.html', data=data)
    else:
       return {'status_info': {'status': 'error','error_mess':'WARN: Incorrect request method'}}

@app.route(app.config['URL_PREFIX']+"/webappauth/")
def webappauth():
    no_params = False

    usertelid = request.args.get('webappauthtelid')

    if not usertelid:
        no_params = True

    is_auth = False

    check_user_tel = UserTelegramInfo.query.filter_by(tlgmid=str(usertelid)).first()

    if check_user_tel is not None:
        is_auth = True

    data = {
        'no_params': no_params,
        'no_params_text': 'Для авторизации не были получены все необходимые парметры. Попробуйте повторить попытку позже',
        'is_auth': is_auth,
        'usertelid': usertelid,
        'title': 'Авторизация',
        'already_auth_text': 'Вы уже прошли процедуру авторизации',
        'webapp_js': app.config['URL_PREFIX']+'/static/js/telegram-web-app.js',
        'app_js': app.config['URL_PREFIX']+'/static/webappauth/js/app.js',
        'app_css': app.config['URL_PREFIX'] + '/static/webappauth/css/app.css',
    }
    return render_template('webappauth.html', data=data)

@app.route(app.config['URL_PREFIX']+"/webappanonymviewer/")
def webapp_anonym_viewer():

    invalid = False

    questionid = request.args.get('webappquestionid')

    if not questionid:
        invalid = True

    else:
        check_order = OrderMess.query.filter_by(id=int(questionid)).first()
        if check_order is not None:
            check_anonym_order = AnonymOrder.query.filter_by(orderid=int(questionid)).first()
            if check_anonym_order is None:
                invalid = True
        else:
            invalid = True

    data = {
        'invalid': invalid,
        'invalid_text': 'Не получена необходимая информация для отображения. Повторите попытку позже',
        'title': 'Просмотр вопроса',
        'webapp_js': app.config['URL_PREFIX']+'/static/js/telegram-web-app.js',
        'app_js': app.config['URL_PREFIX']+'/static/webappanonymviewer/js/app.js',
        'app_css': app.config['URL_PREFIX'] + '/static/webappanonymviewer/css/app.css',
    }
    return render_template('webappanonymviewer.html', data=data)

@app.route(app.config['URL_PREFIX']+"/webapp/")
def webapp_main():

    data = {
        'title': 'Вопросы/Ответы',
        'webapp_js': app.config['URL_PREFIX']+'/static/webapp/js/telegram-web-app.js',
        'app_js': app.config['URL_PREFIX']+'/static/webapp/js/app.js',
        'app_css': app.config['URL_PREFIX'] + '/static/webapp/css/app.css',
    }
    return render_template('webapp.html', data=data)