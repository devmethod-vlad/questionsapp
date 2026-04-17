import os
import re

import markdown
from celery import shared_task
from pytz import timezone

from app.core.settings import get_settings
from app.integrations import ConfluenceGateway
from app.services.workers.public_order_data import (
    delete_order_public,
    get_order_space,
    get_order_with_answer,
    get_other_union_role,
    get_space_by_id,
    get_union_role_name,
    list_public_answer_attachment_paths,
    list_public_order_attachment_paths,
    list_space_public_order_ids_with_answer_date,
    set_public_active,
)

SETTINGS = get_settings()


east = timezone('Europe/Moscow')
HTML_TAG_RE = re.compile(r'<.*?>')
CONTENT_TYPES = {
    '.pdf': 'application/pdf',
    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    '.xls': 'application/vnd.ms-excel',
    '.doc': 'application/msword',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
}
QUESTION_TITLE = 'Вопросы и ответы'
TABLE_BODY_START = """<p>Если у вас есть вопрос, нажмите кнопку <strong>Задать вопрос</strong> в верхнем баннере и заполните открывшуюся форму. Ответ будет опубликован в таблице ниже.</p>
<p>Вводите ключевые слова в поле поиска над таблицей. В ней будут отображаться строки, содержащие совпадения.</p>
<ac:structured-macro ac:macro-id="176c857e-c3b2-418a-b434-365310f8f68d" ac:name="hidden-fragment" ac:schema-version="1">
  <ac:rich-text-body>
    <p class="auto-cursor-target">
      <br/>
    </p>
    <ac:structured-macro ac:macro-id="6086ebf4-bd27-47de-b45a-929c9cdff820" ac:name="html" ac:schema-version="1">
      <ac:parameter ac:name="atlassian-macro-output-type">INLINE</ac:parameter>
      <ac:plain-text-body><![CDATA[<input type="text" id="em-search" placeholder="Введите ключевое слово">]]></ac:plain-text-body>
    </ac:structured-macro>
    <p class="auto-cursor-target">
      <br/>
    </p>
  </ac:rich-text-body>
</ac:structured-macro>
<p class="auto-cursor-target">
  <br/>
</p>
<ac:structured-macro ac:macro-id="26ef5691-1f4b-4b00-91ab-d43fc5f3b9c0" ac:name="table-filter" ac:schema-version="1">
  <ac:parameter ac:name="totalrow">,,,,</ac:parameter>
  <ac:parameter ac:name="hidelabels">false</ac:parameter>
  <ac:parameter ac:name="sparkName">Sparkline</ac:parameter>
  <ac:parameter ac:name="hidePane">Filtration panel</ac:parameter>
  <ac:parameter ac:name="sparkline">false</ac:parameter>
  <ac:parameter ac:name="default">,</ac:parameter>
  <ac:parameter ac:name="isFirstTimeEnter">true</ac:parameter>
  <ac:parameter ac:name="cell-width">250,250</ac:parameter>
  <ac:parameter ac:name="hideColumns">false</ac:parameter>
  <ac:parameter ac:name="customNoTableMsg">false</ac:parameter>
  <ac:parameter ac:name="disabled">false</ac:parameter>
  <ac:parameter ac:name="enabledInEditor">false</ac:parameter>
  <ac:parameter ac:name="globalFilter">true</ac:parameter>
  <ac:parameter ac:name="id">1749472619348_-128530837</ac:parameter>
  <ac:parameter ac:name="order">0,1</ac:parameter>
  <ac:parameter ac:name="hideControls">true</ac:parameter>
  <ac:parameter ac:name="inverse">false,false</ac:parameter>
  <ac:parameter ac:name="column">По роли или должности</ac:parameter>
  <ac:parameter ac:name="disableSave">true</ac:parameter>
  <ac:parameter ac:name="separator">Point (.)</ac:parameter>
  <ac:parameter ac:name="labels">Роль или должность‚Ключевые слова</ac:parameter>
  <ac:parameter ac:name="ddOperator">OR</ac:parameter>
  <ac:parameter ac:name="datepattern">dd.mm.yy</ac:parameter>
  <ac:parameter ac:name="updateSelectOptions">false</ac:parameter>
  <ac:parameter ac:name="worklog">365|5|8|y w d h m|y w d h m</ac:parameter>
  <ac:parameter ac:name="isOR">AND</ac:parameter>
  <ac:rich-text-body>
    <p class="auto-cursor-target">
      <br/>
    </p>"""
