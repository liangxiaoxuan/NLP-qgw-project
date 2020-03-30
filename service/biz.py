import functools
import json
import re
import time

import jieba
import jieba.posseg as pseg
from apscheduler.schedulers.background import BackgroundScheduler
from sklearn.externals import joblib
from sqlalchemy import func

from qgw_autoflow.common.data_cleansing import get_type
from qgw_autoflow.common.logger import MyLog
from qgw_autoflow.common.resource import (COMMUNITIES_VILLAGES_FILE,
                                          DISTRICT_COUNTY_FILE,
                                          JIEBA_SYS_STUDY_DICT_FILE,
                                          JIEBA_USER_DICT_FILE,
                                          JIEBA_USER_DICT_STOP_WORDS_FILE,
                                          STREETS_TOWNSHIPS_TOWNS_FILE,
                                          TYPE_SET_FILE, TYPE_TFIDF_FILE,
                                          TYPE_VEC_FILE)
from qgw_autoflow.dao.model import (AlgorithmAssignHistory,
                                    AlgorithmAssignNextHistory,
                                    AlgorithmCaseType, AlgorithmTypeHistory,
                                    AlgorithmUnitWeight, CaseFinished,
                                    CaseFinishedUnit, VisualCategory,
                                    NewCaseFinished, VisualDepart,
                                    OrgUnitPossibility, db_session, load_session, CaseRepo, CaseAssignTier)

jieba.load_userdict(JIEBA_USER_DICT_FILE)
jieba.load_userdict(JIEBA_SYS_STUDY_DICT_FILE)

# 停顿词
STOP_WORDS = set([])
with open(JIEBA_USER_DICT_STOP_WORDS_FILE, 'r', encoding='utf-8') as stop_word_f:
    for row in stop_word_f.readlines():
        STOP_WORDS.add(row.strip())

scheduler = BackgroundScheduler()


@scheduler.scheduled_job("cron", minute='*')
def some_decorated_task():
    s = time.strftime("%Y-%m-%d %X", time.localtime(time.time()))
    print("I am printed at %s on the last Sunday of every month!" % s)


def get_category_id(name, type_name, parent_id=None):
    """
    根据类别名称获取类别编号
    :param name: 类别名称
    :param type_name: 类别类型，只有bigCat,smallCat,threeCat,infoCat
    :param parent_id: 上级类别的id，大类的是None(null)
    :return:如果找到类别返回该类别的id,没有找到返回None(null)
    """
    session = db_session
    category = session.query(VisualCategory).filter(VisualCategory.category_name == name, VisualCategory.type == type_name, VisualCategory.parent_id == parent_id).first()
    if category is None:
        return None
    else:
        return category.category_id


def get_category_name(id):
    """
    感觉类别编号获取名称
    :param id:
    :return:
    """
    session = db_session
    category = session.query(VisualCategory).filter(VisualCategory.category_id == id).first()
    if category is None:
        return None
    else:
        return category.category_name


def get_depart_by_id(unit_id):
    """
    根据单位编号获取单位信息
    :param unit_id:
    :return:
    """
    session = db_session
    depart = session.query(VisualDepart).filter(VisualDepart.unit_id == unit_id).first()
    if depart is None:
        return None
    else:
        return depart


# scheduler.start()


