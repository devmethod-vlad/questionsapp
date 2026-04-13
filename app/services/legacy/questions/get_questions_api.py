# questionsapp/services/questions/get_questions_api.py

from flask import current_app
from sqlalchemy import text
from database import db


def get_questions_api_data(page: int = 1, page_count: int = 100, public_only: bool = True):
    """
    Возвращает (data: list[dict], total_count: int) для API вопросов/ответов.
    - page_count: по умолчанию 100, максимум 500
    - page: минимум 1
    - public_only: если True, добавляем условие публикации (order_public.orderid IS NOT NULL)
    """
    # Нормализация и границы
    try:
        page_count = int(page_count)
    except Exception:
        page_count = 100
    page_count = max(1, min(page_count, 500))

    try:
        page = int(page)
    except Exception:
        page = 1
    page = max(1, page)

    attach_orders_base = "https://edu.emias.ru" + current_app.config.get("URL_PREFIX","") + "/static/attachments/orders"
    attach_answers_base = "https://edu.emias.ru" + current_app.config.get("URL_PREFIX","") + "/static/attachments/answers"

    # Условие публикации добавляем ТОЛЬКО при public_only=True
    public_clause = "AND order_public.orderid IS NOT NULL" if public_only else ""

    # БАЗОВАЯ часть SQL: всегда статусы (3,4,6), присутствие ответа, плюс левый join на order_public
    base_sql = f"""
        FROM ordermess ord
        JOIN order_status ON ord.id = order_status.orderid
        JOIN statusorder ON statusorder.id = order_status.statusid
        LEFT JOIN order_infospace ON order_infospace.orderid = ord.id
        LEFT JOIN infospace ON infospace.id = order_infospace.spaceid
        LEFT JOIN order_unionrole ON order_unionrole.orderid = ord.id
        LEFT JOIN unionrole ON unionrole.id = order_unionrole.unionroleid
        LEFT JOIN order_public ON order_public.orderid = ord.id
        LEFT JOIN order_attachment ord_att ON ord_att.orderid = ord.id
        LEFT JOIN attachment order_attach ON order_attach.id = ord_att.attachid
        JOIN answermess answ ON answ.orderid = ord.id
        LEFT JOIN answer_attachment answ_att ON answ_att.answerid = answ.id
        LEFT JOIN attachment answer_attach ON answer_attach.id = answ_att.attachid
        WHERE answ.id IS NOT NULL 
          AND statusorder.id IN (4)
          {public_clause}
    """

    # Алиасы без кавычек -> ключи в результате в нижнем регистре (id, space, role, role_id, question, question_attach, answer, answer_attach)
    data_query_sql = f"""
        SELECT
            ord.id AS id,
            infospace.title AS space,
            unionrole.name AS role,
            unionrole.emiasid AS role_id,
            case when order_public.id is not null then true else false end as public,
            ord.text AS question,

            array_agg(
                DISTINCT CAST(:attach_orders_base AS text) || '/' || COALESCE(ord.userid::text, '') || '/'
                        || COALESCE(ord.id::text, '') || '/' || COALESCE(order_attach.path, '')
            ) FILTER (WHERE order_attach.path IS NOT NULL AND order_attach.public = 1) AS question_attach,

            answ.text AS answer,

            array_agg(
                DISTINCT CAST(:attach_answers_base AS text) || '/' || COALESCE(ord.userid::text, '') || '/'
                        || COALESCE(ord.id::text, '') || '/' || COALESCE(answer_attach.path, '')
            ) FILTER (WHERE answer_attach.path IS NOT NULL AND answer_attach.public = 1) AS answer_attach,
            to_char(
                ( GREATEST(
                    COALESCE(MAX(ord.modified_at),  'epoch'::timestamptz),
                    COALESCE(MAX(answ.modified_at), 'epoch'::timestamptz)
                 )
                AT TIME ZONE 'Europe/Moscow'         -- получить локальное московское время как timestamp without time zone
                   ),
                    'YYYY-MM-DD"T"HH24:MI:SS.MS'     -- ISO-8601 без зоны
            ) || '+03:00'                            -- добавить постоянный смещённый оффсет
            AS modified_at 

        {base_sql}
        GROUP BY ord.id, ord.modified_at,infospace.title, unionrole.name, unionrole.emiasid, ord.text, answ.text, answ.modified_at, order_public.id
        ORDER BY ord.id
        LIMIT :limit OFFSET :offset
    """

    count_query_sql = f"SELECT COUNT(DISTINCT ord.id) {base_sql}"

    params = {
        "limit": page_count,
        "offset": (page - 1) * page_count,
        "attach_orders_base": attach_orders_base,
        "attach_answers_base": attach_answers_base,
    }

    try:
        result = db.session.execute(text(data_query_sql), params)
        rows = result.fetchall()
        total_count = db.session.execute(text(count_query_sql)).scalar()
    except Exception as e:
        current_app.logger.error(f"Error fetching questions data: {e}")
        raise

    colnames = list(result.keys())  # -> ['id','space','role','role_id','question','question_attach','answer','answer_attach']
    data = []
    for row in rows:
        rec = dict(zip(colnames, row))
        # На всякий случай: нормализуем массивы (None -> [], выкинуть пустые элементы)
        for k in ("question_attach", "answer_attach"):
            arr = rec.get(k)
            if not arr:
                rec[k] = []
            else:
                rec[k] = [x for x in arr if x]
        data.append(rec)

    return data, int(total_count or 0)
