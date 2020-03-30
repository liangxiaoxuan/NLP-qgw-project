import random
import re

import pandas
import pymysql
import numpy as np
from qgw_autoflow import conf
from qgw_autoflow.common.resource import MINI_WORD, TIER2_GRID, TIER3_GRID
from qgw_autoflow.common.resource import TIER2_LINK, TIER3_LINK, TIER4_LINK, TIER2_LINK_KEYWORD, TIER3_LINK_KEYWORD, \
    TIER4_LINK_KEYWORD
from sklearn.externals import joblib

from qgw_autoflow.common.resource import YUNYAN_LBL,YUNYAN_RF,YUNYAN_TFIDF,YUNYAN_VEC, \
    NANMING_LBL,NANMING_RF,NANMING_TFIDF,NANMING_VEC,\
    BAIYUN_LBL,BAIYUN_RF,BAIYUN_TFIDF,BAIYUN_VEC,\
    HUAXI_LBL,HUAXI_RF,HUAXI_TFIDF,HUAXI_VEC,\
    WUDANG_LBL,WUDANG_RF,WUDANG_TFIDF,WUDANG_VEC,\
    GUANSHANHU_LBL,GUANSHANHU_RF,GUANSHANHU_TFIDF,GUANSHANHU_VEC,\
    QINGZHEN_LBL,QINGZHEN_RF,QINGZHEN_TFIDF,QINGZHEN_VEC,\
    XIFENG_LBL,XIFENG_RF,XIFENG_TFIDF,XIFENG_VEC,\
    KAIYANG_LBL,KAIYANG_RF,KAIYANG_TFIDF,KAIYANG_VEC,\
    XIUWEN_LBL,XIUWEN_RF,XIUWEN_TFIDF,XIUWEN_VEC

from qgw_autoflow.service.word_split import load, mates

# 读取各区县模型
yunyan_vec = joblib.load(YUNYAN_VEC)
yunyan_tfidf = joblib.load(YUNYAN_TFIDF)
yunyan_lbl = joblib.load(YUNYAN_LBL)
yunyan_rf = joblib.load(YUNYAN_RF)

nanming_vec = joblib.load(NANMING_VEC)
nanming_tfidf = joblib.load(NANMING_TFIDF)
nanming_lbl = joblib.load(NANMING_LBL)
nanming_rf = joblib.load(NANMING_RF)

baiyun_vec = joblib.load(BAIYUN_VEC)
baiyun_tfidf = joblib.load(BAIYUN_TFIDF)
baiyun_lbl = joblib.load(BAIYUN_LBL)
baiyun_rf = joblib.load(BAIYUN_RF)

huaxi_vec = joblib.load(HUAXI_VEC)
huaxi_tfidf = joblib.load(HUAXI_TFIDF)
huaxi_lbl = joblib.load(HUAXI_LBL)
huaxi_rf = joblib.load(HUAXI_RF)

wudang_vec = joblib.load(WUDANG_VEC)
wudang_tfidf = joblib.load(WUDANG_TFIDF)
wudang_lbl = joblib.load(WUDANG_LBL)
wudang_rf = joblib.load(WUDANG_RF)

guanshanhu_vec = joblib.load(GUANSHANHU_VEC)
guanshanhu_tfidf = joblib.load(GUANSHANHU_TFIDF)
guanshanhu_lbl = joblib.load(GUANSHANHU_LBL)
guanshanhu_rf = joblib.load(GUANSHANHU_RF)

qingzhen_vec = joblib.load(QINGZHEN_VEC)
qingzhen_tfidf = joblib.load(QINGZHEN_TFIDF)
qingzhen_lbl = joblib.load(QINGZHEN_LBL)
qingzhen_rf = joblib.load(QINGZHEN_RF)

xifeng_vec = joblib.load(XIFENG_VEC)
xifeng_tfidf = joblib.load(XIFENG_TFIDF)
xifeng_lbl = joblib.load(XIFENG_LBL)
xifeng_rf = joblib.load(XIFENG_RF)

