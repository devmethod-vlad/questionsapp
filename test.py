from zipfile import ZipFile

import pandas as pd

# df = pd.read_parquet('/usr/src/data/suppinfo/supp_09_04_2024_13_10.parquet.gzip')

# df.to_excel('/usr/src/data/suppinfo/supp_09_04_2024_13_10.xlsx')

# df = pd.read_excel('/usr/src/data/suppinfo/supp_09_04_2024_13_10.xlsx')

with ZipFile('/usr/src/data/suppinfo/supp_09_04_2024_13_10.zip', 'w', compresslevel=9) as myzip:
    myzip.write('/usr/src/data/suppinfo/supp_09_04_2024_13_10.xlsx')