sql_questions = """
select distinct ordermess.id as order_id, ordermess.userid as order_userid,
    order_user.lastname || ' ' || order_user.firstname || ' ' || order_user.secondname as order_user_fio,
    order_user.mail as order_user_mail, order_user.phone as order_user_phone,
    order_user_tel_info.tlgmid as order_user_tg_id, order_user_tel_info.tlgmname as order_user_tg_name,
    order_user_emias_info.emiaslogin as order_user_emiaslogin, order_user_wiki_info.login as order_user_wikilogin,
    ordermess.text as order_text, ordermess.modified_at as order_modified_at,ordermess.created_at as order_created_at,
    fq.orderid as feedback_id, space.id as space_id, space.spacekey as space_key,space.title as space_title, stord.id as status_id, stord.name as status_name,
    ordpublic.id as public_id,anonord.id as anonym_id, anordinfo.fio as anonymorder_fio,
    anordinfo.speciality as anonymorder_speciality,anordinfo.muname as anonymorder_muname, anordinfo.mail as anonymorder_mail,
    anordinfo.phone as anonymorder_phone,anordinfo.tlgmid as anonymorder_tg_id,answ.id as answer_id,
    answ.userid as answer_userid, answ.text as answer_text, answ.modified_at as answer_modified_at,
    answ.created_at as answer_created_at, oi.orderid as inwork_id,oi.userid as inwork_userid,
    ord_inwork_user.lastname || ' ' || ord_inwork_user.firstname || ' ' || ord_inwork_user.secondname as inwork_user_fio,
    ord_inwork_user.mail as inwork_user_mail, ord_inwork_user.phone as inwork_user_phone,
    oiw_user_eminfo.emiaslogin as inwork_user_emiaslogin, oiw_user_wiki.login as inwork_user_wikilogin,
    oiw_user_telinfo.tlgmid as inwork_user_tg_id, oiw_user_telinfo.tlgmname as inwork_user_tg_name,
    answer_user.lastname || ' ' || answer_user.firstname || ' ' || answer_user.secondname as answer_user_fio,
    answer_user.phone as answer_user_phone, answer_user.mail as answer_user_mail,
    answ_user_tel_info.tlgmid as answer_user_tg_id, answ_user_tel_info.tlgmname as answer_user_tg_name,
    answ_user_emias_info.emiaslogin as answer_user_emiaslogin,
    answ_user_wiki_info.login as answer_user_wikilogin, unr.id as order_unionrole_id, unr.name as order_unionrole_name,
    unr.emiasid as order_unionrole_emiasid
from ordermess
left join userpg order_user on ordermess.userid = order_user.id
left join user_telegraminfo order_user_tel_info on order_user.id=order_user_tel_info.userid
left join user_emiasinfo order_user_emias_info on order_user.id=order_user_emias_info.userid
left join user_wikiinfo order_user_wiki_info on order_user.id=order_user_wiki_info.userid
left join feedback_question fq on ordermess.id = fq.orderid
left join order_infospace orinfo on ordermess.id = orinfo.orderid
left join infospace space on orinfo.spaceid = space.id
left join order_status ors on ordermess.id = ors.orderid
left join statusorder stord on ors.statusid = stord.id
left join order_public ordpublic on ordermess.id = ordpublic.orderid
left join anonymorder anonord on ordermess.id = anonord.orderid
left join anonymorderinfo anordinfo on ordermess.id = anordinfo.orderid
left join answermess answ on ordermess.id = answ.orderid
left join userpg answer_user on answ.userid = answer_user.id
left join user_telegraminfo answ_user_tel_info on answer_user.id=answ_user_tel_info.userid
left join user_emiasinfo answ_user_emias_info on answer_user.id=answ_user_emias_info.userid
left join user_wikiinfo answ_user_wiki_info on answer_user.id=answ_user_wiki_info.userid
left join orders_inwork oi on ordermess.id = oi.orderid
left join userpg ord_inwork_user on ord_inwork_user.id = oi.userid
left join user_emiasinfo oiw_user_eminfo on oiw_user_eminfo.userid = ord_inwork_user.id
left join user_wikiinfo oiw_user_wiki on oiw_user_wiki.userid=ord_inwork_user.id
left join user_telegraminfo oiw_user_telinfo on oiw_user_telinfo.userid =ord_inwork_user.id
left join order_unionrole our on our.orderid = ordermess.id
left join unionrole unr on unr.id=our.unionroleid
"""

select_count = """
select count(distinct ordermess.id) 
"""

select_status = """
select distinct stord.id, stord.name 
"""

select_space = """
select distinct space.id, space.title, space.spacekey 
"""

feedback_query = """
 from ordermess
left join feedback_question fq on ordermess.id = fq.orderid 
where fq.orderid is not null
"""

public_query = """
 from ordermess
left join order_public ordpublic on ordermess.id = ordpublic.orderid
where ordpublic is not null 
"""

sql_questions_service = """ 
from ordermess
left join feedback_question fq on ordermess.id = fq.orderid
left join order_infospace orinfo on ordermess.id = orinfo.orderid
left join infospace space on orinfo.spaceid = space.id
left join order_status ors on ordermess.id = ors.orderid
left join statusorder stord on ors.statusid = stord.id
left join order_public ordpublic on ordermess.id = ordpublic.orderid
left join anonymorder anonord on ordermess.id = anonord.orderid
left join answermess answ on ordermess.id = answ.orderid
left join orders_inwork oi on ordermess.id = oi.orderid
"""

sql_find_question = """select ordermess.id, row_number() over (order by ordermess.created_at desc, ordermess.text)
from ordermess
join order_status os on ordermess.id = os.orderid """