kaiyang_vec = joblib.load(KAIYANG_VEC)
kaiyang_tfidf = joblib.load(KAIYANG_TFIDF)
kaiyang_lbl = joblib.load(KAIYANG_LBL)
kaiyang_rf = joblib.load(KAIYANG_RF)

xiuwen_vec = joblib.load(XIUWEN_VEC)
xiuwen_tfidf = joblib.load(XIUWEN_TFIDF)
xiuwen_lbl = joblib.load(XIUWEN_LBL)
xiuwen_rf = joblib.load(XIUWEN_RF)

# 读取分词数据
ls = load(True)

# 六区三县一市
districts = ['云岩区', '南明区', '白云区', '花溪区', '乌当区', '观山湖区', '清镇市', '息烽县', '开阳县', '修文县']

# 获得最小地理名词粒度表
mini_word = []
with open(MINI_WORD, 'r', encoding='gbk') as mini:
    for i in mini:
        i = i.strip()
        mini_word.append(i)

# 获得联动单位关键词表
tier2_keyword, tier3_keyword, tier4_keyword = [], [], []
with open(TIER2_LINK_KEYWORD, 'r', encoding='gbk') as f:
    for i in f:
        a = i.strip('"').strip().rstrip('"')
        tier2_keyword.append(a)

with open(TIER3_LINK_KEYWORD, 'r', encoding='gbk') as f:
    for i in f:
        a = i.strip('"').strip().rstrip('"')
        tier3_keyword.append(a)

with open(TIER4_LINK_KEYWORD, 'r', encoding='gbk') as f:
    for i in f:
        a = i.strip('"').strip().rstrip('"')
        tier4_keyword.append(a)

# 获得二级网格中心概率表
tier2_grids = pandas.read_csv(TIER2_GRID, encoding='gbk')
tier2_grids.rename(columns={'Unnamed: 0': 'location_split'}, inplace=True)
tier2_grids = tier2_grids.set_index(['location_split'])

# 获得三级网格中心概率表
tier3_grids = pandas.read_csv(TIER3_GRID, encoding='gbk')
tier3_grids.rename(columns={'Unnamed: 0': 'location_split'}, inplace=True)
tier3_grids = tier3_grids.set_index(['location_split'])

# 获得二级联动单位概率表
tier2_link_prob = pandas.read_csv(TIER2_LINK, encoding='gbk')
tier2_link_prob.set_index('Unnamed: 0', inplace=True)
# 获得三级联动单位概率表
tier3_link_prob = pandas.read_csv(TIER3_LINK, encoding='gbk')
tier3_link_prob.set_index('Unnamed: 0', inplace=True)
# 获得四级联动单位概率表
tier4_link_prob = pandas.read_csv(TIER4_LINK, encoding='gbk')
tier4_link_prob.set_index('Unnamed: 0', inplace=True)

# 从数据库中获取所有单位列表
db_conf = {'host': conf.db_host,
           'user': conf.db_user,
           'password': conf.db_pwd,
           'db': 'auto_flow',
           'charset': 'utf8'}
conn = pymysql.connect(**db_conf)
cursor = conn.cursor()
cursor.execute('SELECT * FROM auto_flow.visual_depart;')
all_departments = cursor.fetchall()
conn.close()

# 从数据库中获得信息
tier3_grid = {}
grid2_id, grid2_name = [], []
grid_3_dic = {}
link_unit2, link_unit3 = {}, {}
unit_id2, unit_name2, unit_id3, unit_name3 = [], [], [], []

# 网格中心信息获取
for i in all_departments:
    if i[4] == '网格中心' and i[5] == '2':
        grid2_id.append(i[1])
        grid2_name.append(i[2])
        tier3_grid[i[1] + ',' + i[2]] = []
    if i[5] == '3':
        grid_3_dic[i[2]] = i[1]
