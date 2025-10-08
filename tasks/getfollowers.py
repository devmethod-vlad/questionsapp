from celery import shared_task
import pandas as pd
import requests
from flask import current_app as app
from openpyxl import Workbook
from io import BytesIO
from openpyxl.utils.dataframe import dataframe_to_rows

follower_sql = """
select useminfo.emiaslogin as login,
       userpg.lastname || ' ' || userpg.firstname || ' ' || userpg.secondname as fio,
       user_telegraminfo.tlgmid as telid, user_telegraminfo.tlgmname as telname
from user_telegraminfo
left join user_emiasinfo useminfo on useminfo.userid = user_telegraminfo.userid
join userpg on user_telegraminfo.userid = userpg.id where emiaslogin is not null
"""

@shared_task()
def get_followers_excel(chatid):
    try:
        df = pd.read_sql(follower_sql, app.config['SQLALCHEMY_DATABASE_URI'])
        df = df.drop_duplicates(subset=['login'], keep='first')
        df.rename(columns={"login": "ЛОГИН", "fio": "ФИО", "telid": "ID Telegram", "telname": "USERNAME Telegram"},
                  inplace=True)

        wb = Workbook()

        sheet = wb.active

        for item in dataframe_to_rows(df, index=False, header=True):
            sheet.append(item)

        out = BytesIO()
        wb.save(out)
        out.name = "followers.xlsx"
        out.seek(0)
        wb.close()
        url = 'https://api.telegram.org/bot' + app.config['TEL_TOKEN'] + '/sendDocument?chat_id={}'.format(chatid)
        requests.post(url, files={"document": out})

    except Exception as e:
        print(str(e))
        method = "sendMessage"
        url = f"https://api.telegram.org/bot{app.config['TEL_TOKEN']}/{method}"
        data = {"chat_id": chatid,
                "text": '🚫 <b>При запросе файла произошла ошибка! Попробуйте позже или создайте заявку для решения проблемы.</b>',
                'parse_mode': 'html'}
        requests.post(url, data=data)

