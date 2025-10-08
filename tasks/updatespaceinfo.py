from bs4 import BeautifulSoup
from sqlalchemy import and_
from database import db
import pandas as pd
from celery import shared_task
from questionsapp.models import Spaces, BotSpaces, OrderSpace, UnionRole, SpaceUnionRoleActive, SpaceUnionRole
from flask import current_app as app
import requests, cx_Oracle
from supp_db.queries.suppallroles import supp_all_roles
from supp_db.supp_connection import dsn

@shared_task()
def update_spaces_info():
        try:
            if app.config['FLASK_ENV'] == 'production':
                con = cx_Oracle.connect(user=app.config['SUPP_DB_USERNAME'], password=app.config['SUPP_DB_PASS'],dsn=dsn, encoding="UTF-8", nencoding="UTF-8")
                dfSuppRoles = pd.read_sql(supp_all_roles, con=con)
            else:
                dfSuppRoles = pd.read_parquet('/usr/src/data/all_supp_roles.parquet.gzip')

            dfSuppRoles = dfSuppRoles.drop_duplicates(subset=['USER_ROLE_ID'], keep='first')

            supproles_list = dfSuppRoles.to_dict("records")

            supproles_dict = {}

            for rItem in supproles_list:
                if not rItem['USER_ROLE_ID'] in supproles_dict:
                    supproles_dict[rItem['USER_ROLE_ID']] = rItem['USER_ROLE']
        except Exception as e:
            return {'status':'error', 'error_mess': "ВНИМАНИЕ! Ошибка при попытке получить данные по всем ролям в СУПП. Текст ошибки: << "+str(e)+" >>"}

        try:
            requestUrl = app.config['CONFLUENCE_SPACEINFO_PAGE']
            requestResponse = requests.get(requestUrl,auth=(app.config['CONFL_BOT_NAME'], app.config['CONFL_BOT_PASS']))
            contentRaw = requestResponse.json()
            body = contentRaw['body']['storage']['value']
            mat_soup = BeautifulSoup(body, "lxml")
            table = mat_soup.find('table')

            headers = [header.text for header in table.find_all('th')]
            results = [{headers[i]: cell.get_text() for i, cell in enumerate(row.find_all('td'))}
                       for row in table.find_all('tr')]

        except Exception as e:
            return {'status': 'error','error_mess': "ВНИМАНИЕ! Ошибка при попытке получить данные из таблицы пространств на портале edu. Текст ошибки: << " + str(e) + " >>"}


        spacesDict = {}
        botSpacesDict = {}

        unionroles_custom = {}
        unionroles_supp = {}

        exist_custom_unionroles = []
        exist_supp_unionroles = {}

        space_unionroles_active = []

        try:
            for exCusUnItem in UnionRole.query.filter(UnionRole.emiasid == 0).all():
                if not exCusUnItem.name in exist_custom_unionroles:
                    exist_custom_unionroles.append(exCusUnItem)

            for exSuppUnItem in UnionRole.query.filter(UnionRole.emiasid != 0).all():
                if not exSuppUnItem.emiasid in exist_supp_unionroles:
                    exist_supp_unionroles[exSuppUnItem.emiasid] = exSuppUnItem.name
        except Exception as e:
            return {'status': 'error','error_mess': "ВНИМАНИЕ! Ошибка при попытке сформировать списки по существующим объединенным ролям. Текст ошибки: << " + str(e) + " >>"}



        rows_with_error = []

        for itemDict in results:
            if not bool(itemDict):
                pass
            else:
                    if itemDict['Опубликовано на Viewport'].strip().lower() == 'да':
                        if len(itemDict['Ключ в VP'].strip()) == 0 or len(itemDict['Название пространства'].strip()) == 0:
                            pass
                        else:
                            spacesDict[itemDict['Ключ в VP'].strip()] = itemDict['Название пространства'].strip()

                            try:
                                if not len(itemDict['id ролей, для которых предназначено пространство'].strip()) == 0 or not len(itemDict['Название функционала, если отсутствует id роли'].strip()) == 0:
                                    space_unionroles_active.append(itemDict['Ключ в VP'].strip())

                                if not len(itemDict['id ролей, для которых предназначено пространство'].strip()) == 0:
                                    rolesid_list_string = itemDict['id ролей, для которых предназначено пространство'].strip().split(";")
                                    rolesid_list = []
                                    for rItem in rolesid_list_string:
                                        if rItem.strip() not in rolesid_list and not rItem.strip() == '':
                                            rolesid_list.append(int(rItem.strip()))
                                    if not itemDict['Ключ в VP'].strip() in unionroles_supp:
                                        unionroles_supp[itemDict['Ключ в VP'].strip()] = rolesid_list
                                    else:
                                        exist_rolesid_list = unionroles_supp[itemDict['Ключ в VP'].strip()]
                                        for nItem in rolesid_list:
                                            if nItem not in exist_rolesid_list:
                                                exist_rolesid_list.append(int(nItem))
                                        unionroles_supp[itemDict['Ключ в VP'].strip()] = exist_rolesid_list

                                if not len(itemDict['Название функционала, если отсутствует id роли'].strip()) == 0:
                                    rolesid_list_string = itemDict['Название функционала, если отсутствует id роли'].strip().split(";")
                                    rolesid_list = []
                                    for rItem in rolesid_list_string:
                                        if rItem.strip() not in rolesid_list and not rItem.strip() == '' and not rItem.strip().lower() == 'другое':
                                            rolesid_list.append(rItem.strip())
                                    if not itemDict['Ключ в VP'].strip() in unionroles_custom:
                                        unionroles_custom[itemDict['Ключ в VP'].strip()] = rolesid_list
                                    else:
                                        exist_rolesid_list = unionroles_custom[itemDict['Ключ в VP'].strip()]
                                        for nItem in rolesid_list:
                                            if nItem not in exist_rolesid_list:
                                                exist_rolesid_list.append(nItem)
                                        unionroles_custom[itemDict['Ключ в VP'].strip()] = exist_rolesid_list
                            except:
                                rows_with_error.append(itemDict['Название пространства'].strip())
                                pass
                    else:
                        pass

                    try:
                        if itemDict['Пространством пользуются МО'].strip().lower() == 'да':
                            if len(itemDict['Ключ в VP'].strip()) == 0 or len(itemDict['Название пространства'].strip()) == 0:
                                pass
                            else:
                                botSpacesDict[itemDict['Ключ в VP'].strip()] = itemDict['Название пространства'].strip()
                        else:
                            pass

                    except:
                        pass

        if len(rows_with_error)>0:
            if app.config['FLASK_ENV'] == 'development':
                print("ВНИМАНИЕ! Есть ошибки при обработке строк таблицы пространств")
                print("Перечень строк с ошибками: ", rows_with_error)


        spacesDict['nullspacekey'] = 'Не распределено'
        botSpacesDict['nullspacekey'] = 'Не распределено'

        existSpacesList = []

        try:
            existSpaces = Spaces.query.all()
            for exItem in existSpaces:
                if exItem.spacekey not in spacesDict:
                    checkOrders = OrderSpace.query.filter(OrderSpace.spaceid == exItem.id).all()
                    if not len(checkOrders) == 0:
                        checkNullSpace = Spaces.query.filter_by(spacekey="nullspacekey").first()
                        for sItem in checkOrders:
                            sItem.spaceid = checkNullSpace.id
                            db.session.commit()
                    db.session.delete(exItem)
                else:
                    existSpacesList.append(exItem.spacekey)
            db.session.commit()
        except Exception as e:
            return {'status': 'error','error_mess': "ВНИМАНИЕ! Ошибка в процессе работы с базой данных пространств после парсинга таблицы пространств. Текст ошибки: << " + str(e) + " >>"}


        existBotSpacesList = []

        try:
            existBotSpaces = BotSpaces.query.all()
            for exBotItem in existBotSpaces:
                if exBotItem.spacekey not in botSpacesDict:
                    db.session.delete(exBotItem)
                else:
                    existBotSpacesList.append(exBotItem.spacekey)
            db.session.commit()
            for key in spacesDict.keys():
                if key not in existSpacesList and not key == 'nullspacekey':
                    newSpace = Spaces(spacekey=key, title=spacesDict[key])
                    db.session.add(newSpace)
            db.session.commit()
            for bkey in botSpacesDict.keys():
                if bkey not in existBotSpacesList and not bkey == 'nullspacekey':
                    newBotSpace = BotSpaces(spacekey=bkey, title=botSpacesDict[bkey])
                    db.session.add(newBotSpace)
            db.session.commit()
        except Exception as e:
            return {'status': 'error','error_mess': "ВНИМАНИЕ! Ошибка в процессе работы с базой данных пространств бота после парсинга таблицы пространств. Текст ошибки: << " + str(e) + " >>"}

        exist_active_spaces = []

        try:
            for exAcitem in SpaceUnionRoleActive.query.all():
                if exAcitem.spaceid not in exist_active_spaces:
                    exist_active_spaces.append(exAcitem.spaceid)

            new_active_spaces = []

            for actItem in space_unionroles_active:
                checkSpace = Spaces.query.filter_by(spacekey=actItem).first()

                if checkSpace is not None:
                    new_active_spaces.append(checkSpace.id)
                    checkActiveUnionRoleSpace = SpaceUnionRoleActive.query.filter_by(spaceid=checkSpace.id).first()
                    if checkActiveUnionRoleSpace is not None:
                        checkActiveUnionRoleSpace.active = 1
                        db.session.commit()
                    else:
                        newSpaceActive = SpaceUnionRoleActive(spaceid=checkSpace.id, active=1)
                        db.session.add(newSpaceActive)
                        db.session.commit()

            for exItem in exist_active_spaces:
                if exItem not in new_active_spaces:
                    checkActiveUnionRoleSpace = SpaceUnionRoleActive.query.filter_by(spaceid=exItem).first()
                    checkActiveUnionRoleSpace.active = 0
                    db.session.commit()

        except Exception as e:
            return {'status': 'error','error_mess': "ВНИМАНИЕ! Ошибка в процессе работы с базой данных, хранящей флаги использования объединенных ролей в пространстве. Текст ошибки: << " + str(e) + " >>"}


        try:
            for sItem in unionroles_supp:
                supp_idlist = unionroles_supp[sItem]
                checkSpace = Spaces.query.filter_by(spacekey=sItem).first()
                existSpaceUnRolesId = []

                if checkSpace is not None:
                    for exsSURItem in SpaceUnionRole.query.filter_by(spaceid=checkSpace.id).all():
                        checkExRole = UnionRole.query.filter_by(id=exsSURItem.unionroleid).first()
                        if checkExRole.emiasid !=0:
                            existSpaceUnRolesId.append(checkExRole.emiasid)

                    if len(existSpaceUnRolesId) > 0:
                        for item in existSpaceUnRolesId:
                            if item not in supp_idlist:
                                checkRole = UnionRole.query.filter_by(emiasid=item).first()
                                if checkRole is not None:
                                    checkExSpaceRole = SpaceUnionRole.query.filter(and_((SpaceUnionRole.spaceid == checkSpace.id),(SpaceUnionRole.unionroleid == checkRole.id))).first()
                                    if checkExSpaceRole is not None:
                                        db.session.delete(checkExSpaceRole)
                                        db.session.commit()

                for idItem in supp_idlist:
                    try:
                        emiasid = idItem
                        roleid = 0
                        checkUnionRole = UnionRole.query.filter_by(emiasid=emiasid).first()
                        if checkUnionRole is None:
                            if emiasid in supproles_dict:
                                newUnionRole = UnionRole(emiasid=emiasid, name=supproles_dict[emiasid])
                                db.session.add(newUnionRole)
                                db.session.commit()
                                roleid = newUnionRole.id
                        else:
                            checkUnionRole.name = supproles_dict[emiasid]
                            db.session.commit()
                            roleid = checkUnionRole.id

                        if checkSpace is not None and roleid !=0:
                            checkSpaceRole = SpaceUnionRole.query.filter(and_((SpaceUnionRole.spaceid == checkSpace.id),(SpaceUnionRole.unionroleid == roleid))).first()
                            if checkSpaceRole is None:
                                newCheckSpaceRole = SpaceUnionRole(spaceid=checkSpace.id, unionroleid=roleid)
                                db.session.add(newCheckSpaceRole)
                                db.session.commit()
                    except:
                        pass

            checkOtherUnionRole = UnionRole.query.filter(and_((UnionRole.name == 'Другое'), (UnionRole.emiasid == 0))).first()
            if checkOtherUnionRole is None:
                newOtherUnionRole = UnionRole(name='Другое', emiasid=0)
                db.session.add(newOtherUnionRole)
                db.session.commit()



            for cItem in unionroles_custom:
                custom_namelist = unionroles_custom[cItem]
                checkSpace = Spaces.query.filter_by(spacekey=cItem).first()

                existSpaceUnCusRolesNames = []
                if checkSpace is not None:
                    for exSUCRItem in SpaceUnionRole.query.filter_by(spaceid=checkSpace.id).all():
                        checkRole = UnionRole.query.filter_by(id=exSUCRItem.unionroleid).first()
                        if checkRole is not None:
                            if checkRole.emiasid==0:
                                existSpaceUnCusRolesNames.append(checkRole.name)

                    if len(existSpaceUnCusRolesNames)>0:
                        for exItem in existSpaceUnCusRolesNames:
                            if exItem not in custom_namelist:
                                checkRole = UnionRole.query.filter(and_((UnionRole.name==exItem),(UnionRole.emiasid==0))).first()
                                if checkRole is not None:
                                    checkExSpaceRole = SpaceUnionRole.query.filter(and_((SpaceUnionRole.spaceid == checkSpace.id),(SpaceUnionRole.unionroleid == checkRole.id))).first()
                                    if checkExSpaceRole is not None:
                                        db.session.delete(checkExSpaceRole)
                                        db.session.commit()

                for nameItem in custom_namelist:
                    try:
                        checkUnionRole = UnionRole.query.filter(and_((UnionRole.name == nameItem), (UnionRole.emiasid == 0))).first()
                        if checkUnionRole is None:
                            newUnionRole = UnionRole(emiasid=0, name=nameItem)
                            db.session.add(newUnionRole)
                            db.session.commit()
                            roleid = newUnionRole.id
                        else:
                            roleid = checkUnionRole.id
                        if checkSpace is not None:
                            checkSpaceRole = SpaceUnionRole.query.filter(and_((SpaceUnionRole.spaceid == checkSpace.id),(SpaceUnionRole.unionroleid == roleid))).first()
                            if checkSpaceRole is None:
                                newCheckSpaceRole = SpaceUnionRole(spaceid=checkSpace.id, unionroleid=roleid)
                                db.session.add(newCheckSpaceRole)
                                db.session.commit()
                    except:
                        pass
        except Exception as e:
            return {'status': 'error','error_mess': "ВНИМАНИЕ! Ошибка в процессе создания и привязки объединенных ролей к пространству. Текст ошибки: << " + str(e) + " >>"}

        return {'status':'ok'}