def deal_new_finished_case():
    """

    :return:
    """
    session = load_session()
    c_f_list = session.query(NewCaseFinished).filter(
        NewCaseFinished.deal_status.is_(False)
    ).all()
    print(len(c_f_list))
    default_unit = session.query(VisualDepart).filter(
        VisualDepart.tier == 1,
        VisualDepart.unit_name == '贵阳市',
    ).first()
    error_flag = False
    for x in c_f_list:
        if x.case_type != '' and x.case_type != '##':
            type_history = session.query(AlgorithmTypeHistory).filter(
                AlgorithmTypeHistory.case_id == x.case_id
            ).order_by(-AlgorithmTypeHistory.create_time).first()
            if type_history:
                type_name = get_type(type_history.bigcat_id, type_history.smallcat_id,
                                     type_history.threecat_id, '').replace('.', '#')
                if type_name == x.case_type:
                    type_history.real_type_name = x.case_type
                    type_history.equal_flag = True
                else:
                    type_history.real_type_name = x.case_type
                    type_history.equal_flag = False
                session.add(type_history)
            unit_id_list = []

            for y in x.units:
                unit_id_list.append(y.unit_id)

            if default_unit.unit_id not in unit_id_list:
                unit_id_list.append(default_unit.unit_id)
            n = len(unit_id_list)
            if n > 1:
                unit_list = session.query(VisualDepart).filter(
                    VisualDepart.unit_id.in_(unit_id_list)
                ).all()

                if len(unit_list) != n:
                    # MyLog.get_log().error('有的id找不到%s' % ','.join(unit_id_list))
                    print('有的id找不到%s' % ','.join(unit_id_list))
                    error_flag = True
                else:
                    unit_list.sort()
                    unit_list.reverse()
                    l = []
                    for i in range(len(unit_list)):
                        if unit_list[i].tier == i + 1:
                            if i >= 1:
                                l.append((unit_list[i - 1], unit_list[i]))
                        else:
                            # MyLog.get_log().error('不是连续的%s' % ','.join(unit_id_list))
                            print('不是连续的%s' % ','.join(unit_id_list))
                            error_flag = True
                            break
                        i += 1
                    if error_flag is False:
                        for y, unit_next in l:
                            a_a_h = session.query(AlgorithmAssignHistory).filter(
                                AlgorithmAssignHistory.case_id == x.case_id,
                                AlgorithmAssignHistory.unit_id == y.id,
                                AlgorithmAssignHistory.tier == y.tier
                            ).order_by(AlgorithmAssignHistory.create_time).first()
                            if a_a_h:
                                a_a_h.real_id = unit_next.id
                                if a_a_h.real_id in a_a_h.next_units:
                                    a_a_h.equal_flag = True
                                else:
                                    a_a_h.equal_flag = False
                                session.add(a_a_h)

        else:
            pass
        x.deal_status = True
        session.add(x)
    session.commit()
    session.close()


def deal_finished_case():
    session = load_session()
    # try:
    pass
    result = session.query(CaseFinished).filter(
        CaseFinished.study_status == 0
    ).all()
    for x in result:
        print(repr(x.case_info))
        s = x.case_info.replace('\n', '').replace('\t', '').encode('utf-8')
        data_dict = json.loads(s)
        case_id = data_dict['case_id']
        case_type = data_dict['case_type']
        if case_type != '' and case_type != '##':
            type_history_list = session.query(AlgorithmTypeHistory).filter(
                AlgorithmTypeHistory.case_id == case_id
            ).order_by(-AlgorithmTypeHistory.create_time).all()
            n = len(type_history_list)
            if n > 0:
                type_history = type_history_list[0]
                type_name = get_type(type_history.bigcat_id, type_history.smallcat_id,
                                     type_history.threecat_id, type_history.infocat_id).replace('.', '#')
                if type_name == case_type:
                    type_history.equal_flag = True

                else:
                    type_history.equal_flag = False
                session.add(type_history)

    session.commit()
    session.close()
    # except:
    #     session.rollback()
    # finally:
    #     session.close()


