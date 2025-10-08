import datetime
from questionsapp.models import UserTelegramInfo
import pandas as pd
from pytz import timezone
from openpyxl import Workbook
from io import BytesIO
from flask import send_file
from openpyxl.utils.dataframe import dataframe_to_rows

east = timezone('Europe/Moscow')

def get_newuser_stat(delta, downloadflag):
    try:
        usersTel = UserTelegramInfo.query.all()
        usersCount = UserTelegramInfo.query.count()
        telList = []
        for telItem in usersTel:
            telList.append({"telid": telItem.tlgmid, "created_at": telItem.created_at})
            # telList.append({"telid":telItem.tlgmid, "created_at":telItem.created_at.strftime("%d-%m-%Y")})
        df = pd.DataFrame(telList)
        if not int(downloadflag) == 1:
            df = df[df["created_at"] > datetime.datetime.now(east) - pd.to_timedelta(delta)]
        df["created_at"] = df["created_at"].dt.strftime("%d-%m-%Y")
        dfGroup = df.groupby(['created_at']).agg({'telid': pd.Series.nunique})
        dfGroup = dfGroup.reset_index()
        dfGroup['created_at'] = pd.to_datetime(dfGroup['created_at'], format='%d-%m-%Y')
        dfGroup.sort_values(by="created_at", inplace=True, ascending=True)
        dfGroup["created_at"] = dfGroup["created_at"].dt.strftime("%d-%m-%Y")
        # print("dfGroup :", dfGroup.head())
        if int(downloadflag) == 1:
            dfGroup = dfGroup.rename(columns={'created_at': 'ДАТА', 'telid': 'КОЛ-ВО НОВЫХ ПОЛЬЗОВАТЕЛЕЙ'})
            wb = Workbook()
            ws = wb.active
            for r in dataframe_to_rows(dfGroup, index=False, header=True):
                ws.append(r)
            out = BytesIO()
            wb.save(out)
            out.seek(0)
            wb.close()
            return send_file(out, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                             download_name='newusers.xlsx', as_attachment=True)
        else:
            dfGroup = dfGroup.rename(columns={"created_at": "x", "telid": "y"})
            infodata = dfGroup.to_dict('records')

            return {'status': 'ok', 'info': {'new_user_data': infodata, 'users_count': str(usersCount)}}

    except Exception as e:
        print(str(e))
        return {'status': 'error', 'error_mess': str(e)}