for i in all_departments:
    if i[3] in grid2_id and i[4] == '网格中心':
        ind = grid2_id.index(i[3])
        tier3_grid[grid2_id[ind] + ',' + grid2_name[ind]].append(i[1] + ',' + i[2])

# 联动单位信息获取
for i in all_departments:
    if i[5] == '2':
        unit_id2.append(i[1])
        unit_name2.append(i[2])
        link_unit2[i[1] + ',' + i[2]] = []
    elif i[5] == '3':
        unit_id3.append(i[1])
        unit_name3.append(i[2])
        link_unit3[i[1] + ',' + i[2]] = []

for i in all_departments:
    if i[3] in unit_id2 and i[4] == '联动单位':
        ind2 = unit_id2.index(i[3])
        link_unit2[unit_id2[ind2] + ',' + unit_name2[ind2]].append(i[1] + ',' + i[2])

    if i[3] in unit_id3 and i[4] == '联动单位':
        ind3 = unit_id3.index(i[3])
        link_unit3[unit_id3[ind3] + ',' + unit_name3[ind3]].append(i[1] + ',' + i[2])

# 无主井盖与线缆初始化
jg = ['4735753215006097878,贵阳市供电局', '-3190018678578920118,贵阳市供水总公司', '-7029569853119115570,贵州燃气集团有限责任公司',
      '-5159211728551131176,中国移动通讯贵阳分公司', '-3850172974376073869,中国联通贵阳分公司', '3699297607899631568,中国电信贵阳分公司',
      '1875866429623451924,中国铁通贵阳分公司', '-1022948766658510616,贵州省广播电视信息网络股份有限公司贵阳市分公司']

xl = ['4735753215006097878,贵阳市供电局', '-5159211728551131176,中国移动通讯贵阳分公司', '-3850172974376073869,中国联通贵阳分公司',
      '3699297607899631568,中国电信贵阳分公司', '1875866429623451924,中国铁通贵阳分公司', '-1022948766658510616,贵州省广播电视信息网络股份有限公司贵阳市分公司']

xl_uni = ['中国移动', '中国联通', '中国电信', '中国铁通']


def dist_sub(line):
    for d in districts:
        line = re.sub(d, '', line)
    return line


def clean(line):
    line = re.sub(" ", "", line)
    line = re.sub("【微治】", "", line)
    line = re.sub("请职能部门及时处理", "", line)
    line = re.sub("请相关职能部门及时处理", "", line)
    line = re.sub("市民信息需要保密", "", line)
    line = re.sub("市民来电反映", "", line)
    line = re.sub("微信案件请附处理后图片，拍摄角度须与原图片一致", "", line)
    line = re.sub("请如实上报处理情况，附事前，事中，事后图片", "", line)
    line = re.sub("举报人反映", "", line)
    line = re.sub("请相关部门及时处理", "", line)
    line = re.sub("请相关职能部门及时核实并处理", "", line)
    line = re.sub("(请如实上报处理情况，附事前，事中，事后图片)", '', line)
    line = re.sub("请贵单位务必按照处置时限进行处置；如经现场核实不属于你单位，必须在处置时限内进行回复", "", line)
    line = re.sub("\\(.*\\)", "", line)
    line = re.sub("网格员反映", "", line)
    line = re.sub("该处有", "", line)
    line = re.sub("该处", "", line)
    line = re.sub("此处有", "", line)
    line = re.sub("及时进行处理", "", line)
    line = re.sub("[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领A-Z]{1}[A-Z]{1}[A-Z0-9]{4}[A-Z0-9挂学警港澳]{1}", "", line)
    line = re.sub("[0-9]{1,4}号", '', line)
    line = re.sub("[0-9]{1,4}点[0-9]{1,4}分", "", line)
    line = re.sub("[0-9]{1,4}分", "", line)
    line = re.sub("[0-9]{1,4}时", "", line)
    line = re.sub("贵[0-9]{1,6}", "", line)
    line = re.sub("[0-9]{1,4}路", "", line)
    line = re.sub("[0-9]{2}:[0-9]{2}", "", line)
    line = re.sub("[0-9]{2}：[0-9]{2}", "", line)
    line = re.sub("[0-9]", "", line)
    line = re.sub("[\s+\.\!\/_,$%^*()?;；:-【】+\"\']+|[+——！，;:。？、~@#￥%……&*（）〔〕㎡]+", "", line)
    line = re.sub("：", "", line)
    line = re.sub("-", "", line)
    line = re.sub("[上中下午晚上]{2}", "", line)
    line = re.sub("[一二三四五六七八九十两]{1,3}[点时]{1}", "", line)
    line = re.sub("[一二三四五六七八九十两]{1,3}[点时分]{1}", "", line)
    return line