def run_time(func):
    @functools.wraps(func)
    def wrapper(*args, **kw):

        begin = time.time()
        result = func(*args, **kw)
        end = time.time()
        deal_time = end - begin
        # print('call %s(): %10f' % (func.__name__, end - begin))
        if func.__name__ == 'get_case_type':
            case_id = args[0]
            session = db_session
            try:
                bigcat_id = ''
                smallcat_id = ''
                threecat_id = ''
                infocat_id = ''
                for x in result:
                    if x.type == 'bigCat':
                        bigcat_id = x.category_id
                    elif x.type == 'smallCat':
                        smallcat_id = x.category_id
                    elif x.type == 'threeCat':
                        threecat_id = x.category_id
                    elif x.type == 'infoCat':
                        infocat_id = x.category_id
                type_history = AlgorithmTypeHistory(case_id, bigcat_id, smallcat_id, threecat_id, infocat_id, deal_time)
                session.add(type_history)
                session.commit()

                save_repo_assign_type(args, bigcat_id, case_id, deal_time, infocat_id, smallcat_id, threecat_id)

            except IOError:
                session.rollback()
                # finally:
                #     session.close()

        elif func.__name__ == 'get_case_assign':
            case_id = args[0]
            linkage_unit_list = args[4]
            session = db_session
            try:
                if result[1] == '':
                    length = len(linkage_unit_list)
                    # 初始化为贵阳市的unit
                    unit = session.query(VisualDepart).filter(VisualDepart.unit_id == '5154297156650094256').first()
                    if length == 0:
                        pass
                    else:
                        units = session.query(VisualDepart).filter(VisualDepart.unit_id.in_([x['id'] for x in linkage_unit_list])).order_by(-VisualDepart.tier).all()
                        if units:
                            unit = units[0]

                    assign = AlgorithmAssignHistory(case_id, unit.id, unit.tier, deal_time)
                    i = 0
                    for x in result[0]:
                        assign_next = AlgorithmAssignNextHistory(x.org_unit.unit_id, i)
                        i += 1
                        assign.next_units.append(assign_next)
                        session.add(assign_next)
                    session.add(assign)
                    session.commit()

                    save_repo_assign_depart(args, case_id, deal_time, linkage_unit_list)

                else:
                    pass

            except IOError:
                session.rollback()
            finally:
                session.remove()
        return result

    return wrapper


def save_repo_assign_type(args, bigcat_id, case_id, deal_time, infocat_id, smallcat_id, threecat_id):
    session = db_session
    case_repo = session.query(CaseRepo).filter(CaseRepo.case_id == case_id).first()
    if case_repo is None:
        case_repo = CaseRepo()
    case_repo.case_id = case_id
    case_repo.detail = args[1]
    case_repo.location = args[2]
    case_repo.assign_category_big = bigcat_id
    case_repo.assign_category_small = smallcat_id
    case_repo.assign_category_three = threecat_id
    case_repo.assign_category_info = infocat_id

    # 如果是空字符串则置null
    if case_repo.assign_category_big == '':
        case_repo.assign_category_big = None
    if case_repo.assign_category_small == '':
        case_repo.assign_category_small = None
    if case_repo.assign_category_three == '':
        case_repo.assign_category_three = None
    if case_repo.assign_category_info == '':
        case_repo.assign_category_info = None
    case_repo.deal_category_time = deal_time
    case_repo.assign_category_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    case_repo.update_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    session.add(case_repo)
    session.commit()
    session.close()


def save_repo_assign_depart(args, deal_time, linkage_unit_list):
    """
    保存案件分派的信息,先删除同级的分派部门，然后在添加同级的分派部门
    :param args:依次是 案件编号，案件类别（#分割），案发地址，案件描述
    :param deal_time:处理时间
    :param linkage_unit_list:分派的单位
    :return:
    """
    session = db_session
    case_repo = session.query(CaseRepo).filter(CaseRepo.case_id == args[0]).first()
    if case_repo is None:
        case_repo = CaseRepo()
        case_repo.case_id = args[0]
        case_repo.location = args[2]
        case_repo.detail = args[3]

        category = args[1].split('#')
        if len(category) >= 1:
            case_repo.finish_category_big = get_category_id(category[0], type_name='bigCat')
        if len(category) >= 2:
            case_repo.finish_category_small = get_category_id(category[1], 'smallCat', case_repo.finish_category_big)
        if len(category) >= 3:
            case_repo.finish_category_three = get_category_id(category[2], 'threeCat', case_repo.finish_category_small)
        if len(category) >= 4:
            case_repo.finish_category_info = get_category_id(category[3], 'infoCat', case_repo.finish_category_three)

    session.add(case_repo)
    session.commit()
    # 删除原来的同级的部门
    current_tier = 0
    if len(linkage_unit_list) >= 0:
        current_tier = linkage_unit_list[0]['tier']

    if current_tier != 0:
        exist_departs = session.query(CaseAssignTier).filter(CaseAssignTier.case_repo_id == case_repo.id, CaseAssignTier.tier == current_tier).all()
        for u in exist_departs:
            session.delete(u)
        session.commit()

        for u in linkage_unit_list:
            ct = CaseAssignTier()
            ct.case_repo_id = case_repo.id
            ct.tier = u['tier']
            ct.depart_id = u['id']
            ct.depart_name = u['name']
            ct.possibility = float(u['possibility'])
            ct.assign_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            session.add(ct)
        session.commit()

    case_repo.deal_depart_time = deal_time
    case_repo.assign_depart_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    case_repo.update_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    session.add(case_repo)
    session.commit()
    session.close()


