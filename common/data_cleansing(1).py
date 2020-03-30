import random
import re
import time

import jieba
import jieba.posseg as pseg
import xlrd
from sqlalchemy import func

from qgw_autoflow.common.resource import (ALL_NEW_DATA_FILE, CLASS_WEIGHT_FILE,
                                          COMMUNITIES_VILLAGES_FILE,
                                          DATA_TYPE_FILE, DATA_UNIT_FILE,
                                          DETAIL_TRAIN_FILE,
                                          DISTRICT_COUNTY_FILE,
                                          JIEBA_SYS_STUDY_DICT_FILE,
                                          JIEBA_USER_DICT_FILE,
                                          JIEBA_USER_DICT_STOP_WORDS_FILE,
                                          NEW_DATA_FILE, OLD_DATA_FILE,
                                          STREETS_TOWNSHIPS_TOWNS_FILE,
                                          TYPE_SET_FILE, TYPE_TRAIN_FILE)
from qgw_autoflow.dao.model import (AlgorithmCaseType, AlgorithmData,
                                    AlgorithmDataUnit, AlgorithmKeyWord,
                                    AlgorithmUnitWeight, AlgorithmUnitWeightLo,
                                    VisualCategory, VisualDepart, load_session)

jieba.load_userdict(JIEBA_USER_DICT_FILE)
jieba.load_userdict(JIEBA_SYS_STUDY_DICT_FILE)

STOP_WORDS = set([])
with open(JIEBA_USER_DICT_STOP_WORDS_FILE, 'r', encoding='utf-8') as f1:
    for row in f1.readlines():
        STOP_WORDS.add(row.strip())


def pretreat():
    id_list = []
    data_type_list = []
    data_unit_list = []
    with open(OLD_DATA_FILE, encoding='utf8') as f:
        for line in f.readlines():
            line = line.strip()
            # case_id, finished_time, location,\
            # detail, bigcat_id, smallcat_id, threecat_id, infocat_id,\
            # unit_id, name, tier\
            l = line.split('$')
            s_list = [l[i] for i in [0, 8, 9, 10]]
            data_unit_list.append('$'.join(s_list))
            if l[0] not in id_list:
                id_list.append(l[0])
                s = '$'.join(l[:8])
                data_type_list.append(s)

    with open(NEW_DATA_FILE, mode='r', encoding='utf-8') as f:
        for line in f.readlines():
            line = line.strip()
            # case_id, finished_time, location,\
            # detail, bigcat_id, smallcat_id, threecat_id, infocat_id,\
            # unit_id, name, tier\
            l = line.split('$')
            s_list = [l[i] for i in [0, 8, 9]]
            data_unit_list.append('$'.join(s_list))
            if l[0] not in id_list:
                id_list.append(l[0])
                s = '$'.join(l[:8])
                data_type_list.append(s)

    with open(DATA_TYPE_FILE, mode='w', encoding='utf8') as f:
        for x in data_type_list:
            f.write('%s\n' % x)

    with open(DATA_UNIT_FILE, mode='w', encoding='utf8') as f:
        for x in data_unit_list:
            f.write('%s\n' % x)


def pretreat_new_data_to_db():
    """
    将new_data文件写入数据库
    :return:
    """
    session = load_session()
    with open(NEW_DATA_FILE, mode='r', encoding='utf-8') as f:
        i = 0
        for line in f.readlines():
            line = line.strip()
            case_id, finished_time, location, \
            detail, bigcat_id, smallcat_id, threecat_id, infocat_id, \
            unit_id, type_, tier, weight = line.split('$')

            finished_time += ':00'

            algorithm_data = session.query(AlgorithmData).filter(
                AlgorithmData.case_id == case_id,
                AlgorithmData.detail == detail,
            ).first()
            if algorithm_data is None:
                algorithm_data = AlgorithmData(case_id, time.strptime(finished_time, "%Y/%m/%d %X"),
                                               location, detail, bigcat_id, smallcat_id, threecat_id, infocat_id,
                                               get_type(bigcat_id, smallcat_id, threecat_id, infocat_id),
                                               new_flag=True)
            result = get_unit_name(unit_id)
            if result:
                name, type_, tier = result
                algorithm_data_unit = AlgorithmDataUnit(case_id, unit_id, name, type_, tier)
                algorithm_data.units.append(algorithm_data_unit)
                session.add(algorithm_data)
                session.add(algorithm_data_unit)
            else:
                print("error:unit_id: %s" % unit_id)

            i += 1
            if i != 0 and i % 10000 == 0:
                session.commit()
    session.commit()
    session.close()


