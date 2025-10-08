import os
from celery import shared_task
import markdown
from sqlalchemy import desc, and_
from questionsapp.models import AppConfig, OrderSpace, OrderMess, AnswerMess, OrderAttachment, Attachment, AnswerAttachment, OrderStatus, Spaces, OrderPublic, OrderUnionRole, UnionRole
from atlassian import Confluence
from pytz import timezone
from flask import current_app as app
import re
from database import db

east = timezone('Europe/Moscow')

def setContenType(extension):
    content_type = 'attachment'
    if extension == '.pdf':
        content_type = 'application/pdf'
    if extension == '.xlsx':
        content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    if extension == '.xls':
        content_type = 'application/vnd.ms-excel'
    if extension == '.doc':
        content_type = 'application/msword'
    if extension == '.docx':
        content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    return content_type

@shared_task()
def publicOrder(orderid):
    appConfRecStart = AppConfig.query.order_by(desc('created_at')).limit(1).first()
    appConfRecStart.ispublicactive = 1
    db.session.commit()

    try:
        confluence = Confluence(url=app.config['CONFLUENCE_URL'], username=app.config['CONFL_BOT_NAME'],
                                password=app.config['CONFL_BOT_PASS'])
        orderSpace = OrderSpace.query.filter_by(orderid=int(orderid)).first()

        spaceOrdersList = []
        allSpaceOrders = OrderSpace.query.filter(OrderSpace.spaceid == orderSpace.spaceid).all()
        checkOtherUnionRole = UnionRole.query.filter(
            and_((UnionRole.name == 'Другое'), (UnionRole.emiasid == 0))).first()

        roleOutFlag = False
        for soItem in allSpaceOrders:
            publicOrder = OrderPublic.query.filter_by(orderid=soItem.orderid).first()
            orderStatus = OrderStatus.query.filter_by(orderid=soItem.orderid).first()
            orderUnionRole = OrderUnionRole.query.filter_by(orderid=soItem.orderid).first()
            if orderUnionRole is not None and publicOrder is not None:
                if not orderUnionRole.unionroleid == checkOtherUnionRole.id:
                    roleOutFlag = True
            if not orderStatus.statusid in [1, 2, 5] and publicOrder:
                answer = AnswerMess.query.filter_by(orderid=int(soItem.orderid)).first()
                spaceOrdersList.append({"id": soItem.orderid, "answer_date": answer.modified_at})

        spaceOrdersList.sort(key=lambda x: x['answer_date'], reverse=True)

        spaceRec = Spaces.query.filter_by(id=orderSpace.spaceid).first()
        space = spaceRec.spacekey

        contentDict = {}

        body = """<p>Если у вас есть вопрос, нажмите кнопку <strong>Задать вопрос</strong> в верхнем баннере и заполните открывшуюся форму. Ответ будет опубликован в таблице ниже.</p>
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

        body = body + """
                                    <table class="wrapped tf-macro tablesorter" data-tf-ready="true">
                                        <colgroup>
                                            <col style="width: 29.0px;"/>
                                            <col/>"""
        if roleOutFlag:
            body = body + """<col/>"""

        body = body + """
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
        if roleOutFlag:
            body = body + """<th style="vertical-align: middle;text-align: center;">По роли или должности</th>"""
        body = body + """
                                                <th style="vertical-align: middle;text-align: center;">Вопрос</th>
                                                <th style="vertical-align: middle;text-align: center;">№ в базе знаний</th>
                                                <th style="vertical-align: middle;text-align: center;">Ответ</th>
                                            </tr>
                            """

        for item in spaceOrdersList:
            order = OrderMess.query.filter_by(id=int(item['id'])).first()
            checkPublicOrder = OrderPublic.query.filter_by(orderid=int(item['id'])).first()
            if checkPublicOrder:
                localDict = {}
                orderDict = {}
                cleanorder = re.compile('<.*?>')
                orderDict['text'] = re.sub(cleanorder, '', order.text)
                # orderDict['text'] = order.text
                orderDict['orderid'] = str(order.id)
                orderDict['userid'] = order.userid
                orderTime = order.created_at.astimezone(east)
                orderDict['created_at'] = orderTime
                attachments = []
                attachs = OrderAttachment.query.filter_by(orderid=int(item['id'])).order_by(
                    desc(OrderAttachment.created_at)).all()
                if len(attachs) > 0:
                    for atItem in attachs:
                        attRec = Attachment.query.filter_by(id=atItem.attachid).first()
                        if attRec.public == 1:
                            attachments.append(
                                app.config['QUESTION_ATTACHMENTS'] + str(order.userid) + '/' + str(
                                    item['id']) + '/' + attRec.path)

                orderDict['attachments'] = attachments

                orderUnionRole = OrderUnionRole.query.filter_by(orderid=int(item['id'])).first()
                if orderUnionRole is not None:
                    if not orderUnionRole.unionroleid == checkOtherUnionRole.id:
                        checkUnionRole = UnionRole.query.filter_by(id=orderUnionRole.unionroleid).first()
                        orderDict['unionrole'] = checkUnionRole.name
                    else:
                        orderDict['unionrole'] = ''
                else:
                    orderDict['unionrole'] = ''

                localDict['order'] = orderDict

                answerDict = {}
                answer = AnswerMess.query.filter_by(orderid=int(item['id'])).first()
                cleananswer = re.compile('<.*?>')
                answerDict['text'] = re.sub(cleananswer, '', answer.text)
                # answerDict['text'] = answer.text
                answerDict['userid'] = answer.userid
                answerDict['created_at'] = answer.created_at
                answerTime = answer.modified_at.astimezone(east)
                answerDict['modified_at'] = answerTime.strftime("%d.%m.%Y")
                answerattachs = []
                answatts = AnswerAttachment.query.filter_by(answerid=answer.id).order_by(
                    desc(AnswerAttachment.created_at)).all()
                if len(answatts) > 0:
                    for ansItem in answatts:
                        attAnswRec = Attachment.query.filter_by(id=ansItem.attachid).first()
                        if attAnswRec.public == 1:
                            answerattachs.append(app.config['ANSWER_ATTACHMENTS'] + str(answer.userid) + '/' + str(
                                item['id']) + '/' + attAnswRec.path)
                answerDict['attachments'] = answerattachs
                localDict['answer'] = answerDict
                contentDict[item['id']] = localDict

        questionTitle = 'Вопросы и ответы'

        if app.config['FLASK_ENV'] == 'production':
            page = confluence.get_page_by_title(space, questionTitle, 0, 1, expand="body.storage.value")
        else:
            page = confluence.get_page_by_id(app.config['CONFLUENCE_PUBLIC_TESTPAGE_ID'], expand="body.storage.value")

        for j in range(0, 1000, 50):
            resp = confluence.get_attachments_from_content(page['id'], start=j, limit=50, expand=None, filename=None,
                                                           media_type=None)
            if len(resp) > 0:
                attachList = resp['results']
                for delItem in attachList:
                    confluence.delete_attachment(page['id'], delItem['title'], version=None)
        for numKey, key in enumerate(contentDict, start=1):
            body = body + """
                                   <tr><td style="vertical-align: middle;text-align: left;"><span>""" + str(numKey) + """</span></td>
                                   <td style="vertical-align: middle;text-align: left; min-width: 100px;"><div class="content-wrapper"><p>""" + \
                   contentDict[key]['answer']['modified_at'] + """</p>
                                   <ac:structured-macro ac:macro-id="29f83253-7ddd-44ec-b91e-2291e36fb998" ac:name="html" ac:schema-version="1">
                                   <ac:plain-text-body><![CDATA[<span id='anchor-""" + spaceRec.spacekey + """-""" + \
                   contentDict[key]['order']['orderid'] + """'></span>]]></ac:plain-text-body>
                                  </ac:structured-macro></div></td>"""

            if roleOutFlag:
                # if not contentDict[key]['order']['unionrole'] == '':
                body = body + """
                                <td style="vertical-align: middle;text-align: left; min-width: 100px;"><p>""" + \
                       contentDict[key]['order']['unionrole'] + """</p></td>
                                """
            body = body + """
                                <td style="vertical-align: middle;text-align: left;"><div class="content-wrapper"><p>""" + \
                   contentDict[key]['order']['text'] + """</p>"""
            atOrderList = contentDict[key]['order']['attachments']
            attTextBody = """"""
            for num, filename in enumerate(atOrderList, start=1):
                filesplit = os.path.splitext(filename)
                extension = filesplit[1]
                newFileName = 'Приложение-к-вопросу-' + str(numKey) + '-' + str(num) + extension
                attTextBody = attTextBody + """
                                <p>
                                    <ac:link>
                                        <ri:attachment ri:filename='""" + newFileName + """'/>
                                    </ac:link>
                                </p>"""
                content_type = setContenType(extension)
                confluence.attach_file(filename, name=newFileName, content_type=content_type, page_id=page['id'],
                                       title=questionTitle, space=space)
            body = body + attTextBody + """</div></td><td style="vertical-align: middle;"><div><p style="text-align: center;">""" + \
                   contentDict[key]['order']['orderid'] + """</p></div></td>
                                <td style="vertical-align: middle;text-align: left;"><div class="content-wrapper"><p>""" + markdown.markdown(
                contentDict[key]['answer']['text']) + """</p></div>"""
            atAnswerList = contentDict[key]['answer']['attachments']
            attAnswTextBody = """"""
            for num, filename in enumerate(atAnswerList, start=1):
                filesplit = os.path.splitext(filename)
                extension = filesplit[1]
                newFileName = 'Приложение-к-ответу-' + str(numKey) + '-' + str(num) + extension
                attAnswTextBody = attAnswTextBody + """
                                            <p>
                                                <ac:link>
                                                    <ri:attachment ri:filename='""" + newFileName + """'/>
                                                </ac:link>
                                            </p>"""
                content_type = setContenType(extension)
                confluence.attach_file(filename, name=newFileName, content_type=content_type,
                                       page_id=page['id'], title=questionTitle, space=space)
            body = body + attAnswTextBody + """</td></tr>"""

        body = body + """
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
        confluence.update_page(page['id'], questionTitle, body, type='page', representation='storage',
                               minor_edit=False)
        appConfRecEnd = AppConfig.query.order_by(desc('created_at')).limit(1).first()
        appConfRecEnd.ispublicactive = 0
        db.session.commit()
    except Exception as e:
        print(str(e))
        print("ERROR during public question" + str(orderid))
        appConfRecEnd = AppConfig.query.order_by(desc('created_at')).limit(1).first()
        appConfRecEnd.ispublicactive = 0
        db.session.commit()
        check_public = OrderPublic.query.filter_by(orderid=int(orderid)).first()
        if check_public is not None:
            db.session.delete(check_public)
            db.session.commit()
