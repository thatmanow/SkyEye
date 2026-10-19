import re
import sys

sys.path.insert(0, r'E:\SkyEyev2.0\backend')
from tyt.seed import data_risks as DR

src = open(r'E:\SkyEyev2.0\backend\tyt\seed\data_life.py', encoding='utf-8').read()
m = re.findall(r'"(landlord|agency|estate)",\s*"([^"]+)"', src)
types = {}
for t, n in m:
    types.setdefault(t, set()).add(n)
for t, ns in types.items():
    print(t, ':', sorted(ns))

labor = [r for r in DR.COMPANY_RISKS if '劳动' in str(r) or '欠薪' in str(r)]
print('\nlabor risk rows:', len(labor))
for r in labor[:6]:
    print(' ', r[1] if len(r) > 1 else r)
