from celery import shared_task
import pandas as pd
import requests
from flask import current_app as app
from openpyxl import Workbook
from io import BytesIO
from openpyxl.utils.dataframe import dataframe_to_rows
import os

def check_parquet():
    response = {'status': False, 'filename': ''}

    files = os.listdir(app.config['SUPP_PARQUET_DATA_DIR'])

    if len(files) == 1:
        ext = files[0].split('.')[-1]

        if app.config['SUPP_PARQUET_FILE_PREFIX'] in files[0] and ext == app.config['SUPP_PARQUET_FILE_EXT']:
            response['status'] = True
            response['filename'] = files[0]

    return response

@shared_task()
def get_supp_info(chatid):

    # print("get_supp_info function")
    send_error = False

    try:
        check_resp = check_parquet()

        # print("check_resp :", check_resp)

        if check_resp['status']:

            df = pd.read_parquet(app.config['SUPP_PARQUET_DATA_DIR']+'/'+check_resp['filename'])

            df.drop(['LOGIN_ID', 'STATUS', 'PHONE'], axis= 1 , inplace= True)

            # print(df.head())

            wb = Workbook()

            sheet = wb.active

            for item in dataframe_to_rows(df, index=False, header=True):
                sheet.append(item)

            out = BytesIO()
            wb.save(out)
            out.name = "supp.xlsx"
            out.seek(0)
            wb.close()
            url = 'https://api.telegram.org/bot' + app.config['TEL_TOKEN'] + '/sendDocument?chat_id={}'.format(chatid)
            req = requests.post(url, files={"document": out})

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

        method = "sendMessage"
        url = f"https://api.telegram.org/bot{app.config['TEL_TOKEN']}/{method}"
        data = {"chat_id": chatid,
                "text": '🚫 <b>При запросе файла произошла ошибка! Попробуйте позже или создайте заявку для решения проблемы.</b>',
                'parse_mode': 'html'}
        requests.post(url, data=data)