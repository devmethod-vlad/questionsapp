supp_all_roles = """SELECT distinct ur.USER_ROLE, ur.ID AS USER_ROLE_ID
FROM emias_cluster.USER_ROLE ur
UNION
SELECT distinct ur.USER_ROLE, ur.ID AS USER_ROLE_ID
FROM ETD2.USER_ROLE ur
"""