TABLE_BODY_END = """
                            </tbody>
                        </table>
                        <p class="auto-cursor-target">
                            <br/>
                        </p>
                       </ac:rich-text-body>
</ac:structured-macro>
<p class="auto-cursor-target">
  <br/>
</p>
                        """


def setContenType(extension):
    return CONTENT_TYPES.get(extension, 'attachment')


def _set_public_active(value):
    set_public_active(value)


def _create_confluence_client():
    gateway = ConfluenceGateway(
        base_url=SETTINGS.confluence_url,
        bearer_token=SETTINGS.iac_bot_token,
    )
    return gateway.create_client()


def _strip_html(value):
    return re.sub(HTML_TAG_RE, '', value)


def _build_attachment_url(base_url, user_id, order_id, path):
    return f'{base_url}{user_id}/{order_id}/{path}'


def _get_order_attachments(order_id, user_id):
    return [
        _build_attachment_url(SETTINGS.question_attachments_dir, user_id, order_id, path)
        for path in list_public_order_attachment_paths(order_id)
    ]


def _get_answer_attachments(answer_id, order_id, user_id):
    return [
        _build_attachment_url(SETTINGS.answer_attachments_dir, user_id, order_id, path)
        for path in list_public_answer_attachment_paths(answer_id)
    ]


def _get_union_role_name(order_id, other_role_id):
    return get_union_role_name(order_id, other_role_id)


def _build_table_header(role_out_flag):
    body = TABLE_BODY_START + """
                                    <table class="wrapped tf-macro tablesorter" data-tf-ready="true">
                                        <colgroup>
                                            <col style="width: 29.0px;"/>
                                            <col/>"""
    if role_out_flag:
        body += """<col/>"""

    body += """
                                            <col/>
                                            <col/>
                                            <col/>
                                        </colgroup>
                                        <tbody>
                                            <tr class="tablesorter-header">
                                                <th>
                                                    <br/>
                                                </th>
                                                <th style="vertical-align: middle;text-align: center;">Отметка времени</th>"""
    if role_out_flag:
        body += """<th style="vertical-align: middle;text-align: center;">По роли или должности</th>"""

    body += """
                                                <th style="vertical-align: middle;text-align: center;">Вопрос</th>
                                                <th style="vertical-align: middle;text-align: center;">№ в базе знаний</th>
                                                <th style="vertical-align: middle;text-align: center;">Ответ</th>
                                            </tr>
                            """
    return body


def _get_public_page(confluence, space):
    if SETTINGS.prod:
        return confluence.get_page_by_title(space, QUESTION_TITLE, 0, 1, expand='body.storage.value')
    return confluence.get_page_by_id(SETTINGS.confluence_public_testpage_id, expand='body.storage.value')


def _delete_page_attachments(confluence, page_id):
    for start in range(0, 1000, 50):
        response = confluence.get_attachments_from_content(
            page_id,
            start=start,
            limit=50,
            expand=None,
            filename=None,
            media_type=None,
        )
        for attachment in response.get('results', []):
            confluence.delete_attachment(page_id, attachment['title'], version=None)


def _attach_files_and_render_links(confluence, page_id, files, prefix, row_number, question_title, space):
    body = ''
    for attachment_number, filename in enumerate(files, start=1):
        _, extension = os.path.splitext(filename)
        new_file_name = f'{prefix}-{row_number}-{attachment_number}{extension}'
        body += f"""
                                <p>
                                    <ac:link>
                                        <ri:attachment ri:filename='{new_file_name}'/>
                                    </ac:link>
                                </p>"""
        content_type = setContenType(extension)
        confluence.attach_file(
            filename,
            name=new_file_name,
            content_type=content_type,
            page_id=page_id,
            title=question_title,
            space=space,
        )
    return body


