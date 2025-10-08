from questionsapp.models import AccessToken, AppConfig
from questionsapp.services.user.userinfo import set_user_info
import datetime
import pytz
from database import db
local_timezone = pytz.timezone('Europe/Moscow')
# import logging

# logging.basicConfig(filename="checktoken.log",
# 					format='%(asctime)s %(message)s',
# 					filemode='w')
# logger=logging.getLogger()
# logger.setLevel(logging.DEBUG)

def check_user_token(token):
    if token:

        try:
            config_rec = AppConfig.query.first()

            if config_rec is not None:

                check_token_rec = AccessToken.query.filter_by(token=token).first()

                if check_token_rec is not None:

                    created_date = check_token_rec.created_at.astimezone(local_timezone)
                    print("created_date :", created_date)
                    now = datetime.datetime.now(pytz.utc).astimezone(local_timezone)

                    print("now:", now)

                    difference = now - created_date

                    diff_min = abs(difference.total_seconds() / 60)

                    if diff_min > config_rec.token_expire:
                        db.session.delete(check_token_rec)
                        db.session.commit()
                        return {"status": "token_expire"}

                    fulluserinfo = {'token': check_token_rec.token}
                    user_info = set_user_info(check_token_rec.userid)
                    fulluserinfo.update(user_info)

                    return {'status': 'ok', 'info': fulluserinfo}

                else:
                    return {"status": "token_error", "error_mess": "WARN: Token doesn't find"}
            else:
                return {"status": "error", "error_mess": "WARN: No appconfig record"}

        except:
            return {"status": "error", "error_mess": "WARN: Error during checking token"}

    else:
        return {"status": "error", "error_mess": "WARN: No token param"}