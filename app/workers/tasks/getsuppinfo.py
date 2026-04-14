import os
from io import BytesIO

import pandas as pd
from celery import shared_task
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows

from app.core.settings import get_settings
from app.integrations import TelegramGateway

SETTINGS = get_settings()


def check_parquet():
    response = {'status': False, 'filename': ''}

    files = os.listdir(SETTINGS.supp_parquet_data_dir)

    if len(files) == 1:
        ext = files[0].split('.')[-1]

        if SETTINGS.supp_parquet_file_prefix in files[0] and ext == SETTINGS.supp_parquet_file_ext:
            response['status'] = True
            response['filename'] = files[0]

    return response

@shared_task()
def get_supp_info(chatid):

    # print("get_supp_info function")
    send_error = False

    telegram = TelegramGateway(token=SETTINGS.tel_token)

    try:
        check_resp = check_parquet()

        # print("check_resp :", check_resp)

        if check_resp['status']:

            df = pd.read_parquet(SETTINGS.supp_parquet_data_dir + '/' + check_resp['filename'])

            df.drop(['LOGIN_ID', 'STATUS', 'PHONE'], axis= 1 , inplace= True)

            # print(df.head())

            wb = Workbook()

            sheet = wb.active

            for item in dataframe_to_rows(df, index=False, header=True):
                sheet.append(item)

            out = BytesIO()
            wb.save(out)
            out.seek(0)
            wb.close()
            req = telegram.send_document(chat_id=chatid, document=out, filename="supp.xlsx")

            answer = req.json()

            # print(req.json())

            if 'ok' in answer:
                if not answer['ok']:
                    send_error = True

        else:
            send_error = True

    except Exception as e:
        print(str(e))
        send_error = True

    if send_error:
        telegram.send_message(
            chat_id=chatid,
            text="🚫 <b>При запросе файла произошла ошибка! Попробуйте позже или создайте заявку для решения проблемы.</b>",
        )