def pretreat_old_data_to_db():
    session = load_session()
    with open(OLD_DATA_FILE, mode='r', encoding='utf-8') as f:
        i = 0
        for line in f.readlines():
            line = line.strip()
            try:
                case_id, finished_time, location, \
                detail, bigcat_id, smallcat_id, threecat_id, infocat_id, \
                unit_id, type_, tier, weight = line.split('$')
            except ValueError:
                print(line)

            algorithm_data = session.query(AlgorithmData).filter(
                AlgorithmData.case_id == case_id).first()
            if algorithm_data is None:
                algorithm_data = AlgorithmData(case_id, time.strptime(finished_time, "%Y/%m/%d %X"),
                                               location, detail, bigcat_id, smallcat_id, threecat_id, infocat_id,
                                               get_type(bigcat_id, smallcat_id, threecat_id, infocat_id),
                                               new_flag=False)
            result = get_unit_name(unit_id)
            if result:
                name, type_, tier = result
                algorithm_data_unit = AlgorithmDataUnit(case_id, unit_id, name, type_, tier)
                algorithm_data.units.append(algorithm_data_unit)
                session.add(algorithm_data)
                session.add(algorithm_data_unit)
            else:
                print("error:unit_id: %s" % unit_id)

            i += 1
            if i != 0 and i % 10000 == 0:
                session.commit()
    session.commit()
    session.close()


def set_new_data_weight_to_db():
    session = load_session()
    ad_list = session.query(AlgorithmData).filter(
        AlgorithmData.new_flag.is_(True),
        AlgorithmData.id > 335239,
        AlgorithmData.bigcat_id != '',
        AlgorithmData.location != '',
    ).all()
    for ad in ad_list:
        ad.units.sort()
        unit_id_list = []
        tier_list = []
        l = []
        ll = []
        temp = None
        for unit in ad.units:
            if unit.unit_id not in unit_id_list:
                unit_id_list.append(unit.unit_id)
                l.append(unit)

        for unit in l:
            if unit.tier not in tier_list:
                tier_list.append(unit.tier)
                temp = [unit]
                ll.append(temp)
            else:
                ll[-1].append(unit)

        func_list = get_func(ll)
        location_ns, location_nv, location_words = __seg_detail(ad.location)
        i = 0
        for x, y in func_list:

            auw = session.query(AlgorithmUnitWeight).filter(
                AlgorithmUnitWeight.unit_id == x.unit_id,
                AlgorithmUnitWeight.next_id == y.unit_id,
            ).first()
            # x_org_unit = session.query(OrgUnit).get(x.unit_id)
            # y_org_unit = session.query(OrgUnit).get(y.unit_id)
            if auw:
                name_list = []
                for auwl_x in auw.locations:
                    name_list.append(auwl_x.name)
                for lc in set(location_ns):
                    if lc in name_list:
                        for auwl_x in auw.locations:
                            if auwl_x.name == lc:
                                auwl_x.default_weight += 1
                                auwl_x.user_weight = auwl_x.default_weight
                                session.merge(auwl_x)
                    else:
                        auwl = AlgorithmUnitWeightLo(
                            lc, 1, 1,
                        )
                        auw.locations.append(auwl)
                        session.add(auwl)
                        session.merge(auw)

            else:
                auw = AlgorithmUnitWeight(x.algorithm_data.bigcat_id, x.algorithm_data.smallcat_id,
                                          x.algorithm_data.threecat_id, x.algorithm_data.infocat_id,
                                          x.unit_id, x.tier, y.unit_id, x.algorithm_data.type_name, x.unit_name,
                                          y.unit_name)

                for lc in set(location_ns):
                    auwl = AlgorithmUnitWeightLo(
                        lc, 1, 1,
                    )
                    auw.locations.append(auwl)
                    session.add(auwl)
                session.add(auw)
            if i != 0 and i % 10000 == 0:
                print(i)
                session.commit()
    session.commit()
    session.close()