def jgxl(detail, current_dep):
    if current_dep['tier'] == '1':
        jgxl_assign = []

        # 井盖判断
        if '无主井盖' in detail:
            for i in jg:
                jgxl_assign.append(i)

        # 线缆判断
        elif '线缆垂吊' in detail:
            for i in xl:
                jgxl_assign.append(i)
        # 如果出现了xl_uni中的单位，则走常规推送逻辑
        for i in xl_uni:
            if detail.find(i) != -1:
                jgxl_assign = []
        return jgxl_assign
    else:
        return None


def get_address(location, detail):
    # 地理信息粒度获取函数
    if location:
        address = []
        for j in mini_word:
            if location.find(j) != -1:
                address.append(j)
                location = re.sub(j, '#', location)

    else:
        address = []
        for j in mini_word:
            if detail.find(j) != -1:
                address.append(j)
                detail = re.sub(j, '#', detail)
    return address


def get_keywords(detail, current_dep):
    # 联动单位关键词获取函数
    key_words = []
    if current_dep['tier'] == '1':
        for key in tier2_keyword:
            if detail.find(key) != -1:
                key_words.append(key)
                detail = re.sub(key, '#', detail)

    elif current_dep['tier'] == '2':
        for key in tier3_keyword:
            if detail.find(key) != -1:
                key_words.append(key)
                detail = re.sub(key, '#', detail)

    elif current_dep['tier'] == '3':
        for key in tier4_keyword:
            if detail.find(key) != -1:
                key_words.append(key)
                detail = re.sub(key, '#', detail)

    return key_words


def get_grid(probs, current_dep):
    # 网格中心概率计算函数

    # Initialization     grid_prob-dic{id+name: prob for each word}
    #                    dep_count-dic{id+name: number of key word with prob > 0.8}
    #                    next_grid_list-list[best_grid,...]
    grid_prob = {}
    dep_count = {}
    next_grid_list = []

    # extract grid with respect to max prob
    for i in probs:
        max_value = i.max()
        max_dep = i.idxmax()

        if max_dep not in grid_prob:
            grid_prob[max_dep] = [max_value]
        else:
            grid_prob[max_dep].append(max_value)
        dep_count[max_dep] = []

    # assign dep tp dep_count if prob > 0.8
    for i in grid_prob:
        for p in grid_prob[i]:
            if p >= 0.8:
                dep_count[i].append(p)

    # normal step, execute when dep_count has values
    if len(dep_count) >= 1:
        for i in dep_count:
            best_grid = {}
            if len(dep_count[i]) >= 1:
                dep_count[i] = sum(dep_count[i]) / len(dep_count[i])
                if dep_count[i] > 0.6:
                    best_grid['possibility'] = dep_count[i]
                    best_grid['id'] = i.split(',')[0]
                    best_grid['name'] = i.split(',')[1]
                    if current_dep['tier'] == '1':
                        best_grid['tier'] = '2'
                        next_grid_list.append(best_grid)
                    elif current_dep['tier'] == '2':
                        best_grid['tier'] = '3'
                        next_grid_list.append(best_grid)
                    elif current_dep['tier'] == '3':
                        best_grid['tier'] = '4'
                        next_grid_list.append(best_grid)

    # when normal dep process returns nothing in next_grid_list, execute mode algorithm
    if not next_grid_list:
        mode = 0
        mode_prob = 0
        best_grid = {}
        for i in grid_prob:
            if len(grid_prob[i]) >= mode:
                mode = len(grid_prob[i])
                if sum(grid_prob[i]) / mode > mode_prob:
                    mode_prob = sum(grid_prob[i]) / mode
                    best_grid['possibility'] = 1
                    best_grid['id'] = i.split(',')[0]
                    best_grid['name'] = i.split(',')[1]
                    if current_dep['tier'] == '1':
                        best_grid['tier'] = '2'
                        next_grid_list.append(best_grid)
                    elif current_dep['tier'] == '2':
                        best_grid['tier'] = '3'
                        next_grid_list.append(best_grid)
                    elif current_dep['tier'] == '3':
                        best_grid['tier'] = '4'
                        next_grid_list.append(best_grid)
    return next_grid_list


