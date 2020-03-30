# -*- coding=utf8 -*-

import codecs
import re

from qgw_autoflow import conf
from qgw_autoflow.common.resource import EVENT_CAT

event_category = codecs.open(EVENT_CAT, 'w', encoding='utf8')

db = conf.db_default()
cursor = db.cursor()
cursor.execute("SELECT * FROM auto_flow.visual_category;")
data = cursor.fetchall()
db.close()


# 递归查找父级类别
def parent_child(p):
    if p in child:
        loc = child.index(p)
        return parent_child(parent[loc]) + '#' + dep[child.index(p)]
    else:
        return ""


# 取出所有案件类别id, parent_id, name存入数组
child, parent, dep, types, process = [], [], [], [], []
for detail in data:
    child.append(detail[1])
    parent.append(detail[2])
    dep.append('@'.join([detail[1], detail[3]]))

# 遍历所有根节点
for ch in child:
    ind = child.index(ch)
    s = parent_child(parent[ind]) + '#' + dep[ind]
    s = re.sub('^#', '', s)
    process.append(s)
process.sort()

for item in process:
    cat = ''
    temp = item.split('#')
    for term in temp:
        cat += ('#' + term.split('@')[1])
        cat_id = term.split('@')[0]
    cat += ('@' + cat_id)
    cat = re.sub(r'^#', '', cat)
    event_category.write(cat + '\n')

event_category.close()


def get_cat():
    '''# 遍历所有根节点
    for i in child:
        j = child.index(i)
        k = parent_child(parent[j]) + ',' + dep[child.index(i)]
        k = re.sub('^,', '', k)
        process.append(k)
    process.sort()'''
    return process