def get_func(ll):
    """
    给定一个三维列表，建立从上往下的映射关系
    :return:
    """
    n = len(ll)
    result = []
    if n == 0 or n == 1:
        pass

    else:
        for i in range(n - 1):
            for x in ll[i]:
                for y in ll[i + 1]:
                    result.append((x, y))

    return result


def get_type(bigcat_id, smallcat_id, threecat_id, infocat_id):
    """

    :param bigcat_id:
    :param smallcat_id:
    :param threecat_id:
    :param infocat_id:
    :return:
    """
    session = load_session()
    bigcat = session.query(VisualCategory).filter(VisualCategory.category_id == bigcat_id).first()
    smallcat = session.query(VisualCategory).filter(VisualCategory.category_id == smallcat_id).first()
    threecat = session.query(VisualCategory).filter(VisualCategory.category_id == threecat_id).first()
    infocat = session.query(VisualCategory).filter(VisualCategory.category_id == infocat_id).first()
    session.close()
    l = []
    if bigcat:
        l.append(bigcat.category_name)
        if smallcat:
            l.append(smallcat.category_name)
            if threecat:
                l.append(threecat.category_name)
                if infocat:
                    l.append(infocat.category_name)

    return ".".join(l)


def get_unit_name(unit_id):
    """

    :param unit_id:
    :return:
    """
    session = load_session()
    unit = session.query(VisualDepart).filter(VisualDepart.unit_id == unit_id).first()
    result = None
    if unit:
        result = (unit.unit_name, unit.type, unit.tier)
    session.close()
    return result


def handle_data(report_data_list):
    """构建类型训练数据并保存到文件"""
    # 随机打乱数据顺序
    random.shuffle(report_data_list)
    # 不重复的类型集
    type_set = set([])
    # 训练集
    detail_list = []
    type_list = []
    # 不存在的department
    none_department = []
    type_weight_data = []
    unit_weight_data = []
    # LearnLog.AddLog('Begin seg, time: %s' % time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time()))))

    # 加载location字典
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

    for data in report_data_list:
        type_value = data.str_type()
        type_set.add(type_value)

        data.seg_detail()
        # 添加到detail type训练集
        detail_list.append(' '.join(str(v) for v in data.detail_nv))
        type_list.append(type_value)

    type_dict = {}
    i = 0
    for v in type_set:
        i += 1
        type_dict[str(v)] = i

    # 保存type字典
    with open(TYPE_SET_FILE, 'w', encoding='utf-8') as f:
        for k, v in type_dict.items():
            f.writelines('%s$%s\n' % (k, v))

    # 保存训练数据 detail type
    with open(DETAIL_TRAIN_FILE, 'w', encoding='utf-8') as f:
        for x in detail_list:
            f.writelines('%s\n' % x)

    with open(TYPE_TRAIN_FILE, 'w', encoding='utf-8') as f:
        filter_list = []
        for x in type_list:
            dict_value = type_dict[str(x)]
            filter_list.append(dict_value)
        for x in filter_list:
            f.writelines('%s\n' % x)


def handle_data_from_db():
    session = load_session()

    try:
        detail_list = []
        type_list = []
        data = session.query(AlgorithmData).filter(
            AlgorithmData.detail != '',
            # AlgorithmData.type_name != '',
            AlgorithmData.new_flag == True,
            AlgorithmData.id > 335239,
            AlgorithmData.bigcat_id != '',
        ).all()

        for x in data:
            ns_words, nv_words, show_words = __seg_detail(x.detail)
            type_value = x.get_type_id()
            detail_list.append(' '.join(nv_words))
            type_list.append(type_value)

        result = session.query(
            AlgorithmData.bigcat_id, AlgorithmData.smallcat_id,
            AlgorithmData.threecat_id, AlgorithmData.infocat_id
        ).group_by(
            AlgorithmData.bigcat_id, AlgorithmData.smallcat_id,
            AlgorithmData.threecat_id, AlgorithmData.infocat_id
        ).all()
        type_set = set()
        type_dict = {}
        i = 1
        for x in result:
            s = '.'.join(x)
            type_set.add(s)
            type_dict[s] = i
            i += 1

        with open(TYPE_SET_FILE, 'w', encoding='utf-8') as f:
            for k, v in type_dict.items():
                f.writelines('%s$%s\n' % (k, v))

        with open(DETAIL_TRAIN_FILE, 'w', encoding='utf-8') as f:
            for x in detail_list:
                f.writelines('%s\n' % x)

        with open(TYPE_TRAIN_FILE, 'w', encoding='utf-8') as f:
            for x in type_list:
                dict_value = type_dict[x]
                f.writelines('%s\n' % dict_value)

    except:
        print('error')
    finally:
        session.close()


