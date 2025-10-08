import numpy as np
import pandas as pd
# from pandasgui import show
from flask import current_app as app
from questionsapp.services.auxillary.readsqltmpfile import read_sql_tmpfile
from questionsapp.services.roles.getrole import get_role
from questionsapp.services.status.transformstatuslist import tranform_status_list
from supp_db.queries.questions import sql_questions, sql_questions_service, select_status,select_count
from supp_db.queries.questions import feedback_query, select_space, sql_find_question, public_query
from sqlalchemy import create_engine, text
from questionsapp.models import Attachment, OrderAttachment, AnswerAttachment, UserBaseRole
from questionsapp.models import OrderStatus
from questionsapp.services.user.checkusertoken import check_user_token


def divide_chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]


def find_question_in_list(params):

    list_params = {
        'statusId': 0,
        'spaceId': 0,
        'activePage': 1,
        'countPerPage': 5,
        'sorting': 'desc',
        'searchInput': '',
        'enableSearch': 0,
    }

    if params['userid'] and params['orderid']:
        try:
            userid = params['userid']
            orderid = params['orderid']

            check_status = OrderStatus.query.filter_by(orderid=int(orderid)).first()

            check_role = UserBaseRole.query.filter_by(userid=int(userid)).first()

            status_condition = " where os.statusid=" + str(check_status.statusid) + " "

            role = get_role(check_role.roleid)

            role_condition = ""

            if role == 'personal':
                role_condition = " and ordermess.userid=" + str(userid)

            if role == 'redactor':
                if check_status.statusid == app.config['QUESTION_STATUS']['trash']['id']:
                    role_condition = " and ordermess.userid=" + str(userid)

            result_query = sql_find_question + status_condition + role_condition

            # print("find_question_in_list result_query: ", result_query)

            engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'], pool_pre_ping=True)

            df = read_sql_tmpfile(result_query, engine)

            if not df.empty:

                df['id'] = df['id'].astype('int64')

                quest_id_list = df['id'].values.tolist()

                if int(orderid) in quest_id_list:
                    list_params['statusId'] = check_status.statusid

                    if len(quest_id_list) > 5:
                        list_of_questlist = divide_chunks(quest_id_list, 5)

                        for count, item in enumerate(list_of_questlist, start=1):
                            if int(orderid) in item:
                                list_params['activePage'] = int(count)
        except Exception as e:
            print(str(e))

        return {'status': 'ok', 'info': list_params}

    else:
        return {'status': 'error', 'error_mess': 'WARN: No params'}


def exec_raw_query(engine, query, flag='one'):
    with engine.begin() as con:
        if flag == 'one':
            return con.execute(text(query)).fetchone()
        elif flag == 'all':
            return con.execute(text(query)).fetchall()


def create_status_condition(role, userid, status_list, is_numeric=False):
    prepare_status_list = tranform_status_list(status_list)

    if role == "redactor" and "trash" in status_list:
        if is_numeric:
            status_condition = " and ("
        else:
            status_condition = " and "

        for count, item in enumerate(prepare_status_list, start=1):
            if item == app.config['QUESTION_STATUS']['trash']['id']:
                status_condition = status_condition + " (stord.id=" + str(item) + " and ordermess.userid=" + str(
                    userid) + ")"
            else:
                status_condition = status_condition + " stord.id=" + str(item)

            if count != len(prepare_status_list):
                status_condition = status_condition + " or"

        if is_numeric:
            status_condition = status_condition + ")"

    else:
        status_condition = " and stord.id in ("
        for count, item in enumerate(prepare_status_list, start=1):
            if count != len(prepare_status_list):
                status_condition = status_condition + str(item) + ','
            else:
                status_condition = status_condition + str(item) + ')'

    return status_condition


def check_questions_list_params(params):
    check_params = True

    if not params['userid']:
        check_params = False
    else:
        if int(params['userid']) == 0:
            check_params = False

    if not params['roleid']:
        check_params = False
    else:
        if int(params['roleid']) == 0:
            check_params = False

    if not isinstance(params['spaceid'], int):
        check_params = False

    if not isinstance(params['statusid'], int):
        check_params = False

    if not isinstance(params['perpagecount'], int):
        check_params = False

    if not isinstance(params['activepage'], int):
        check_params = False

    if not isinstance(params['enablesearch'], int):
        check_params = False

    if not isinstance(params['searchinput'], str):
        check_params = False

    if not isinstance(params['usertoken'], str):
        check_params = False

    if not isinstance(params['forsynchroflag'], int):
        check_params = False

    return check_params


def check_search_numeric(params):
    numeric = False
    if int(params['enablesearch']) == 1 and params['searchinput'] != '':
        if params['searchinput'].isnumeric():
            numeric = True
    return numeric