def get_linkunit(prob, current_dep):
    # 联动单位概率推荐函数
    dep_prob = {}
    next_unit_list = []
    dep_50 = {}

    # 从所有关键词的概率中找出最大的一项所对应的部门
    for i in prob:
        max_value = i.max()
        max_dep = i.idxmax()

        if max_dep not in dep_prob:
            dep_prob[max_dep] = [max_value]
        else:
            dep_prob[max_dep].append(max_value)
        dep_50[max_dep] = []

    # 筛选出所有大于0.5的概率
    for i in dep_prob:
        for p in dep_prob[i]:
            if p >= 0.5:
                dep_50[i].append(p)

    # 对所有大于0.5的概率求平均值,找出均值大于0.618（黄金分割率）的部门并委派
    for i in dep_50:
        best_dep = {}
        if len(dep_50[i]) >= 1:
            dep_50[i] = sum(dep_50[i]) / len(dep_50[i])
            if dep_50[i] > 0.618:
                best_dep['possibility'] = dep_50[i]
                best_dep['id'] = i.split(',')[0]
                best_dep['name'] = i.split(',')[1]
                if current_dep['tier'] == '1':
                    best_dep['tier'] = '2'
                    next_unit_list.append(best_dep)
                elif current_dep['tier'] == '2':
                    best_dep['tier'] = '3'
                    next_unit_list.append(best_dep)
                elif current_dep['tier'] == '3':
                    best_dep['tier'] = '4'
                    next_unit_list.append(best_dep)

    if next_unit_list == [] and current_dep['tier'] != '1':
        mode = 0
        best_dep = {}
        for i in dep_prob:
            if len(dep_prob[i]) > mode:
                next_unit_list = []
                mode = len(dep_prob[i])
                best_dep['possibility'] = 1
                best_dep['id'] = i.split(',')[0]
                best_dep['name'] = i.split(',')[1]
                if current_dep['tier'] == '1':
                    best_dep['tier'] = '2'
                    next_unit_list.append(best_dep)
                if current_dep['tier'] == '2':
                    best_dep['tier'] = '3'
                    next_unit_list.append(best_dep)
                if current_dep['tier'] == '3':
                    best_dep['tier'] = '4'
                    next_unit_list.append(best_dep)

    return next_unit_list