def __set_class_weight():
    session = load_session()
    try:
        result = session.query(
            AlgorithmData.bigcat_id, AlgorithmData.smallcat_id,
            AlgorithmData.threecat_id, AlgorithmData.infocat_id,
            func.count('*')
        ).group_by(
            AlgorithmData.bigcat_id, AlgorithmData.smallcat_id,
            AlgorithmData.threecat_id, AlgorithmData.infocat_id
        ).all()
        type_dict = {}
        class_weight = {}
        with open(TYPE_SET_FILE, 'r', encoding='utf-8') as f:
            for line in f.readlines():
                line = line.strip()
                k, v = line.split('$')
                type_dict[k] = v

        for x in result:
            s = '.'.join(x[:4])
            weight = 1
            if x[4] < 10:
                weight = x[4] * 2000
            elif x[4] < 100:
                weight = x[4] * 200
            elif x[4] < 1000:
                weight = x[4] * 20
            class_weight[type_dict[s]] = weight

        with open(CLASS_WEIGHT_FILE, 'w', encoding='utf-8') as f:
            for k, v in class_weight.items():
                f.writelines('%s$%s\n' % (k, v))
    except IOError:
        pass
    finally:
        session.close()


class ReportData(object):
    """
    报案数据
    """

    def __init__(self, case_id, finished_time, location, detail,
                 bigcat_id, smallcat_id, threecat_id, infocat_id, ):

        self.case_id = case_id
        self.finished_time = finished_time
        self.location = location
        self.detail = detail
        self.bigcat_id = bigcat_id
        self.smallcat_id = smallcat_id
        self.threecat_id = threecat_id
        self.infocat_id = infocat_id

        self.detail_ns = None
        self.detail_nv = None

    def str_type(self):
        return '.'.join([self.bigcat_id, self.smallcat_id, self.threecat_id, self.infocat_id])

    def __seg_type(self):
        pass

    def seg_detail(self):
        ns_words = []
        nv_words = []
        words = pseg.cut(self.detail)
        for w in words:
            if w.word in STOP_WORDS:
                continue
            if w.flag in ["ns"]:
                ns_words.append(w.word)
            # nv 存放所有词
            nv_words.append(w.word)

        self.detail_ns = ns_words
        self.detail_nv = nv_words


def __read_data_file(file_path, ):
    """加载历史报案数据"""
    report_data_list = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            line_arr = line.strip().split('$')
            # 0 big type, 1 small type, 4 detail, 6 department
            rd = ReportData(line_arr[0], line_arr[1], line_arr[2],
                            __detail_format(line_arr[3]).strip(), line_arr[4],
                            line_arr[5], line_arr[6], line_arr[7])
            report_data_list.append(rd)

    # LearnLog.AddLog('load data %d lines' % len(report_data_list))
    return report_data_list


# 格式化数据，去除里面的无用字符
def __detail_format(detail: str) -> str:
    detail = detail.replace('（', '(').replace('）', ')')
    detail_re = re.compile(r'【.*】')
    detail = detail_re.sub('', detail)
    detail_re = re.compile(r'\(.*\)')
    detail = detail_re.sub('', detail)
    # 处理特殊字符
    detail_re = re.compile(r'[☆▲●【】，。,:：-]')
    detail = detail_re.sub('', detail)
    detail = detail.replace('\r\n', ' ')
    detail = detail.replace('\n', ' ')
    detail = detail.strip()
    return detail


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


def __set_case_distributed_key_words():
    d = {
        '城市管理.市容环境.暴露垃圾': [('有垃圾', '有垃圾'), ('垃圾已满', '垃圾溢出')],
        '城市管理.街面秩序.非法小广告': [('野广告', '野广告')],
        '城市管理.街面秩序.无照游商': [('占道', '占道经营'), ],
        '城市管理.街面秩序.机动车乱停放': [('违停', '违法停车')],
    }
    session = load_session()
    try:
        for k, v in d.items():
            algorithm_case_type = AlgorithmCaseType(k.replace('.', '#'))
            for x in v:
                algorithm_key_word = AlgorithmKeyWord(x[0], x[1])
                algorithm_case_type.key_words.append(algorithm_key_word)
                session.add(algorithm_key_word)
            session.add(algorithm_case_type)
        session.commit()
    except:
        session.rollback()
    finally:
        session.close()