def _build_content_dict(space_orders_list, other_role_id):
    content_dict = {}

    for item in space_orders_list:
        order_id = int(item['id'])
        order, answer = get_order_with_answer(order_id)
        public_order = item.get('is_public', True)
        if not public_order:
            continue
        if order is None or answer is None:
            continue
        order_time = order.created_at.astimezone(east)
        answer_time = answer.modified_at.astimezone(east)

        local_dict = {
            'order': {
                'text': _strip_html(order.text),
                'orderid': str(order.id),
                'userid': order.userid,
                'created_at': order_time,
                'attachments': _get_order_attachments(order_id, order.userid),
                'unionrole': _get_union_role_name(order_id, other_role_id),
            },
            'answer': {
                'text': _strip_html(answer.text),
                'userid': answer.userid,
                'created_at': answer.created_at,
                'modified_at': answer_time.strftime('%d.%m.%Y'),
                'attachments': _get_answer_attachments(answer.id, order_id, answer.userid),
            },
        }
        content_dict[item['id']] = local_dict

    return content_dict


@shared_task()
def publicOrder(orderid):
    _set_public_active(1)

    try:
        confluence = _create_confluence_client()
        order_space = get_order_space(int(orderid))
        other_union_role = get_other_union_role()
        space_orders_list, role_out_flag = list_space_public_order_ids_with_answer_date(
            order_space.spaceid, other_union_role.id
        )
        space_record = get_space_by_id(order_space.spaceid)
        space = space_record.spacekey
        content_dict = _build_content_dict(space_orders_list, other_union_role.id)

        body = _build_table_header(role_out_flag)
        page = _get_public_page(confluence, space)
        _delete_page_attachments(confluence, page['id'])

        for row_number, key in enumerate(content_dict, start=1):
            body += f"""
                                   <tr><td style="vertical-align: middle;text-align: left;"><span>{row_number}</span></td>
                                   <td style="vertical-align: middle;text-align: left; min-width: 100px;"><div class="content-wrapper"><p>{content_dict[key]['answer']['modified_at']}</p>
                                   <ac:structured-macro ac:macro-id="29f83253-7ddd-44ec-b91e-2291e36fb998" ac:name="html" ac:schema-version="1">
                                   <ac:plain-text-body><![CDATA[<span id='anchor-{space_record.spacekey}-{content_dict[key]['order']['orderid']}'></span>]]></ac:plain-text-body>
                                  </ac:structured-macro></div></td>"""

            if role_out_flag:
                body += f"""
                                <td style="vertical-align: middle;text-align: left; min-width: 100px;"><p>{content_dict[key]['order']['unionrole']}</p></td>
                                """

            body += f"""
                                <td style="vertical-align: middle;text-align: left;"><div class="content-wrapper"><p>{content_dict[key]['order']['text']}</p>"""
            body += _attach_files_and_render_links(
                confluence=confluence,
                page_id=page['id'],
                files=content_dict[key]['order']['attachments'],
                prefix='Приложение-к-вопросу',
                row_number=row_number,
                question_title=QUESTION_TITLE,
                space=space,
            )
            body += f"""</div></td><td style="vertical-align: middle;"><div><p style="text-align: center;">{content_dict[key]['order']['orderid']}</p></div></td>
                                <td style="vertical-align: middle;text-align: left;"><div class="content-wrapper"><p>{markdown.markdown(content_dict[key]['answer']['text'])}</p></div>"""
            body += _attach_files_and_render_links(
                confluence=confluence,
                page_id=page['id'],
                files=content_dict[key]['answer']['attachments'],
                prefix='Приложение-к-ответу',
                row_number=row_number,
                question_title=QUESTION_TITLE,
                space=space,
            )
            body += """</td></tr>"""

        body += TABLE_BODY_END
        confluence.update_page(
            page['id'],
            QUESTION_TITLE,
            body,
            type='page',
            representation='storage',
            minor_edit=False,
        )
        _set_public_active(0)
    except Exception as e:
        print(str(e))
        print('ERROR during public question' + str(orderid))
        _set_public_active(0)
        delete_order_public(int(orderid))