@run_time
def get_case_type(case_id: str, detail: str, location: str, vec, tfidf, clf, type_set: dict):
    """
    根据案件描述获取案件类别
    :param case_id:
    :param detail:
    :param location:
    :param vec:
    :param tfidf:
    :param clf:
    :param type_set:
    :return:
    """
    MyLog.get_log().info('get_case_type, detail: %s' % detail)
    # Jieba 分词
    detail_ns, detail_nv, detail_words = __seg_detail(detail)  # 地名词 所有词 带词性标注所有词
    # 回测类型
    test_data_featuress = vec.transform([' '.join(detail_nv)])
    test_data_tfidf = tfidf.transform(test_data_featuress)
    pred = clf.predict(test_data_tfidf)
    # 类型ID配置类型值（文本）
    type_value = __get_type(pred[0], type_set, detail)
    type_array = type_value.split('.')
    case_type_list = []
    session = db_session
    try:
        for type_id in type_array:
            if type_id != '':
                case_type = session.query(VisualCategory).filter(VisualCategory.category_id == type_id).first()
                if case_type:
                    case_type_list.append(case_type)
        if len(case_type_list) == 0:
            default_type = ['2016073647', '2016073656', '2016073688']
            for type_id in default_type:
                case_type = session.query(VisualCategory).filter(VisualCategory.category_id == type_id).first()
                case_type_list.append(case_type)
    finally:
        session.remove()
    return case_type_list


# 获取案件指派部门（单位）
@run_time
def get_case_assign(case_id: str, case_type: str, location: str, detail: str, linkage_unit_list, n=5):
    """

    :param case_id:
    :param case_type:
    :param location:
    :param detail:
    :param linkage_unit_list:
    :param n:
    :return:
    """
    MyLog.get_log().info('get_case_assign case_id: %s case_type: %s location: %s')
    unit_weight_list = []
    # 格式化Type分割符
    case_type = case_type.replace('#', '.')
    result = []
    max_tier = 1
    session = db_session
    message = ''
    try:
        length = len(linkage_unit_list)
        # 初始化为贵阳市的unit
        unit = session.query(VisualDepart).filter(VisualDepart.unit_id == '5154297156650094256').first()

        if length == 0:
            # 地名词分词
            # location_ns, location_nv, location_words = __seg_detail(location)
            pass
        elif length == 1:
            try:
                max_tier = int(linkage_unit_list[0]['tier'])
            except ValueError:
                message += '请输入正确的tier！\n'
            unit = session.query(VisualDepart).filter(VisualDepart.unit_id == linkage_unit_list[0]['id']).first()

        else:
            max_tier_unit = linkage_unit_list[0]
            for i in range(length - 1):
                for j in range(i + 1, length):
                    if linkage_unit_list[i]['tier'] < linkage_unit_list[j]['tier']:
                        max_tier_unit = linkage_unit_list[j]
            try:
                max_tier = int(max_tier_unit['tier'])
            except ValueError:
                message += '请输入正确的tier！\n'
            unit = session.query(VisualDepart).filter(VisualDepart.unit_id == max_tier_unit['id']).first()

        if unit and message == '':
            l = []
            auw_list = session.query(AlgorithmUnitWeight).filter(
                AlgorithmUnitWeight.next_id == VisualDepart.unit_id,
                VisualDepart.tier == max_tier + 1,
                AlgorithmUnitWeight.type_name == case_type,
                AlgorithmUnitWeight.unit_name == unit.unit_name,
            ).all()
            location_ns, location_nv, location_words = __seg_detail(location)
            for auw in auw_list:
                weight = 0
                for auwl in auw.locations:
                    if auwl.name in location_ns:
                        weight += auwl.user_weight

                l.append([auw, weight])

            l.sort(key=lambda temp: temp[1], reverse=True)
            l_n = len(l)
            total = 0
            for i in range(l_n):
                l[i][1] += 0.1
                total += l[i][1]
            for i in range(l_n):
                l[i][1] /= total

            if l_n <= n:
                for x, y in l:
                    org_unit = session.query(VisualDepart).filter(VisualDepart.unit_id == x.next_id).first()
                    org_unit_possibility = OrgUnitPossibility(org_unit, y)
                    result.append(org_unit_possibility)
            else:
                for i in range(n):
                    org_unit = session.query(VisualDepart).filter(VisualDepart.unit_id == l[i][0].next_id).first()
                    org_unit_possibility = OrgUnitPossibility(org_unit, l[i][1])
                    result.append(org_unit_possibility)
        elif message == '':
            message += '请输入正确的部门id\n'

    finally:
        pass
        session.remove()
    return result, message


