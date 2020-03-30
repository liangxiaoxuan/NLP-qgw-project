# -*- encoding=utf8 -*-
import codecs
import os
import re

import jieba
import numpy as np
from pandas import DataFrame as DF

from qgw_autoflow import conf

path = os.getcwd() + "/"

jieba.load_userdict(path + r"../resources/Case_Assign/userdict.txt")
stopwords = {}.fromkeys(
    [line.rstrip() for line in codecs.open(path + r'../resources/Case_Assign/stop_words1.txt', 'r', encoding='utf8')])

db = conf.db_default()
cursor = db.cursor()
cursor.execute("SELECT * FROM auto_flow.visual_depart;")
department = cursor.fetchall()
db.close()

dep_address, address_terms, grid_center = {}, set(), []
file1 = codecs.open(path + r'../resources/Case_Assign/dep_address.txt', 'r', encoding='utf8')
for line in file1:
    dep, address = line.split(':')[0], line.split(':')[1].split('$')
    address[-1] = re.sub(r'[^\u4e00-\u9fa5]*', '', address[-1])
    del address[0]
    dep_address[dep] = address
    address_terms.update(address)
file1.close()
for dep in department:
    if dep[4] == '网格中心':
        grid_center.append('@'.join(dep[1:3]))

temp = list(address_terms)
# temp.insert(0,'网格中心')
data = np.zeros((len(grid_center), len(temp)))
frame2 = DF(data, columns=temp, index=grid_center)

for item in dep_address:
    if item in grid_center and dep_address[item] != '':
        for address in dep_address[item]:
            if dep_address[item].index(address) == 0:
                frame2[address][item] += 100
            elif address in grid_center:
                frame2[address][item] += 10
            else:
                frame2[address][item] += 1
# print(frame2.index)
frame2.to_csv(path + r"../resources/Case_Assign/dep_address.csv")
