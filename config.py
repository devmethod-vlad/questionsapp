import os

path = os.getcwd()

PG_USER = os.getenv('POSTGRES_USER')
PG_PASS = os.getenv('POSTGRES_PASSWORD')
PG_CONTAINER = os.getenv('PG_CONTAINER')
PG_PORT= str(os.getenv('PG_PORT'))
PG_BASE = os.getenv('PG_BASE')

class Config:
    """Base config."""

    MAX_CONTENT_LENGTH = 8 * 1000 * 1000
    TEL_TOKEN = os.getenv('TEL_TOKEN')
    TEL_INFO_CHAT = os.getenv('TEL_INFO_CHAT')

    SUPP_DB_HOST = os.getenv('SUPP_DB_HOST')
    SUPP_DB_PORT = os.getenv('SUPP_DB_PORT')
    SUPP_DB_SID = os.getenv('SUPP_DB_SID')
    SUPP_DB_USERNAME = os.getenv('SUPP_DB_USERNAME')
    SUPP_DB_PASS = os.getenv('SUPP_DB_PASS')

    SUPP_PARQUET_DATA_DIR = '/usr/src/data/suppinfo'

    SUPP_PARQUET_FILE_PREFIX = 'supp'

    SUPP_PARQUET_FILE_EXT = 'gzip'

    SUPP_ZIP_DATA_DIR = '/usr/src/data/suppinfo_zip'

    SQLALCHEMY_DATABASE_URI = 'postgresql://'+PG_USER+':'+PG_PASS+'@'+PG_CONTAINER+':'+PG_PORT+'/'+PG_BASE

    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    CONFLUENCE_URL = os.getenv('CONFLUENCE_BASE_URL')
    CONFL_BOT_NAME = os.getenv('CONFLUENCE_BOT_NAME')
    CONFL_BOT_PASS = os.getenv('CONFL_BOT_PASS')

    CONFLUENCE_SPACEINFO_PAGE = os.getenv('CONFLUENCE_SPACEINFO_PAGE')

    CONFLUENCE_PUBLIC_TESTPAGE_ID = os.getenv('CONFLUENCE_PUBLIC_TESTPAGE_ID')

    TEST_DATA_PATH = '/usr/src/data/'

    JS_FOLDER = os.path.join(path, 'static/js/')
    CSS_FOLDER = os.path.join(path, 'static/css/')
    IMGS_SRC = os.path.join(path, 'static/imgs/')
    FONTS_FOLDER = os.path.join(path, 'static/fonts/')

    MAIN_JS_FOLDER = os.path.join(path, 'static/main/js/')
    MAIN_CSS_FOLDER = os.path.join(path, 'static/main/css/')
    MAIN_IMGS_FOLDER = os.path.join(path, 'static/main/imgs/')

    WEBAPPAUTH_JS_FOLDER = os.path.join(path, 'static/webappauth/js/')
    WEBAPPAUTH_CSS_FOLDER = os.path.join(path, 'static/webappauth/css/')
    WEBAPPAUTH_IMGS_FOLDER = os.path.join(path, 'static/webappauth/imgs/')

    WEBAPPMAIN_JS_FOLDER = os.path.join(path, 'static/webappmain/js/')
    WEBAPPMAIN_CSS_FOLDER = os.path.join(path, 'static/webappmain/css/')
    WEBAPPMAIN_IMGS_FOLDER = os.path.join(path, 'static/webappmain/imgs/')

    WAPPANONYMVIEWER_JS_FOLDER = os.path.join(path, 'static/webappanonymviewer/js/')
    WAPPANONYMVIEWER_CSS_FOLDER = os.path.join(path, 'static/webappanonymviewer/css/')
    WAPPANONYMVIEWER_IMGS_FOLDER = os.path.join(path, 'static/webappanonymviewer/imgs/')

    QUESTION_ATTACHMENTS = os.getenv('QUESTIONS_ATTACHMENTS')+'/orders/'
    ANSWER_ATTACHMENTS = os.getenv('QUESTIONS_ATTACHMENTS')+'/answers/'

    TEL_SENDMESS_URL = f'https://api.telegram.org/bot{TEL_TOKEN}/sendMessage'

    QUESTIONS_MAIN_PAGE=os.getenv('QUESTIONS_MAIN_PAGE')


    URL_PREFIX = os.getenv('QUESTIONSAPP_URL_PREFIX')

    BASE_ROLE = {
        'admin': {
            'id': 1,
            'name': 'Администратор'
        },

        'redactor': {
            'id': 3,
            'name': 'Сотрудник ЕМИАС'
        },

        'personal': {
            'id': 2,
            'name': 'Сотрудник МУ'
        }
    }

    QUESTION_STATUS = {
        'create': {
            'id': 1,
            'name': 'Создано'
        },

        'inwork': {
            'id': 2,
            'name': 'Взято в работу'
        },

        'received_answer': {
            'id': 3,
            'name': 'Получило ответ'
        },

        'archive': {
            'id': 4,
            'name': 'Получило ответ'
        },

        'trash': {
            'id': 5,
            'name': 'В корзине'
        },

        'back_in_work': {
            'id': 7,
            'name': 'Возвращено в работу'
        },

        'feedback' :{
            'id': 100,
            'name': 'Пожелания'
        },

        'public' : {
            'id': 101,
            'name': 'Опубликовано'
        }
    }

    DEFAULT_RENDER_STATUSES = ['create', 'inwork', 'received_answer', 'back_in_work']

    NULLSPACE = {
        'id': 26,
        'title': 'Не распределено',
        'spacekey': 'nullspacekey'
    }

    NULLROLE = {
        'id': 159,
        'name': 'Другое',
        'emiasid': 0
    }

    SHOW_ALL_SPACES_ITEM = {
        'id': 0,
        'title': 'Показать все темы',
        'spacekey': ''
    }
    EXT_DICT = {
        'imageExtension': ['png', 'jpeg', 'jpg'],
        'animExtension': ['gif'],
        'wordExtension': ['doc', 'docx', 'odf'],
        'textDocExtension': ['rtf', 'txt'],
        'excelExtension': ['xlsx', 'xlsm', 'xlsb', 'xltx', 'xltm', 'xls'],
        'videoExtension': ['wmv', 'mp4', 'mov', 'avi', 'flw', 'swf', 'mkv', 'webm', 'mpeg2'],
        'audioExtension': ['flac', 'mp3', 'wav', 'wma', 'aac'],
        'webExtensions': ['json'],
        'pdfExtensions': ['pdf']
    }

    DEFAULT_FORMAT = os.getenv('DEFAULT_FORMAT')
    