def form_params_conditions(is_numeric_search, role, params):
    ALL_STATUSES = ['create', 'inwork', 'received_answer', 'archive', 'trash', 'back_in_work']


    if (role == 'redactor' or role == 'admin') and int(params['isfeedback']) == 1 and not is_numeric_search and int(params['showonlypublic']) != 1:
        feedback_condition = " where fq.orderid is NOT NULL "
    else:
        feedback_condition = " where fq.orderid is NULL "

    public_condition = ""

    if int(params['showonlypublic']) == 1:
        public_condition = " and ordpublic is not NULL "

    search_condition = ""

    if params['searchinput'].strip() != '':
        if is_numeric_search:
            search_condition = " and ordermess.id=" + params['searchinput']
        else:
            search_condition = " and ordermess.text ilike '%" + params['searchinput'].lower() + "%'"

    # print("search_condition: ", search_condition)

    if int(params['isfeedback']) == 1:
        status_condition = " and stord.id=" + str(app.config['QUESTION_STATUS']['archive']['id'])
    else:
        if int(params['showonlypublic']) == 1:
            PUBLIC_STATUSES = ['received_answer', 'archive', 'back_in_work']
            status_condition = create_status_condition(role, params['userid'], PUBLIC_STATUSES, False)
        else:
            if int(params['statusid']) == 0:
                if is_numeric_search or params['searchinput'].strip() != '':
                    status_condition = create_status_condition(role, params['userid'], ALL_STATUSES, True)
                else:
                    status_condition = create_status_condition(role, params['userid'],
                                                               app.config['DEFAULT_RENDER_STATUSES'])

            else:
                status_condition = " and stord.id=" + str(params['statusid'])

                if role == "redactor" and int(params['statusid']) == app.config['QUESTION_STATUS']['trash']['id']:
                    status_condition = " and (stord.id=" + str(params['statusid']) + " and ordermess.userid=" + str(
                        params['userid']) + ")"

    # print("status_condition: ", status_condition)

    space_condition = ""

    if not is_numeric_search and params['searchinput'].strip() == '':

        if int(params['spaceid']) == 0:
            space_condition = ""
        else:
            space_condition = " and space.id=" + str(params['spaceid'])

    # print("space_condition: ", space_condition)


    if role == "personal":
        role_condition = " and ordermess.userid=" + str(params['userid'])
    else:
        role_condition = ""

    orderby_condition = ""

    if not is_numeric_search:
        if params['datesort'] == 'asc':
            orderby_condition = " order by ordermess.created_at asc, ordermess.text asc "
        elif params['datesort'] == 'desc':
            orderby_condition = " order by ordermess.created_at desc, ordermess.text asc "
        elif params['datesort'] == 'notset':
            orderby_condition = " order by ordermess.text desc "
        else:
            orderby_condition = " order by ordermess.created_at desc, ordermess.text asc "

    return {
        'search_condition': search_condition,
        'status_condition': status_condition,
        'space_condition': space_condition,
        'role_condition': role_condition,
        'orderby_condition': orderby_condition,
        'feedback_condition': feedback_condition,
        'public_condition': public_condition
    }


def form_limit_condition(is_numeric_search, params):
    offset = (int(params['activepage']) - 1) * int(params['perpagecount'])

    limit_sql = ""

    if not is_numeric_search:
        limit_sql = " limit " + str(params['perpagecount'])

        if offset != 0:
            limit_sql = " limit " + str(params['perpagecount']) + " offset " + str(offset)

    return limit_sql


def process_by_pandas(query, engine):
    df = read_sql_tmpfile(query, engine)

    df['order_unionrole_id'] = df['order_unionrole_id'].fillna(app.config['NULLROLE']['id'])
    df['order_unionrole_name'] = df['order_unionrole_name'].fillna(app.config['NULLROLE']['name'])
    df['order_unionrole_emiasid'] = df['order_unionrole_emiasid'].fillna(app.config['NULLROLE']['emiasid'])
    df['answer_id'] = df['answer_id'].fillna(0)
    df = df.replace(np.nan, None)
    # show(df)
    # dtale.show(df)
    df['order_created_at'] = pd.to_datetime(df['order_created_at'], format='mixed')
    df['order_created_at'] = df['order_created_at'].dt.strftime('%d.%m.%Y %H:%M')

    return df.to_dict("records")


def add_default_front_params(item):
    item['order_union_roles'] = []

    item['new_order_upload_files'] = []
    item['deny_order_upload_files'] = []
    item['upload_order_infoarray'] = []
    item['order_simul_files'] = 0

    item['new_answer_upload_files'] = []
    item['deny_answer_upload_files'] = []
    item['upload_answer_infoarray'] = []
    item['answer_simul_files'] = 0

    item['is_update_active'] = 0

    return item


def get_attach_info(item):
    order_attachments = []
    answer_attachments = []

    quest_attachs = OrderAttachment.query.filter_by(orderid=int(item['order_id'])).all()
    if len(quest_attachs) != 0:
        for a_item in quest_attachs:
            attach_rec = Attachment.query.filter_by(id=a_item.attachid).first()
            order_attachments.append({'type': attach_rec.type, 'path': attach_rec.path,
                                      'attachid': attach_rec.id, 'public': attach_rec.public})
    item['order_attachments'] = order_attachments

    if item['answer_id'] != 0:
        answer_attachs = AnswerAttachment.query.filter_by(answerid=int(item['answer_id'])).all()

        if len(answer_attachs) != 0:
            for a_item in answer_attachs:
                attach_rec = Attachment.query.filter_by(id=a_item.attachid).first()
                answer_attachments.append({'type': attach_rec.type, 'path': attach_rec.path,
                                           'attachid': attach_rec.id, 'public': attach_rec.public})

    item['answer_attachments'] = answer_attachments
    return item


