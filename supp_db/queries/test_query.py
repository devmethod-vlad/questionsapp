import pandas as pd

SQLALCHEMY_DATABASE_URI = 'postgresql://root:root@postgresdb:5432/info'

dfSuppRoles = pd.read_sql(supp_all_roles, con=con)

supp_all_roles = """SELECT ur.USER_ROLE, ur.ID AS USER_ROLE_ID
FROM emias_cluster.USER_ROLE ur
UNION
SELECT ur.USER_ROLE, ur.ID AS USER_ROLE_ID
FROM ETD2.USER_ROLE ur
"""