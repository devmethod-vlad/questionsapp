import datetime
from questionsapp.models import TelPhrazeStats
import pandas as pd
from pytz import timezone
from openpyxl import Workbook
from io import BytesIO
from flask import send_file
from openpyxl.utils.dataframe import dataframe_to_rows

east = timezone('Europe/Moscow')

def get_phraze_stat(delta, downloadflag):
    try:
        phrazes = TelPhrazeStats.query.all()
        phrazeList = []
        for phrazeItem in phrazes:
            phrazeList.append({"searchphraze": phrazeItem.searchphrase, "created_at": phrazeItem.created_at})
        df = pd.DataFrame(phrazeList)
        if int(downloadflag) != 1:
            df = df[df["created_at"] > datetime.datetime.now(east) - pd.to_timedelta(delta)]
        df["created_at"] = df["created_at"].dt.strftime("%d-%m-%Y")
        df['count'] = df['searchphraze']
        dfGroup = df.groupby(['created_at', 'searchphraze']).agg({'count': 'count'})
        dfGroup = dfGroup.reset_index()
        dfGroup['created_at'] = pd.to_datetime(dfGroup['created_at'], format='%d-%m-%Y')
        dfGroup.sort_values(by="created_at", inplace=True, ascending=True)
        dfGroup["created_at"] = dfGroup["created_at"].dt.strftime("%d-%m-%Y")

        if int(downloadflag) == 1:
            dfGroup = dfGroup.rename(
                columns={"created_at": "ДАТА", "searchphraze": "ПОИСКОВЫЙ ЗАПРОС", "count": "КОЛ-ВО"})
            wb = Workbook()
            ws = wb.active
            for r in dataframe_to_rows(dfGroup, index=False, header=True):
                ws.append(r)
            out = BytesIO()
            wb.save(out)
            out.seek(0)
            wb.close()
            return send_file(out, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                             download_name='phrazesstats.xlsx', as_attachment=True)
        else:
            infodata = dfGroup.to_dict('records')
            return {'status': 'ok', 'info': {'infodata': infodata}}

    except Exception as e:
        print(str(e))
        return {'status': 'error', 'error_mess': str(e)}