def form_questions_list(params):
    if check_questions_list_params(params):

        if int(params['statusid']) == int(app.config['QUESTION_STATUS']['public']['id']):
            params['statusid'] = 0

        userid = params['userid']

        role = get_role(params['roleid'])

        ALL_STATUSES = ['create', 'inwork', 'received_answer', 'archive', 'trash', 'back_in_work']

        is_numeric_search = check_search_numeric(params)

        sql_conditions = form_params_conditions(is_numeric_search, role, params)

        search_condition = sql_conditions['search_condition']
        status_condition = sql_conditions['status_condition']
        space_condition = sql_conditions['space_condition']
        role_condition = sql_conditions['role_condition']
        orderby_condition = sql_conditions['orderby_condition']
        feedback_condition = sql_conditions['feedback_condition']
        public_condition = sql_conditions['public_condition']

        limit_condition = form_limit_condition(is_numeric_search, params)

        result_query = sql_questions + feedback_condition + public_condition + status_condition + space_condition + search_condition + role_condition + orderby_condition + limit_condition

        # print("result query: ", result_query)

        engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'], pool_pre_ping=True)

        count_query = select_count + sql_questions_service + feedback_condition + public_condition + status_condition + space_condition + search_condition + role_condition
        # print("count_query:", count_query)

        count_by_conditions = exec_raw_query(engine, count_query)[0]

        # print("count: ", count_by_conditions)

        feedback_count_query = select_count + feedback_query

        feedback_count = 0

        if role == 'admin' or role == 'redactor':
            feedback_count = exec_raw_query(engine, feedback_count_query)[0]

        # print("count: ", feedback_count_query)

        public_count_query = select_count + public_query+role_condition

        public_count = exec_raw_query(engine, public_count_query)[0]

        query_stat_condition = create_status_condition(role, userid, ALL_STATUSES)

        all_statuses_query = select_status + sql_questions_service + " where fq.orderid is NULL " + query_stat_condition + role_condition

        all_statuses = exec_raw_query(engine, all_statuses_query, 'all')

        available_statuses = []

        for item in all_statuses:
            available_statuses.append({'id': item[0], 'name': item[1]})

        if len(available_statuses) > 0:
            available_statuses = sorted(available_statuses, key=lambda x: x['id'])

        if feedback_count > 0:
            available_statuses.append({'id': app.config['QUESTION_STATUS']['feedback']['id'], 'name': app.config['QUESTION_STATUS']['feedback']['name']})

        if public_count >0:
            available_statuses.append({'id': app.config['QUESTION_STATUS']['public']['id'],
                                       'name': app.config['QUESTION_STATUS']['public']['name']})

        all_spaces_query = """
        select distinct space.id, space.title, space.spacekey
        from infospace space where space.spacekey !='' or space.title !=''
        """

        # all_spaces_query = select_space + sql_questions_service + query_stat_condition + role_condition
        print("all_spaces_query: ", all_spaces_query)

        all_spaces = exec_raw_query(engine, all_spaces_query, 'all')

        available_spaces = []

        is_null_space = False

        for item in all_spaces:
            if app.config['NULLSPACE']['spacekey'] == item[2]:
                is_null_space = True
            available_spaces.append({'id': item[0], 'title': item[1], 'spacekey': item[2]})

        if not is_null_space:
            available_spaces.append({'id': app.config['NULLSPACE']['id'], 'title': app.config['NULLSPACE']['title'],
                                     'spacekey': app.config['NULLSPACE']['spacekey']})

        # print("available_spaces: ", available_spaces)
        if len(available_spaces) > 0:
            available_spaces = sorted(available_spaces, key=lambda x: x['title'])

        available_spaces.insert(0,
                                {
                                    'id': app.config['SHOW_ALL_SPACES_ITEM']['id'],
                                    'title': app.config['SHOW_ALL_SPACES_ITEM']['title'],
                                    'spacekey': app.config['SHOW_ALL_SPACES_ITEM']['spacekey']
                                })

        all_count_query = select_count + sql_questions_service + query_stat_condition + role_condition

        all_count = exec_raw_query(engine, all_count_query, 'one')[0]

        # print("result_query: ", result_query)

        result_list = process_by_pandas(result_query, engine)

        # print(result_list)

        for item in result_list:
            item = add_default_front_params(item)

            item = get_attach_info(item)
        # print(result_list)

        info_object = {'render_list': result_list, 'total_count_by_conditions': count_by_conditions,
                       'total_count': all_count, 'available_statuses': available_statuses,
                       'available_spaces': available_spaces}

        if int(params['forsynchroflag']) == 1:
            check_token = check_user_token(params['usertoken'])
            user_token_status = check_token['status']
            info_object['user_token_status'] = user_token_status

        return {'status': 'ok', 'info': info_object}
    else:
        return {"status": "error", "error_mess": "WARN: No params"}
