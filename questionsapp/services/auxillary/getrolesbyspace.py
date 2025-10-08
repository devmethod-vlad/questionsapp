from questionsapp.models import UnionRole, SpaceUnionRole, UserUnionRole
from questionsapp.services.roles.getrole import get_role
from flask import current_app as app

def get_roles_by_space(spaceid, roleid, userid):

    if spaceid and roleid:

        role_list = []

        role = get_role(roleid)

        if role:

            if role == 'redactor' or role == 'admin':

                for item in SpaceUnionRole.query.filter(SpaceUnionRole.spaceid == int(spaceid)).all():
                    role_rec = UnionRole.query.filter_by(id=item.unionroleid).first()

                    if role_rec:
                        role_list.append({'id': role_rec.id, 'emiasid': role_rec.emiasid, 'name': role_rec.name})


            else:
                user_roles_idlist = []

                for item in UserUnionRole.query.filter(UserUnionRole.userid == int(userid)).all():
                    user_roles_idlist.append(item.unionroleid)

                if int(spaceid) != app.config['NULLSPACE']['id']:
                    for item in SpaceUnionRole.query.filter(SpaceUnionRole.spaceid == int(spaceid)).all():

                        role_rec = UnionRole.query.filter_by(id=item.unionroleid).first()

                        if role_rec:
                            if role_rec.emiasid != 0 and role_rec.id in user_roles_idlist:
                                role_list.append(
                                    {'id': role_rec.id, 'emiasid': role_rec.emiasid, 'name': role_rec.name})

                else:
                    for item in user_roles_idlist:
                        role_rec = UnionRole.query.filter_by(id=item).first()

                        if role_rec:
                            if role_rec.emiasid != 0:
                                role_list.append(
                                    {'id': role_rec.id, 'emiasid': role_rec.emiasid, 'name': role_rec.name})

            if len(role_list) > 1:
                role_list = sorted(role_list, key=lambda x: x['name'])

            return {'status': 'ok', 'info': {'roles_list': role_list}}

        else:
            return {"status": "error", "error_mess": "WARN: No role"}
    else:
        return {"status": "error", "error_mess": "WARN: No spaceid param"}