def next_grid(address, current_dep):
    if current_dep['tier'] == '1':
        probs = []
        # 获得位置粒度对应二级网格中心概率
        for loc in address:
            try:
                p = tier2_grids.loc[loc, :]  # 此时p为series
                probs.append(p)
            except BaseException as error:
                pass
        return_grid = get_grid(probs, current_dep)
        return return_grid

        # tier2推送tier3
    elif current_dep['tier'] == '2':
        probs = []
        # 当前处置部门下属网格中心位置粒度概率表
        current_grid = current_dep['id'] + ',' + current_dep['name']
        sub_grid = tier3_grid[current_grid]
        all_tier3 = tier3_grids.columns.tolist()
        no_use_tier3 = [x for x in all_tier3 if x not in sub_grid]
        tier3_grids_sub = tier3_grids.drop(no_use_tier3, axis=1)

        for loc in address:
            try:
                p = tier3_grids_sub.loc[loc, :]
                probs.append(p)
            except:
                pass
        return_grid = get_grid(probs, current_dep)
        return return_grid


def next_linkunit(key_words, current_dep):
    if current_dep['tier'] == '1':
        # 获得二级联动单位推荐概率
        prob2 = []
        for keys in key_words:
            try:
                p = tier2_link_prob.loc[keys, :]
                prob2.append(p)
            except:
                pass
        return_linkunit = get_linkunit(prob2, current_dep)
        return return_linkunit

    elif current_dep['tier'] == '2':
        # 获得当前2级处置部门下属联动单位推荐概率表
        prob3 = []
        current_unit = current_dep['id'] + ',' + current_dep['name']
        sub_unit3 = link_unit2[current_unit]
        all_unit3 = tier3_link_prob.columns.tolist()
        no_use_units3 = [x for x in all_unit3 if x not in sub_unit3]
        tier3_unit_sub = tier3_link_prob.drop(no_use_units3, axis=1)
        # 获得关键词推荐概率
        for keys in key_words:
            try:
                p = tier3_unit_sub.loc[keys, :]
                prob3.append(p)
            except:
                pass
        return_linkunit = get_linkunit(prob3, current_dep)
        return return_linkunit

    elif current_dep['tier'] == '3':
        # 获得当前3级处置部门下属联动单位推荐概率表
        prob4 = []
        current_unit = current_dep['id'] + ',' + current_dep['name']
        sub_unit4 = link_unit3[current_unit]
        all_unit4 = tier4_link_prob.columns.tolist()
        no_use_units4 = [x for x in all_unit4 if x not in sub_unit4]
        tier4_unit_sub = tier4_link_prob.drop(no_use_units4, axis=1)

        # 获得关键词推荐概率
        for keys in key_words:
            try:
                p = tier4_unit_sub.loc[keys, :]
                prob4.append(p)
            except:
                pass
        return_linkunit = get_linkunit(prob4, current_dep)
        return return_linkunit


def predict_tier3(predict_prob, lbl):
    result = []
    prob_list = []
    for p in predict_prob[0]:
        prob_list.append(p)

    s = []
    for i in range(len(prob_list)-1):
        s.append((i, prob_list[i]))
    s.sort(key=lambda x: x[1], reverse=True)

    deps = [
            (lbl.inverse_transform(s[0][0]), s[0][1]),
            (lbl.inverse_transform(s[1][0]), s[1][1]),
            (lbl.inverse_transform(s[2][0]), s[2][1])
    ]

    for d in deps:
        tier3_result = {}
        if d[0] in grid_3_dic:
            tier3_result['id'] = grid_3_dic[d[0]]
            tier3_result['name'] = d[0]
            tier3_result['possibility'] = d[1]
            result.append(tier3_result)
    return result