def __set_all_new_data_to_db():
    session = load_session()
    l = excel_table_byindex(ALL_NEW_DATA_FILE)
    i = 0
    for x in l:
        case_id = x['ID']
        finished_time = x['结案时间']
        location = x['案件地址']
        detail = x['案件描述']
        bigcat_id = __get_type_id(x['大类'], session, _type='bigCat')
        smallcat_id = __get_type_id(x['小类'], session, _type='smallCat')
        threecat_id = __get_type_id(x['三类'], session, _type='threeCat')
        infocat_id = __get_type_id(x['细类'], session, _type='InfoCat')
        # algorithm_data = session.query(AlgorithmData).filter(
        #     AlgorithmData.case_id == case_id,
        #     AlgorithmData.detail == detail,
        # ).first()

        # if algorithm_data is None:
        if finished_time == '':
            f_time = None
        else:
            f_time = time.strptime(finished_time, "%Y/%m/%d %X")
        algorithm_data = AlgorithmData(case_id, f_time,
                                       location, detail, bigcat_id, smallcat_id, threecat_id, infocat_id,
                                       '.'.join([x['大类'], x['小类'], x['三类'], x['细类']]),
                                       new_flag=2)
        session.add(algorithm_data)
        unit_list = x['部门信息'].split(';')[:-1]
        for unit in unit_list:
            unit_id = unit.split(',')[0]
            result = get_unit_name(unit_id)
            if result:
                name, type_, tier = result
                algorithm_data_unit = AlgorithmDataUnit(case_id, unit_id, name, type_, tier)
                algorithm_data.units.append(algorithm_data_unit)
                session.add(algorithm_data)
                session.add(algorithm_data_unit)
            else:
                print("row: %s error:unit_id: %s" % (x[''], unit_id))

        i += 1
        if i != 0 and i % 2000 == 0:
            session.commit()

    session.commit()  # 335239
    session.close()


def __get_type_id(name, session, _type='bigCat'):
    result = session.query(VisualCategory).filter(
        VisualCategory.category_name == name,
        VisualCategory.type == _type
    ).all()
    category_id = None
    if len(result) == 0:
        pass
    else:
        category_id = result[0].id
    return category_id


def __update_new_data_type():
    session = load_session()  # 335878
    l = excel_table_byindex(ALL_NEW_DATA_FILE)
    a_d_s = session.query(AlgorithmData).filter(
        AlgorithmData.id >= 335878,
    ).all()
    i = 0
    for x in l:
        case_id = x['ID']
        finished_time = x['结案时间']
        location = x['案件地址']
        detail = x['案件描述']
        bigcat_id = __get_type_id(x['大类'], session, _type='bigCat')
        smallcat_id = __get_type_id(x['小类'], session, _type='smallCat')
        threecat_id = __get_type_id(x['三类'], session, _type='threeCat')
        infocat_id = __get_type_id(x['细类'], session, _type='InfoCat')
        a_d = session.query(AlgorithmData).filter(
            AlgorithmData.case_id == case_id
        ).first()
        if a_d:
            a_d.bigcat_id = bigcat_id
            a_d.smallcat_id = smallcat_id
            a_d.threecat_id = threecat_id
            a_d.infocat_id = infocat_id
            session.add(a_d)
            pass
        else:
            print(x[''])
        i += 1
        if i != 0 and i % 2000 == 0:
            session.commit()
    session.commit()
    session.close()


def __get_no_id():
    l = excel_table_byindex(ALL_NEW_DATA_FILE)
    session = load_session()
    with open('my.txt', mode='w', encoding='utf-8') as f:
        for x in l:
            result = session.query(AlgorithmData).filter(
                AlgorithmData.case_id == x['ID']
            ).first()

            if result is None:
                line_list = [x[''], x['ID'], x['结案时间'], x['案件地址'], x['案件描述'],
                             x['大类'], x['小类'], x['三类'], x['细类'], x['部门信息']]
                s = '~~'.join(line_list)
                f.write('%s\n' % s)

    session.close()