def get_words(detail, case_type, n=2):
    detail_ns, detail_nv, detail_words = __seg_detail(detail)  # 地名词 所有词 带词性标注所有词
    vec = joblib.load(TYPE_VEC_FILE)
    tfidf = joblib.load(TYPE_TFIDF_FILE)
    test_data_featuress = vec.transform([' '.join(detail_nv)])
    test_data_tfidf = tfidf.transform(test_data_featuress)
    names = vec.inverse_transform(test_data_tfidf)
    l = [(names[0][i], test_data_tfidf.data[i]) for i in range(len(names[0]))]
    l.sort(key=lambda temp: temp[1], reverse=True)

    # 过滤数字和地名
    result_list = []
    district_county = []
    streets_townships_towns = []
    communities_villages = []
    with open(DISTRICT_COUNTY_FILE, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            district_county.append(line.strip())

    with open(STREETS_TOWNSHIPS_TOWNS_FILE, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            streets_townships_towns.append(line.strip())

    with open(COMMUNITIES_VILLAGES_FILE, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            communities_villages.append(line.strip())
    for x in l:
        if x[0] in district_county or x[0] in streets_townships_towns or x[0] in communities_villages:
            pass
        elif x[0].isdigit():
            pass
        else:
            result_list.append(x)
    # print(l)
    l_n = len(result_list)
    if l_n <= n:
        result = result_list
    else:
        result = result_list[:n]
    return result


def get_word(detail, case_type):
    session = db_session
    try:
        result_list = session.query(AlgorithmCaseType).filter(
            AlgorithmCaseType.type_name == case_type).all()
        n = len(result_list)
        result = case_type.split('#')[-1]
        result = result.replace('/', '或')

        if n > 0:
            for x in result_list[0].key_words:
                if x.key_word in detail:
                    result = x.show_word
    finally:
        pass
        # session.close()
    # print(result)
    return result


def finish_case(case_info, new_case_finished, linkage_unit_list):
    """

    :param case_info:
    :return:
    """
    MyLog.get_log().info(case_info)
    session = db_session
    try:
        session.add(CaseFinished(case_info))
        n_c_f = session.query(NewCaseFinished).filter(
            NewCaseFinished.case_id == new_case_finished.case_id,
            NewCaseFinished.study_status == 0,
            NewCaseFinished.deal_status == False
        ).first()
        if n_c_f:
            n_c_f.case_id = new_case_finished.case_id
            n_c_f.case_type = new_case_finished.case_type
            n_c_f.detail = new_case_finished.detail
            n_c_f.location = new_case_finished.location
            n_c_f.longitude = new_case_finished.longitude
            n_c_f.latitude = new_case_finished.latitude
            n_c_f.finished_time = new_case_finished.finished_time
            n_units = len(n_c_f.units)
            for x in linkage_unit_list:
                try:
                    tier = int(x['tier'])
                except ValueError:
                    tier = None
                if n_units == 0:
                    unit = CaseFinishedUnit(x['id'], tier, x['name'])
                    n_c_f.units.append(unit)
                    session.add(unit)
                    continue

                isFind = False
                for i in range(n_units):
                    if n_c_f.units[i].tier == tier and x['id'] == n_c_f.units[i].unit_id:
                        isFind = True
                        break
                if isFind:
                    n_c_f.units[i].unit_name = x['name']
                    n_c_f.units[i].tier = tier
                    session.add(n_c_f.units[i])
                else:
                    unit = CaseFinishedUnit(x['id'], tier, x['name'])
                    n_c_f.units.append(unit)
                    session.add(unit)

            session.add(n_c_f)
        else:
            n_c_f = new_case_finished
            for x in linkage_unit_list:
                try:
                    tier = int(x['tier'])
                except ValueError:
                    tier = None
                unit = CaseFinishedUnit(x['id'], tier, x['name'])
                new_case_finished.units.append(unit)
                session.add(unit)
            session.add(n_c_f)
        session.commit()
    except ValueError:
        session.rollback()
    finally:
        session.remove()


def get_avg_deal_time():
    session = db_session
    avg = 0
    message = ''
    # try:
    #     case_id_list = session.query(AlgorithmTypeHistory.case_id).join(
    #         AlgorithmAssignHistory, AlgorithmTypeHistory.case_id == AlgorithmAssignHistory.case_id
    #     ).filter(
    #         AlgorithmAssignHistory.tier == 1
    #     ).group_by(
    #         AlgorithmTypeHistory.case_id
    #     ).all()
    #
    #     l = []
    #     for case_id in case_id_list:
    #         type_history = session.query(AlgorithmTypeHistory).filter(
    #             AlgorithmTypeHistory.case_id == case_id[0],
    #         ).order_by(
    #             AlgorithmTypeHistory.create_time.desc()
    #         ).first()
    #         assign_history = session.query(AlgorithmAssignHistory).filter(
    #             AlgorithmAssignHistory.case_id == case_id[0],
    #         ).order_by(
    #             AlgorithmAssignHistory.create_time.desc()
    #         ).first()
    #         if type_history and assign_history:
    #             l.append(type_history.deal_time + assign_history.deal_time)
    #
    #     if len(l) == 0:
    #         message = '没有有用的数据。\n'
    #     else:
    #         avg = sum(l) / len(l)
    # except IOError:
    #     message = '数据库操作报错！\n'
    # finally:
    #     session.remove()
    try:
        type_history_result = session.query(func.avg(AlgorithmTypeHistory.deal_time)).first()
        assign_history_result = session.query(func.avg(AlgorithmAssignHistory.deal_time)).first()
        if type_history_result is None or assign_history_result is None:
            raise IOError
        avg = type_history_result[0] + assign_history_result[0]
    except IOError:
        message = '数据库操作报错'
    return avg, message


# 分词
def __seg_detail(detail: str) -> tuple:
    # 正则去垃圾数据
    detail = __detail_format(detail)

    show_words = []
    ns_words = []
    nv_words = []
    words = pseg.cut(detail)
    for w in words:
        show_words.append('%s %s' % (w.word, w.flag))
        if w.word in STOP_WORDS:
            continue
        if w.flag in ["ns"]:
            ns_words.append(w.word)
        # nv 存放所有词
        nv_words.append(w.word)
    return ns_words, nv_words, show_words


# 清除垃圾数据
def __detail_format(detail: str) -> str:
    detail = detail.replace('（', '(').replace('）', ')')
    detail_re = re.compile(r'【.*】')
    detail = detail_re.sub('', detail)
    detail_re = re.compile(r'\(.*\)')
    detail = detail_re.sub('', detail)
    # 处理特殊字符
    detail_re = re.compile(r'[☆▲●【】，。,:：-]')
    detail = detail_re.sub('', detail)
    return detail


# 根据id获取类别
def __get_type(pred: int, type_set: dict, detail) -> str:
    # LearnLog.AddLog('Id is %s' % pred)
    type_value = '2016073647.2016073656..'
    if pred != 0:
        try:
            type_value = str(type_set[pred])
        except ValueError as ex:
            # LearnLog.AddLog('return default v %s' % ex.args)
            type_value = '2016073647.2016073656..'
    if type_value == '2016073647.2016073657..':
        type_value = '2016073647.2016073657.-3481384730160312900'

    # 2016072800城市管理2016073089市政设施2016073106市政排水设施 #2016073308下水道
    if type_value == '2016072800.2016073089.2016073106.':
        if '下水道' in detail:
            type_value = '2016072800.2016073089.2016073106.2016073308'

    # 2016072800城市管理2016073089市政设施2016073105市政照明设施 #2016073299路灯
    if type_value == '2016072800.2016073089.2016073105.':
        if '路灯' in detail:
            type_value = '2016072800.2016073089.2016073105.2016073299'

    # 2016073087城市设施2016073088基础设施2016073101供水 #2016073259停水 and #2016073233供水管道
    if type_value == '2016073087.2016073088.2016073101.':
        if '停水' in detail:
            type_value = '2016073087.2016073088.2016073101.2016073259'
        elif '自来水管' in detail or '水阀' in detail or '水管' in detail:
            type_value = '2016073087.2016073088.2016073101.2016073233'

    # 2016073087城市设施2016073088基础设施2016073099供电 #2016073225停电 and #2016073221电缆
    if type_value == '2016073087.2016073088.2016073099.':
        if '停电' in detail:
            type_value = '2016073087.2016073088.2016073099.2016073225'
        elif '高压线' in detail or '电线' in detail:
            type_value = '2016073087.2016073088.2016073099.2016073221'

    # 2016072800城市管理2017031303噪音污染2016073524建筑施工噪音 #2016073552施工扰民
    if type_value == '2016072800.2017031303.2016073524.':
        if '施工扰民' in detail or '施工' in detail:
            type_value = '2016072800.2017031303.2016073524.2016073552'

    # 2016072800城市管理2016073089市政设施2016073106市政排水设施 #2016073308下水道
    if type_value == '2016072800.2016073089.2016073106.':
        if '下水道' in detail:
            type_value = '2016072800.2016073089.2016073106.#2016073308'

    # 2016072800城市管理2017031303噪音污染2016073525社会生活噪音 #2016073557广场舞 and #2016073559喇叭叫卖 and #2016073564生活设备噪音
    if type_value == '2016072800.2017031303.2016073525.':
        if '广场舞' in detail:
            type_value = '2016072800.2017031303.2016073525.2016073557'
        elif '喇叭' in detail:
            type_value = '2016072800.2017031303.2016073525.2016073559'
        # 生活设备噪音关键词规则不明

    return type_value


# 加载类别信息
def load_type_set() -> dict:
    data_list = []
    with open(TYPE_SET_FILE, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            data_list.append(line.strip())

    type_set = data_list
    type_dict = {}
    for type_line in type_set:
        type_array = str(type_line).split('$')
        if len(type_array) == 2:
            type_dict[int(type_array[1])] = type_array[0]

    return type_dict


def back_train(detail, vec, tfidf, clf, type_set):
    case_type_list = get_case_type('', detail, '', vec, tfidf, clf, type_set)
    type_name = '#'.join([x.name for x in case_type_list])
    type_value = type_name.replace('#', '.')
    department_list = get_case_assign('', type_name, '', detail, [])
    return type_value, department_list


def main():
    # get_words(detail='市民来电反映该处有井盖遗失存在安全隐患请贵单位按照二环内井盖案卷处置时限在4小时内到现场核实并回复如超时未回复将会影响你部门的绩效考核请相关部及时处理', case_type=None)
    # get_deal_time()

    # scheduler.start()
    # while True:
    #     pass

    # get_word('举报人反映该处垃圾箱垃圾已满地上也有垃圾请相关职能部门及时'
    #          '处理(微信案件请附处理后图片拍摄角度须与原图片一致)', case_type='城市管理#市容环境#投诉/举报')
    # deal_finished_case()
    deal_new_finished_case()


if __name__ == '__main__':
    main()