class ProdConfig(Config):
    FLASK_ENV = 'production'
    TEL_SEND_NEWMESS = True
    TEL_SEND_ANSWERMESS = True
    TEL_SEND_UPDTMESS = True
    TEL_SEND_MESSCLOSEXECTIME = True
    TEL_SEND_MESSINWORK = True
    TEL_SEND_MESSUSERCLOSED = True
    TEL_SEND_TOHELPMESS = True
    TEL_NOTIFY_FEEDBACK = True
    TEL_INFO_LIST = [298333313, 313953337, 402905678]
    TEL_FEEDBACK_USERLIST = [298333313]
    NOTIFY_SELF_ORDER = False
    WEB_APP_ORDERSHOWER = 'https://edu.emias.ru//edu-rest-api/questions/webappanonymviewer/'


class DevConfig(Config):
    FLASK_ENV = 'development'
    TEL_SEND_NEWMESS = True
    TEL_SEND_ANSWERMESS = True
    TEL_SEND_UPDTMESS = True
    TEL_SEND_MESSCLOSEXECTIME = True
    TEL_SEND_MESSINWORK = True
    TEL_SEND_MESSUSERCLOSED = True
    TEL_SEND_TOHELPMESS = True
    TEL_NOTIFY_FEEDBACK = True
    TEL_INFO_LIST = [298333313]
    TEL_FEEDBACK_USERLIST = [298333313]
    NOTIFY_SELF_ORDER = True
    WEB_APP_ORDERSHOWER = 'http://127.0.0.1:5000/eduportal/questions/webappanonymviewer/'