def __get_error_type():
    session = load_session()
    result = session.query(AlgorithmData.type_name).filter(
        AlgorithmData.id > 335239
    ).group_by(AlgorithmData.type_name).all()
    for x in result:
        # print(x[0])
        l = x[0].split('.')
        if l[0] == '':
            pass
        else:
            big_cat = session.query(VisualCategory).filter(
                VisualCategory.category_name == l[0],
                VisualCategory.type == 'bigCat'
            ).first()
            if big_cat:
                if l[1] == '':
                    pass
                else:
                    small_cat = session.query(VisualCategory).filter(
                        VisualCategory.category_name == l[1],
                        VisualCategory.type == 'smallCat',
                        VisualCategory.parent_id == big_cat.category_id
                    ).first()
                    if small_cat:
                        if l[2] == '':
                            pass
                        else:
                            three_cat = session.query(VisualCategory).filter(
                                VisualCategory.category_name == l[2],
                                VisualCategory.type == 'threeCat',
                                VisualCategory.parent_id == small_cat.category_id
                            ).first()
                            if three_cat:
                                if l[3] == '':
                                    pass
                                else:
                                    info_cat = session.query(VisualCategory).filter(
                                        VisualCategory.category_name == l[3],
                                        VisualCategory.type == 'InfoCat',
                                        VisualCategory.parent_id == three_cat.category_id
                                    ).first()
                                    if info_cat:
                                        pass
                                    else:
                                        print('%s infocat' % x[0])
                            else:
                                print('%s threecat' % x[0])
                    else:
                        print('%s smallcat' % x[0])
            else:
                print('%s bigcat' % x[0])
    session.close()