def model_predict(detail, current_dep):
    district_name = current_dep['name']
    detail = clean(detail)
    detail = dist_sub(detail)
    detail = mates(ls, detail)
    result = []
    if district_name == '云岩区':
        vec = yunyan_vec.transform([detail])
        tfidf = yunyan_tfidf.transform(vec)
        predict = yunyan_rf.predict_proba(vec)
        result = predict_tier3(predict, yunyan_lbl)

    elif district_name == '南明区':
        vec = nanming_vec.transform([detail])
        tfidf = nanming_tfidf.transform(vec)
        predict = nanming_rf.predict_proba(vec)
        result = predict_tier3(predict, nanming_lbl)

    elif district_name == '白云区':
        vec = baiyun_vec.transform([detail])
        tfidf = baiyun_tfidf.transform(vec)
        predict = baiyun_rf.predict_proba(vec)
        result = predict_tier3(predict, baiyun_lbl)

    elif district_name == '花溪区':
        vec = huaxi_vec.transform([detail])
        tfidf = huaxi_tfidf.transform(vec)
        predict = huaxi_rf.predict_proba(vec)
        result = predict_tier3(predict, huaxi_lbl)

    elif district_name == '乌当区':
        vec = wudang_vec.transform([detail])
        tfidf = wudang_tfidf.transform(vec)
        predict = wudang_rf.predict_proba(vec)
        result = predict_tier3(predict, wudang_lbl)

    elif district_name == '观山湖区':
        vec = guanshanhu_vec.transform([detail])
        tfidf = guanshanhu_tfidf.transform(vec)
        predict = guanshanhu_rf.predict_proba(vec)
        result = predict_tier3(predict, guanshanhu_lbl)

    elif district_name == '清镇市':
        vec = qingzhen_vec.transform([detail])
        tfidf = qingzhen_tfidf.transform(vec)
        predict = qingzhen_rf.predict_proba(vec)
        result = predict_tier3(predict, qingzhen_lbl)

    elif district_name == '息烽县':
        vec = xifeng_vec.transform([detail])
        tfidf = xifeng_tfidf.transform(vec)
        predict = xifeng_rf.predict_proba(vec)
        result = predict_tier3(predict, xifeng_lbl)

    elif district_name == '开阳县':
        vec = kaiyang_vec.transform([detail])
        tfidf = kaiyang_tfidf.transform(vec)
        predict = kaiyang_rf.predict_proba(vec)
        result = predict_tier3(predict, kaiyang_lbl)

    elif district_name == '修文县':
        vec = xiuwen_vec.transform([detail])
        tfidf = xiuwen_tfidf.transform(vec)
        predict = xiuwen_rf.predict_proba(vec)
        result = predict_tier3(predict, xiuwen_lbl)

    return result


def grid_center(case_id, location, case_type, detail, linkage_unit_list):
    current_dep = {}
    next_deps = []
    if not linkage_unit_list:
        current_dep = {
            "id": "5154297156650094256",
            "tier": "1",
            "name": "贵阳市"
        }
    else:
        for dic in linkage_unit_list:
            if (current_dep and int(dic['tier']) > int(current_dep['tier'])) or current_dep == {}:
                current_dep = dic

    # 二级网格->三级部门推荐算法
    if current_dep['tier'] == '2' and current_dep['name'] in districts:
        next_tier3 = model_predict(detail, current_dep)
        next_deps += next_tier3

    else:

        address = get_address(location, detail)

        try:
            next_grid_assign = next_grid(address, current_dep)
            next_deps += next_grid_assign
        except:
            pass

        next_jgxl = jgxl(detail, current_dep)
        if not next_jgxl:
            key_words = get_keywords(detail, current_dep)
            try:
                next_linkunit_assign = next_linkunit(key_words, current_dep)
                next_deps += next_linkunit_assign
            except:
                pass

        else:
            jgxl_list = []
            for i in next_jgxl:
                jgxl_dic = {'id': i.split(',')[0], 'name': i.split(',')[1], 'tier': '2', 'possibility': 1}
                jgxl_list.append(jgxl_dic)
            for i in jgxl_list:
                next_deps.append(i)

    return next_deps


if __name__ == '__main__':
    link_unit_list = [
        {
            "id": "74529609387101585", "tier": "2", "name": "云岩区"
        }
    ]
    result = grid_center('12345', '', 'xxx', '云岩区北京路有垃圾', [{"id": "74529609387101585", "name": "云岩区", "possibility": 1.0, "tier": "2"}])
    print(result)














