from io import BytesIO

import pandas as pd
from celery import shared_task
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows

from app.core.settings import get_settings
from app.integrations import TelegramGateway

SETTINGS = get_settings()

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
    telegram = TelegramGateway(token=SETTINGS.tel_token)
    try:
        df = pd.read_sql(follower_sql, SETTINGS.sqlalchemy_database_uri)
        df = df.drop_duplicates(subset=['login'], keep='first')
        df.rename(columns={"login": "ЛОГИН", "fio": "ФИО", "telid": "ID Telegram", "telname": "USERNAME Telegram"},
                  inplace=True)

        wb = Workbook()

        sheet = wb.active

        for item in dataframe_to_rows(df, index=False, header=True):
            sheet.append(item)

        out = BytesIO()
        wb.save(out)
        out.seek(0)
        wb.close()
        telegram.send_document(chat_id=chatid, document=out, filename="followers.xlsx")

    except Exception as e:
        print(str(e))
        telegram.send_message(
            chat_id=chatid,
            text="🚫 <b>При запросе файла произошла ошибка! Попробуйте позже или создайте заявку для решения проблемы.</b>",
        )