def __update_right_type():
    error_s = '''城市设施.井盖设施.无主井盖. threecat
城市设施.井盖设施.污水井盖. threecat
城市设施.井盖设施.路灯井盖. threecat
城市设施.井盖设施.雨水井盖. threecat
城市设施.交通设施.停车场. threecat
城市设施.交通设施.其它. threecat
城市设施.交通设施.道路隔音屏. threecat
城市设施.市政设施.市政排水设施. smallcat
城市设施.市政设施.市政排水设施.下水道 smallcat
城市设施.市政设施.市政排水设施.其它 smallcat
城市设施.市政设施.市政排水设施.排水沟渠 smallcat
城市设施.市政设施.市政排水设施.污水管道 smallcat
城市设施.市政设施.市政排水设施.雨水污水合流管道 smallcat
城市设施.市政设施.市政排水设施.雨水篦子 smallcat
城市设施.市政设施.市政桥涵设施. smallcat
城市设施.市政设施.市政桥涵设施.其它 smallcat
城市设施.市政设施.市政桥涵设施.地下通道 smallcat
城市设施.市政设施.市政桥涵设施.立交桥 smallcat
城市设施.市政设施.市政桥涵设施.过街天桥 smallcat
城市设施.市政设施.市政照明设施. smallcat
城市设施.市政设施.市政照明设施.其它 smallcat
城市设施.市政设施.市政照明设施.地灯 smallcat
城市设施.市政设施.市政照明设施.路灯 smallcat
城市设施.市政设施.市政照明设施.路灯杆 smallcat
城市设施.市政设施.市政道路设施. smallcat
城市设施.市政设施.市政道路设施.人行道 smallcat
城市设施.市政设施.市政道路设施.其它 smallcat
城市设施.市政设施.市政道路设施.城市机动车道 smallcat
城市设施.市政设施.市政道路设施.眨眼石 smallcat
城市设施.环卫设施.. smallcat
城市设施.环卫设施.公共厕所. smallcat
城市设施.环卫设施.其它. smallcat
城市设施.环卫设施.化粪池. smallcat
城市设施.环卫设施.垃圾中转站\转运站. smallcat
城市设施.环卫设施.垃圾填埋场. smallcat
城市设施.环卫设施.垃圾池. smallcat
城市设施.环卫设施.垃圾箱. smallcat
城市设施.环卫设施.垃圾间（楼）. smallcat
城市设施.环卫设施.洒水车供水站. smallcat
城市设施.环卫设施.环卫工人休息室. smallcat
城市设施.环卫设施.环卫车辆. smallcat
环境保护.噪音污染.建筑施工噪音. threecat
环境保护.噪音污染.建筑施工噪音.倾倒渣土 threecat
环境保护.噪音污染.建筑施工噪音.其它 threecat
环境保护.噪音污染.建筑施工噪音.施工扰民 threecat
环境保护.噪音污染.社会生活噪音. threecat
环境保护.噪音污染.社会生活噪音.其它 threecat
环境保护.噪音污染.社会生活噪音.喇叭叫卖 threecat
环境保护.噪音污染.社会生活噪音.夜市摊点 threecat
环境保护.噪音污染.社会生活噪音.娱乐噪音 threecat
环境保护.噪音污染.社会生活噪音.室内装修 threecat
环境保护.噪音污染.社会生活噪音.家养宠物 threecat
环境保护.噪音污染.社会生活噪音.广场舞 threecat
环境保护.噪音污染.社会生活噪音.生活设备噪音 threecat
环境保护.噪音污染.社会生活噪音.街头卖唱 threecat
环境保护.噪音污染.社会生活噪音.饲养家禽 threecat
环境保护.大气污染.其它. threecat
环境保护.大气污染.工业烟尘废气. threecat
环境保护.大气污染.工地扬尘. threecat
环境保护.大气污染.焚烧垃圾树叶. threecat
环境保护.大气污染.经营性煤火炉灶. threecat
环境保护.市容环境.. smallcat
环境保护.市容环境.乱倒渣土. smallcat
环境保护.市容环境.乱排污水. smallcat
环境保护.市容环境.公共场所遛狗. smallcat
环境保护.市容环境.其它. smallcat
环境保护.市容环境.动物尸体清理. smallcat
环境保护.市容环境.废弃家具设备. smallcat
环境保护.市容环境.废弃车辆. smallcat
环境保护.市容环境.建筑垃圾. smallcat
环境保护.市容环境.建筑物外立面不洁. smallcat
环境保护.市容环境.施工未围场. smallcat
环境保护.市容环境.暴露垃圾. smallcat
环境保护.市容环境.水域秩序. smallcat
环境保护.市容环境.私占公共用地. smallcat
环境保护.市容环境.绿地脏乱. smallcat
环境保护.市容环境.车外抛垃圾. smallcat
环境保护.市容环境.违章建筑. smallcat
环境保护.市容环境.违章接坡. smallcat
环境保护.市容环境.道路不洁. smallcat
环境保护.市容环境.道路撒漏. smallcat
环境保护.市容环境.道路破损. smallcat
环境保护.市容环境.道路积水. smallcat
环境保护.市容环境.遮阳棚破损. smallcat
环境保护.市容环境.随地大小便. smallcat
环境保护.市容环境.非装饰性树挂. smallcat
环境保护.街面秩序.. smallcat
环境保护.街面秩序.乱倒污水. smallcat
环境保护.街面秩序.乱堆物堆料. smallcat
环境保护.街面秩序.乱扔垃圾、随地吐痰行为. smallcat
环境保护.街面秩序.其它. smallcat
环境保护.街面秩序.占用消防通道. smallcat
环境保护.街面秩序.占道作业. smallcat
环境保护.街面秩序.占道广告牌. smallcat
环境保护.街面秩序.占道废品收购. smallcat
环境保护.街面秩序.广告招牌破损. smallcat
环境保护.街面秩序.店外经营. smallcat
环境保护.街面秩序.施工占道. smallcat
环境保护.街面秩序.无照游商. smallcat
环境保护.街面秩序.机动车乱停放. smallcat
环境保护.街面秩序.横幅乱吊乱挂. smallcat
环境保护.街面秩序.沿街晾挂. smallcat
环境保护.街面秩序.洗车场/冲洗站. smallcat
环境保护.街面秩序.空调室外挂机低挂. smallcat
环境保护.街面秩序.街头卖艺. smallcat
环境保护.街面秩序.街头散发广告. smallcat
环境保护.街面秩序.违章张贴悬挂广告牌匾. smallcat
环境保护.街面秩序.违章设置LED屏. smallcat
环境保护.街面秩序.露天烧火. smallcat
环境保护.街面秩序.非机动车乱停放. smallcat
环境保护.街面秩序.非法小广告. smallcat
'''
    lines = error_s.split('\n')
    error_list = []
    for line in lines:
        error_list.append(line.split(' ')[0])

    session = load_session()
    result = session.query(AlgorithmData).filter(
        AlgorithmData.id > 335239,
        AlgorithmData.type_name.in_(error_list)
    ).all()
    i = 0
    for x in result:
        type_list = x.type_name.split('.')
        type_list[0] = '城市管理'
        x.type_name = '.'.join(type_list)
        session.add(x)
        i += 1
        if i != 0 and i % 10000 == 0:
            session.commit()
    session.commit()
    # print(len(result))
    session.close()


