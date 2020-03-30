import codecs
import os
import re

import jieba
import numpy as np
import pandas
import pymysql

from qgw_autoflow import conf
from qgw_autoflow.common.resource import EVENT_CAT, DEP_ADDRESS, WEIGHT_MATRIX, STOPWORDS, USERDICT

jieba.load_userdict(USERDICT)
stopwords = {}.fromkeys([line.rstrip() for line in codecs.open(STOPWORDS, 'r', encoding='utf8')])

# 获取案件类别最小类的id对应的大小三类中文名称，可以和我们获取的类别信息一一对应，类别中文名用#做分割
# event_cat={'城市管理#市政设施#市政道路设施':'2016073104'}
event_cat = {}
for line in codecs.open(EVENT_CAT, 'r', encoding='utf8'):
    try:
        event_cat[line.split('@')[0]] = int(line.split('@')[1])
    except:
        continue

db = pymysql.connect(conf.db_host, conf.db_user, conf.db_pwd, "auto_flow", charset='utf8')
cursor = db.cursor()
cursor.execute("SELECT * FROM auto_flow.visual_depart;")
all_department = cursor.fetchall()
db.close()

# 将所有处置单位读入字典，key为部门id，value是部门名称、父级id和tier；all_dep{'5789917294897807434':'南明区@5154297156650094256@2'}
# 将所有联动单位的父级id作为key，父级id下面的所有联动单位作为list（value）读入字典；bureau_dep{'5154297156650094256':['-2038452952757288084@贵阳市教育局@2','贵阳市工商局@5154297156650094256@2']}
all_dep, bureau_dep = {}, {}
for item in all_department:  #####
    try:
        all_dep[item[1]] = item[2] + '@' + item[3] + '@' + item[5]
    except:
        all_dep[item[1]] = item[2] + '@' + '' + '@' + item[5]
    if item[4] == '联动单位':
        if item[3] not in bureau_dep:
            bureau_dep[item[3]] = ['@'.join(item[1:3]) + '@' + item[5]]
        else:
            bureau_dep[item[3]].append('@'.join(item[1:3]) + '@' + item[5])

path = os.getcwd()
dep_address = pandas.read_csv(DEP_ADDRESS)  # 读取网格中心推荐矩阵
weight_matrix = np.load(WEIGHT_MATRIX)  #读取联动单位推荐矩阵

grider_center_name = list(dep_address['Unnamed: 0'])  #####
dep_address = dep_address.set_index(['Unnamed: 0'])