def __update_right_type_id():
    session = load_session()
    a_d_list = session.query(AlgorithmData).filter(
        AlgorithmData.id > 335239,
    ).all()
    i = 0
    for a_d in a_d_list:
        type_list = a_d.type_name.split('.')
        if type_list[0] != '':
            bigcat = session.query(VisualCategory).filter(
                VisualCategory.category_name == type_list[0],
                VisualCategory.type == 'bigCat',
            ).first()
            if bigcat:
                a_d.bigcat_id = bigcat.category_id
                if type_list[1] != '':
                    smallcat = session.query(VisualCategory).filter(
                        VisualCategory.category_name == type_list[1],
                        VisualCategory.parent_id == bigcat.category_id
                    ).first()
                    if smallcat:
                        a_d.smallcat_id = smallcat.id
                        if type_list[2] != '':
                            threecat = session.query(VisualCategory).filter(
                                VisualCategory.category_name == type_list[2],
                                VisualCategory.parent_id == smallcat.category_id
                            ).first()
                            if threecat:
                                a_d.threecat_id = threecat.id
                                if type_list[3] != '':

                                    infocat = session.query(VisualCategory).filter(
                                        VisualCategory.category_name == type_list[3],
                                        VisualCategory.parent_id == threecat.category_id
                                    ).first()
                                    if infocat:
                                        a_d.infocat_id = infocat.category_id
                                    else:
                                        print('error: %d, %s infocat', a_d.id, a_d.type_name)
                            else:
                                print('error: %d, %s threecat', a_d.id, a_d.type_name)
                    else:
                        print('error: %d, %s smallcat', a_d.id, a_d.type_name)

                session.add(a_d)
            else:
                print('error: %d, %s bigcat', a_d.id, a_d.type_name)
        i += 1
        if i != 0 and i % 2000 == 0:
            print(i)
            session.commit()

    session.commit()
    session.close()


def __update_beautiful_type_name():
    """

    :return:
    """
    session = load_session()
    a_d_list = session.query(AlgorithmData).filter(
        AlgorithmData.id > 335239,
    ).all()
    i = 0
    for x in a_d_list:
        x.type_name = re.sub('\.+$', '', x.type_name)
        session.add(x)
        i += 1
        if i != 0 and i % 2000 == 0:
            print(i)
            session.commit()
    session.commit()
    session.close()


def excel_table_byindex(file='file.xls', colnameindex=0, by_index=0):
    result_list = None
    with xlrd.open_workbook(ALL_NEW_DATA_FILE) as data:
        table = data.sheets()[by_index]
        n_rows = table.nrows  # 行数
        n_cols = table.ncols  # 列数
        col_names = table.row_values(colnameindex)  # 某一行数据
        result_list = []
        for row_num in range(1, n_rows):
            row_line = table.row_values(row_num)
            if row_line:
                app = {}
                for i in range(len(col_names)):
                    app[col_names[i]] = row_line[i]
                result_list.append(app)
    return result_list


def main():
    # pretreat()
    # report_data_list = __read_data_file(DATA_TYPE_FILE)
    # handle_data(report_data_list)
    # pretreat_new_data_to_db()
    # ll = [(1, 2), (3, 4, 5), (6, 7, 8)]
    # print(get_func(ll))
    set_new_data_weight_to_db()
    # pretreat_old_data_to_db()
    # handle_data_from_db()
    # __set_class_weight()
    # __set_case_distributed_key_words()
    # __set_all_new_data_to_db()
    # __update_new_data_type()
    # __get_no_id()
    # __get_error_type()
    # __update_right_type()
    # __update_right_type_id()
    # __update_beautiful_type_name()
    pass


if __name__ == '__main__':
    main()