def grid_center(case_id, location, case_type, linkage_unit_list):
    # 确定当前处置部门
    current_dep = {}
    if linkage_unit_list == []:
        current_dep = {
            "id": "5154297156650094256",
            "tier": "1",
            "name": "贵阳市"
        }
    else:
        for dic in linkage_unit_list:
            if (current_dep and int(dic['tier']) < int(current_dep['tier'])) or current_dep == {}:
                current_dep = dic
    dep_list = [current_dep['id'] + '@' + current_dep['name'] + '@' + current_dep['tier']]
    address = []
    level1, level2, level3, level4 = {}, {}, {}, {}
    # 网格中心推荐
    if location != '' and '@'.join(dep_list[0].split('@')[:2]) in grider_center_name:
        #将获得的location字段内容做分词处理，把分词结果存入address列表，过滤掉单个字及停用词列表中的词语
        temp = jieba.cut(location)

        for item in temp:
            if item not in stopwords and len(item) > 1:
                address.append(item)

        # 逐个读取address列表中的元素，对应dep_address矩阵中的地理名词列，然后将多个列相加，得到多个地理名词列的权重计算结果
        #对于矩阵中没有的地理名词则跳过
        j, sums = 0, [0] * len(grider_center_name)

        for item in address:
            try:
                temp, n = list(dep_address[item]), 0
                for num in temp:
                    sums[n] += num
                    n += 1
            except:
                continue
        #对于相加的结果，依次选则前三大的权重对应的网格中心，并且根据当前部门层级推荐下级网格中心
        while j < 3:
            loc = sums.index(max(sums))
            sums[sums.index(max(sums))] = 0
            level = all_dep[grider_center_name[loc].split('@')[0]].split('@')[2]
            temp = grider_center_name[loc] + '@' + level
            # dep_list.append(temp)
            parent_center = all_dep[grider_center_name[loc].split('@')[0]].split('@')[1] \
                            + '@' + all_dep[all_dep[grider_center_name[loc].split('@')[0]].split('@')[1]].split('@')[0] \
                            + '@' + str(int(level) - 1)
            if current_dep['tier'] == '1' and level == '2':
                if parent_center not in level2:
                    level2[parent_center] = [temp]
                else:
                    level2[parent_center].append(temp)
            if current_dep['tier'] == '2' and level == '3':
                if parent_center not in level3:
                    level3[parent_center] = [temp]
                else:
                    level3[parent_center].append(temp)
            if current_dep['tier'] == '3' or level == '4':
                if level == '4':
                    level4[parent_center] = [temp]
                else:
                    level4[current_dep['id'] + '@' + current_dep['name'] + '@' + current_dep['tier']] = []
            j += 1
    else:
        # 如果location字段为空，则把当前部门存入对应level，方便计算下级联动单位
        temp = current_dep['id'] + '@' + current_dep['name'] + '@' + current_dep['tier']
        #dep_list.append(temp)
        level = current_dep['tier']
        if level != '1':
            if level == '2':
                level3[temp] = []
            if level == '3':
                level4[temp] = []
        else:
            level2[temp] = []

    # 联动单位推荐
    united_dep, respond = [], []
    case_type = re.sub(r'##|###|#$', '', case_type)
    # 读取存在dep_list中的当前处置部门（网格中心），并获取这个网格中心的所有下级联动单位(sub_dep_list)，在这个sub_dep_list中
    #寻找权重最高的联动单位进行推荐。
    for item in dep_list:
        if item.split('@')[0] in bureau_dep:
            item_level = item.split('@')[2]
            sub_dep_list = bureau_dep[item.split('@')[0]]
            type_id = event_cat[case_type]
            x = int(np.where(weight_matrix[:, 0, 0] == type_id)[0][0])  #根据类别id确定x的坐标
            MAX = []
            #把这个类别对应的所有sub_dep_list中的联动单位权重存入MAX列表
            for dep in sub_dep_list:
                try:
                    unit_dep_id = int(dep.split('@')[0])
                    y = int(np.where(weight_matrix[0, :, 0] == unit_dep_id)[0][0])
                    MAX.append(weight_matrix[x, y, 2])
                except:
                    pass
            if max(MAX) != 0:
                #获取最高权重的索引位置，并在sub_dep_list中找到这个联动单位，然后根据当前处置部门的层级去进行推荐
                loc = MAX.index(max(MAX))
                united_dep.append(sub_dep_list[loc])
                if item_level == '1':
                    level2[item].append(sub_dep_list[loc])
                if item_level == '2':
                    level3[item].append(sub_dep_list[loc])
                if item_level == '3':
                    if item not in level4:
                        level4[item] = [sub_dep_list[loc]]
                    else:
                        level4[item].append(sub_dep_list[loc])
    #根据当前层级返回标准格式的推荐部门
    if current_dep['tier'] == '1':
        for item in level2:
            for dep in level2[item]:
                model = {'id': dep.split('@')[0], 'name': dep.split('@')[1], 'tier': dep.split('@')[2], 'possibility': 1}
                respond.append(model)
        return respond
    elif current_dep['tier'] == '2':
        for item in level3:
            for dep in level3[item]:
                model = {'id': dep.split('@')[0], 'name': dep.split('@')[1], 'tier': dep.split('@')[2], 'possibility': 1}
                respond.append(model)
        return respond
    elif current_dep['tier'] == '3':
        for item in level4:
            for dep in level4[item]:
                model = {'id': dep.split('@')[0], 'name': dep.split('@')[1], 'tier': dep.split('@')[2], 'possibility': 1}
                respond.append(model)
        return respond
