import time

import requests
from flask import Flask, json, jsonify, request
from jsonschema import Draft4Validator
from sklearn.externals import joblib
from sqlalchemy import func, or_

from qgw_autoflow.common.logger import MyLog
from qgw_autoflow.common.resource import (CASE_FINISHED_JSON_FILE,
                                          TYPE_CLF_FILE, TYPE_TFIDF_FILE,
                                          TYPE_VEC_FILE)
from qgw_autoflow.dao.model import (VisualArea, CaseAssignTier, CaseFinishTier,
                                    CaseRepo, VisualSource, VisualCategory,
                                    GridEventCategoryEncoder, NewCaseFinished,
                                    VisualDepart, OrgUnitEncoder,
                                    db_session, load_session)
from qgw_autoflow.service import biz, assign2, assign3
from qgw_autoflow.service.biz import get_word, get_category_id, get_category_name, get_depart_by_id

vec = joblib.load(TYPE_VEC_FILE)
tfidf = joblib.load(TYPE_TFIDF_FILE)
clf = joblib.load(TYPE_CLF_FILE)
type_set = biz.load_type_set()

url_intelligence = '172.20.15.1:8082'

app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello World!'


# API接口，获取案件类别
@app.route('/api/type', methods=['GET', ])
def index():
    detail = request.args.get('detail')
    result = {}
    global vec, clf, type_set
    case_type, department_list = biz.back_train(detail, vec, tfidf, clf, type_set)
    result['type'] = case_type
    result['department_list'] = department_list
    return json.dumps(result, ensure_ascii=False, cls=OrgUnitEncoder)


# API接口，获取案件类别，三级分类
@app.route('/api/case_type', methods=['POST', ])
def type_case():
    """

    :return:
    """
    case_type_list = []
    error_flag = False
    message = ''
    data_dict = None
    if request.data:
        MyLog.get_log().info('method: case_type data: %s' % request.data.decode('utf8'))

        try:
            data_dict = json.loads(request.data)
        except ValueError:
            error_flag = True
            message += '只接收json数据!\n'
        if not error_flag:
            if 'case_id' in data_dict.keys() \
                    and 'detail' in data_dict.keys() \
                    and 'location' in data_dict.keys():
                case_id = data_dict['case_id']
                detail = data_dict['detail']
                location = data_dict['location']
                if not isinstance(case_id, str):
                    message += 'case_id is not str!\n'
                    error_flag = True
                if not isinstance(detail, str):
                    message += 'detail is not str!\n'
                    error_flag = True
                if not isinstance(location, str):
                    message += 'location is not str!\n'
                    error_flag = True
                global vec, tfidf, clf, type_set
                case_type_list = biz.get_case_type(case_id, detail, location, vec, tfidf, clf, type_set)
            else:
                message += '必填项有缺失。'
                error_flag = True

    else:
        MyLog.get_log().info('method: case_type no data.')
        message = '没有请求数据。'
        error_flag = True

    if error_flag:
        return json.dumps({'message': message}, ensure_ascii=False)
    else:
        return json.dumps(case_type_list, ensure_ascii=False, cls=GridEventCategoryEncoder)


# API接口，案件指派
@app.route('/api/case_assign', methods=['POST', ])
def case_assign():
    """

    :return:
    """
    case_unit_list = []
    message = ''
    error_flag = False
    data_dict = None
    recommend = []
    if request.data:
        MyLog.get_log().info('method: case_assign data: %s' % request.data.decode('utf8'))
        try:
            data_dict = json.loads(request.data)
        except ValueError:
            error_flag = True
            message += '只接收json数据!\n'
        if not error_flag:
            keys = data_dict.keys()
            if 'case_id' in keys \
                    and 'case_type' in keys \
                    and 'detail' in keys \
                    and 'location' in keys \
                    and 'linkage_unit_list' in keys:
                case_id = data_dict['case_id']
                case_type = data_dict['case_type']
                detail = data_dict['detail']
                location = data_dict['location']
                linkage_unit_list = data_dict['linkage_unit_list']
                if not isinstance(case_id, str):
                    error_flag = True
                    message += 'case_id is not str!\n'
                if not isinstance(case_type, str):
                    error_flag = True
                    message += 'case_type is not str!\n'
                if not isinstance(detail, str):
                    error_flag = True
                    message += 'detail is not str!\n'
                if not isinstance(location, str):
                    error_flag = True
                    message += 'location is not str!\n'
                if not isinstance(linkage_unit_list, list):
                    error_flag = True
                    message += 'linkage_unit_list is not list!\n'
                if not error_flag:
                    try:
                        time_begin = time.time()
                        recommend = assign3.grid_center(case_id, location, case_type, detail, linkage_unit_list)
                        time_end = time.time()
                        deal_time = time_end - time_begin

                        # 记录案件分派分信息
                        args = [case_id, case_type, location, detail]
                        biz.save_repo_assign_depart(args, deal_time, recommend)
                    except Exception as msg:
                        MyLog.get_log().info('method: case_assign_recommend_msg.' + str(msg))

                    pass
            else:
                message += '必填项有缺失。'
                error_flag = True

    else:
        # MyLog.get_log().info('method: case_assign no data.')
        message += '没有请求数据。'
    if error_flag:
        return json.dumps({'message': message}, ensure_ascii=False)
    else:
        return json.dumps(recommend, ensure_ascii=False, cls=OrgUnitEncoder)


# # API接口，插入完成案件信息
@app.route('/api/case_finished', methods=['POST', ])
def case_finished():
    """
    结案处理
    :return:
    """
    data_dict = None
    message = ''
    error_flag = False
    with open(CASE_FINISHED_JSON_FILE, mode='r', encoding='utf-8') as f:
        schema_string = f.read()
    if request.data:
        MyLog.get_log().info('method: case_finished data: %s' % request.data.decode('utf8'))
        try:
            data_dict = json.loads(request.data)
            if data_dict['location'] is None:
                data_dict['location'] = ''
        except ValueError:
            error_flag = True
            message += '只接收json数据!\n'
        if not error_flag:
            schema = json.loads(schema_string)
            v = Draft4Validator(schema)
            errors = v.iter_errors(data_dict)
            for error in errors:
                message += '%s\n' % error.message
            if message != '':
                error_flag = True
            if error_flag:
                pass
            else:
                case_id = data_dict['case_id']
                case_type = data_dict['case_type']
                detail = data_dict['detail']
                location = data_dict['location']
                linkage_unit_list = data_dict['linkage_unit_list']
                _date = data_dict['date']
                longitude = None
                latitude = None
                try:
                    if 'longgitude' in data_dict.keys():
                        longitude = float(data_dict['longitude'])
                except ValueError:
                    message += 'longitude不能转化为小数，请检查数据。'
                    error_flag = True
                try:
                    if 'latitude' in data_dict.keys():
                        latitude = float(data_dict['latitude'])
                except ValueError:
                    message += 'latitude不能转化为小数，请检查数据。'
                    error_flag = True
                if not error_flag:
                    n_c_f = NewCaseFinished(case_id, case_type, detail, location, longitude,
                                            latitude, _date)
                    json_info = request.data.decode('utf-8')
                    biz.finish_case(json_info.replace("\n", ""), n_c_f, linkage_unit_list)
    else:
        MyLog.get_log().error('method: case_finished no data.')
        message += '没有请求数据。'
        error_flag = True
    if error_flag:
        result_dict = {'message': message}
    else:
        result_dict = {'result': 'ok'}
        save_repo_finish(data_dict)

    return json.dumps(result_dict, ensure_ascii=False)


def save_repo_finish(data_dict):
    """
    保存结案的信息
    判断分类和派遣是否正确的规则：
    （1）当结案数据的类别或者委派部门是空的时候，这条数据无效，不设置finish_time,当作未结案处理
    （2）类别必须全部相等才能算正确
     (3) 判断结案的最大tier是否在分派里面，如果有就算对
    :param data_dict:
    :return:
    """
    time.sleep(0.5)
    session = db_session
    case_repo = session.query(CaseRepo).filter(CaseRepo.case_id == data_dict['case_id']).first()
    if case_repo is None:
        case_repo = CaseRepo()

    case_repo.case_id = data_dict['case_id']
    case_repo.detail = data_dict['detail']
    case_repo.location = data_dict['location']
    session.add(case_repo)
    session.commit()

    finish_tier = data_dict['linkage_unit_list']
    is_finish = __deal_category(case_repo, data_dict) \
                & __deal_depart(case_repo, finish_tier, session)

    if is_finish:
        case_repo.finish_time = data_dict['date']
        if case_repo.finish_time == '':
            case_repo.finish_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    else:
        case_repo.is_depart_correct = None
        case_repo.is_category_correct = None
        case_repo.finish_time = None

    case_repo.update_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    session.add(case_repo)
    session.commit()
    session.close()


def __deal_category(case_repo, data_dict):
    """
    处理结案的类别
    :param case_repo:
    :param data_dict:
    :return:
    """
    is_finish = True
    finish_cats = data_dict['case_type'].split('#')
    if finish_cats[0].__len__() == 0:
        is_finish = False
        return is_finish
    else:
        if len(finish_cats) >= 1:
            case_repo.finish_category_big = \
                get_category_id(finish_cats[0], type_name='bigCat')
        if len(finish_cats) >= 2:
            case_repo.finish_category_small = \
                get_category_id(finish_cats[1], 'smallCat', case_repo.finish_category_big)
        if len(finish_cats) >= 3:
            case_repo.finish_category_three = \
                get_category_id(finish_cats[2], 'threeCat', case_repo.finish_category_small)
        if len(finish_cats) >= 4:
            case_repo.finish_category_info = \
                get_category_id(finish_cats[3], 'infoCat', case_repo.finish_category_three)
        # 判断分类是否正确，当123类正确时为正确（因为太极不返回4类）
        if case_repo.finish_category_info:
            if case_repo.assign_category_big == case_repo.finish_category_big \
                    and case_repo.assign_category_small == case_repo.finish_category_small \
                    and case_repo.assign_category_three == case_repo.finish_category_three \
                    and case_repo.assign_category_info == case_repo.finish_category_info:
                case_repo.is_category_correct = True

            else:
                case_repo.is_category_correct = False
        if not case_repo.finish_category_info:
            if case_repo.assign_category_big == case_repo.finish_category_big \
                    and case_repo.assign_category_small == case_repo.finish_category_small \
                    and case_repo.assign_category_three == case_repo.finish_category_three:
                case_repo.is_category_correct = True
            else:
                case_repo.is_category_correct = False

    return is_finish


def __deal_depart(case_repo, finish_tier, session):
    """
    处理推荐部门是否是否正确
    :param case_repo:
    :param finish_tier:
    :param session:
    :return:
    """
    is_finish = True
    if finish_tier.__len__() == 0:
        is_finish = False
    else:
        # 删除原有的结案数据添加现在的结案数据
        old_finish = session.query(CaseFinishTier) \
            .filter(CaseFinishTier.case_repo_id == case_repo.id).all()
        [session.delete(cft) for cft in old_finish]
        session.commit()

        # 添加现在的结案数据
        case_repo.finish_depart = ''
        for unit in finish_tier:
            case_repo.finish_depart += '%s,%s,%s$' % (unit['id'], unit['name'], unit['tier'])

            cf = CaseFinishTier()
            cf.case_repo_id = case_repo.id
            cf.depart_id = unit['id']
            cf.finish_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            cf.depart_name = unit['name']
            cf.tier = unit['tier']
            if cf.tier == '':
                depart = get_depart_by_id(unit['id'])
                if depart is not None:
                    cf.tier = depart.tier
            session.add(cf)
        session.commit()

        # 分派的信息
        assign_tier = session.query(CaseAssignTier) \
            .filter(CaseAssignTier.case_repo_id == case_repo.id) \
            .all()
        if assign_tier.__len__() == 0:
            is_finish = False
            return is_finish

        assign_tier.sort(key=lambda obj: obj.tier, reverse=True)
        finish_tier.sort(key=lambda obj: obj.get('tier'), reverse=True)
        max_assign_tier = assign_tier[0].tier
        max_finish_tier = int(finish_tier[0]['tier'])

        is_depart_correct = True
        if max_finish_tier > max_assign_tier:
            is_depart_correct = False

        if max_assign_tier >= max_finish_tier:
            assign_tier = session.query(CaseAssignTier.depart_id) \
                .filter(CaseAssignTier.case_repo_id == case_repo.id, CaseAssignTier.tier == max_finish_tier) \
                .all()
            finish_tier = session.query(CaseFinishTier.depart_id) \
                .filter(CaseFinishTier.case_repo_id == case_repo.id, CaseFinishTier.tier == max_finish_tier) \
                .all()

            assign_tier = set(assign_tier)
            finish_tier = set(finish_tier)
            common = assign_tier.intersection(finish_tier)
            if common.__len__() == 0:
                is_depart_correct = False

        case_repo.is_depart_correct = is_depart_correct
    return is_finish


def save_repo_distribute(data_dict, params_dict):
    session = db_session
    case_repo = session.query(CaseRepo).filter(CaseRepo.case_id == data_dict['case_id']).first()
    if case_repo is None:
        case_repo = CaseRepo()
    case_repo.area_id = params_dict['area_id']
    case_repo.area_name = params_dict['area']
    case_repo.source_id = params_dict['source_id']
    case_repo.source_name = params_dict['source']
    case_repo.longitude = params_dict['longitude']
    case_repo.latitude = params_dict['latitude']
    case_repo.occur_time = params_dict['occur_time']
    case_repo.key_words = params_dict['key_words']
    session.add(case_repo)
    session.commit()
    session.close()


@app.route('/api/case_distributed', methods=['POST', ])
def distribute_case():
    session = db_session
    message = ''
    error_flag = False
    if request.data:
        MyLog.get_log().info('method: case_distributed data: %s' % request.data.decode('utf8'))
        data_dict = None
        try:
            data_dict = json.loads(request.data)
        except ValueError:
            error_flag = True
            message += '只接收json数据!\n'
        if not error_flag:
            keys = data_dict.keys()
            if 'case_id' in keys \
                    and 'case_type' in keys \
                    and 'detail' in keys \
                    and 'assign_date' in keys \
                    and 'source' in keys \
                    and 'area' in keys \
                    and 'address' in keys \
                    and 'first_unit' in keys \
                    and 'occur_time' in keys:
                case_id = data_dict['case_id']
                case_type = data_dict['case_type']
                detail = data_dict['detail']
                assign_date = data_dict['assign_date']
                source = data_dict['source']
                area = data_dict['area']
                address = data_dict['address']
                first_unit = data_dict['first_unit']
                occur_time = data_dict['occur_time']

                if not isinstance(case_id, str):
                    message += 'case_id is not str!\n'
                    error_flag = True
                if not isinstance(case_type, str):
                    message += 'case_type is not str!\n'
                    error_flag = True
                if not isinstance(detail, str):
                    message += 'detail is not str!\n'
                    error_flag = True
                if not isinstance(assign_date, str):
                    message += 'assign_date is not str!\n'
                    error_flag = True
                if not isinstance(source, str):
                    message += 'source is not str!\n'
                    error_flag = True
                if not isinstance(area, str):
                    message += 'area is not str!\n'
                    error_flag = True
                if not isinstance(address, str):
                    message += 'address is not str!\n'
                    error_flag = True
                if not isinstance(first_unit, str):
                    message += 'first_unit is not str!\n'
                    error_flag = True
                if not isinstance(occur_time, str):
                    message += 'occur_time is not str!\n'
                    error_flag = True

                if error_flag:
                    pass
                else:
                    result_area = None
                    result_first_unit = None
                    result_grid_event_category = None
                    result_source = None
                    try:
                        result_area = session.query(VisualArea).filter(VisualArea.name == area).first()
                        if result_area is None:
                            raise ValueError
                    except ValueError:
                        message += '找不到相应的area，请检查数据。\n'
                        error_flag = True

                    try:
                        result_first_unit = session.query(VisualDepart).filter(
                            VisualDepart.tier <= 2,
                            VisualDepart.unit_name == first_unit,
                        ).first()
                        if result_first_unit is None:
                            raise ValueError
                    except ValueError:
                        message += '找不到first_unit，请检查数据。\n'
                        error_flag = True

                    try:
                        type_list = case_type.split('#')
                        result_grid_event_category = session.query(VisualCategory).filter(
                            VisualCategory.category_name == type_list[0],
                            VisualCategory.type == 'bigCat',
                        ).first()
                        if result_grid_event_category is None:
                            raise ValueError
                    except ValueError:
                        message += '大类找不到，请检查数据。\n'
                        error_flag = True

                    try:
                        result_source = session.query(VisualSource).filter(
                            VisualSource.name == source
                        ).first()
                        if result_source is None:
                            raise ValueError
                    except ValueError:
                        message += '找不到案件来源，请检查数据。\n'
                        error_flag = True

                    if 'longitude' in keys:
                        if data_dict['longitude'] == '':
                            if result_area:
                                longitude = result_area.longitude
                        else:
                            try:
                                longitude = float(data_dict['longitude'])
                            except ValueError:
                                message += '经度不能转换为float类型的。'
                                error_flag = True
                    else:
                        if result_area:
                            longitude = result_area.longitude

                    if 'latitude' in keys:
                        if data_dict['latitude'] == '':
                            if result_area:
                                latitude = result_area.latitude
                        else:
                            try:
                                latitude = data_dict['latitude']
                            except ValueError:
                                message += '纬度不能转换为float类型的。'
                                error_flag = True
                    else:
                        if result_area:
                            latitude = result_area.latitude

                    if error_flag:
                        pass
                    else:
                        # result_l = get_word(detail, case_type=case_type)
                        # words = []
                        # for x in result_l:
                        #     words.append(x[0])
                        # s = ' '.join(words)
                        s = get_word(detail, case_type=case_type)
                        url = 'http://qgwzlc.ibdbots.com/display/add_case'
                        params_dict = {
                            'address': address, 'area': area, 'area_id': result_area.id,
                            'assign_date': assign_date, 'case_id': case_id,
                            'case_category': result_grid_event_category.category_name,
                            'case_category_id': result_grid_event_category.category_id,
                            'detail': detail, 'first_unit': first_unit, 'first_unit_id': result_first_unit.unit_id,
                            'key_words': s, 'latitude': latitude, 'longitude': longitude,
                            'source': source, 'source_id': result_source.id,
                            'occur_time': occur_time,
                        }
                        try:

                            save_repo_distribute(data_dict, params_dict)

                            r = requests.post(url, data=params_dict)
                        except ConnectionError:
                            error_flag = True
                            message = '不能连接可视化接口'
                            # print(r.text)
                            # print(r.url)

            else:
                message += '必填项有缺失。'
                error_flag = True

    else:
        MyLog.get_log().info('method: case_distributed no data')
        message += 'method: case_distributed no enough data'
        error_flag = True

    if error_flag:
        MyLog.get_log(log_name='case_d_error').error(
            'data: %s;message: %s' % (request.data.decode('utf8'), message)
        )
        result_dict = {'message': message}

    else:
        MyLog.get_log(log_name='case_d_success').info(
            'method: case_distributed data: %s' % request.data.decode('utf8')
        )
        result_dict = {'result': 'ok'}

    return json.dumps(result_dict, ensure_ascii=False)


@app.route('/api/avg_deal_time', methods=['POST', ])
def get_deal_time():
    # session = db_session
    # count = session.query(CaseRepo).count()
    # deal_category_time = session.execute('select sum(deal_category_time) from case_repo').first()[0]
    # # deal_depart_time = session.execute('select sum(deal_depart_time) from case_repo ').first()[0]

    avg, message = biz.get_avg_deal_time()
    if message == '':
        result = {'result': avg}
    else:
        result = {'message': message}

    return jsonify(result)


@app.route('/api/upload_case', methods=['POST', ])
def upload_case():
    pass


@app.route('/api/intelligence', methods=['POST', ])
def intelligence():
    """
    案件智能补全的接口，即调用图层的接口
    :return:
    """
    data = request.data
    result = {}
    try:
        data = json.loads(data.decode('utf8'))
        case_id = data['case_id']
        detail = data['detail']
        location = data['location']
        occur_time = data['occur_time']
        longitude = data['longitude']
        latitude = data['latitude']
        extend_param = data['extend_param']

        if case_id == '':
            raise ValueError('case_id')
        if detail == '':
            raise ValueError('detail')
        if location == '':
            raise ValueError('location')
        if occur_time == '':
            raise ValueError('occur_time')
        if longitude == '':
            raise ValueError('longitude')
        if latitude == '':
            raise ValueError('latitude')

        rep_param = {'caseSite': detail, 'caseLongitude': longitude, 'caseLatitude': latitude,
                     'caseClassify': 'chengguan', 'exParams': ''}

        # req_result=requests.post('172.20.15.1:8082')
        # print(req_result.content)

        """
        还需要记录案件信息到数据库
        case_repo=CaseRepo()
        """

        result = {
            'status': '1',
            'category': [{"id": "2016072800", "name": "城市管理", "type": "bigCat"},
                         {"id": "2016073443", "name": "街面秩序", "type": "smallCat"},
                         {"id": "2016073455", "name": "无照游商", "type": "threeCat"}],
            'depart': [{"id": "74529609387101585", "name": "云岩区", "possibility": "0.9965753424657534", "tier": "2"},
                       {"id": "-6070725672550055661", "name": "省府社区", "possibility": "0.12500000000000003",
                        "tier": "3"}],
            'extend_param': ''
        }

    except KeyError as msg:
        result = {'status': '0', 'msg': msg.args[0] + '不存在'}
    except ValueError as msg:
        result = {'status': '0', 'msg': msg.args[0] + '不能是空值'}
    except Exception as msg:
        result = {'status': '0', 'msg': msg.args[0]}

    finally:
        return json.dumps(result, encoding='utf8', ensure_ascii=False)


@app.route('/api/display/info', methods=['POST', ])
def count_info():
    """
    统计重要指标的信息
    :return:
    """

    str_result = {'status': 1, 'msg': ''}

    try:
        data = json.loads(request.data.decode('utf8'))
    except Exception as msg:
        str_result['status'] = 0
        str_result['msg'] = '请使用Json对象上传参数' + str(msg)
        return jsonify(str_result)

    if 'date' not in data:
        dtstr = ''
    else:
        dtstr = data['date']
    if 'big_type' not in data or data['big_type'] == '':
        type_id_big = ''
    else:
        type_name = data['big_type']
        type_id_big = get_category_id(type_name, 'bigCat')
        if type_id_big is None:
            type_id_big = ''
    if 'area' not in data:
        area_name = ''
    else:
        area_name = data['area']

    db = load_session()
    all = db.query(func.count()).filter(CaseRepo.deal_category_time != None, CaseRepo.deal_depart_time != None,
                                        CaseRepo.finish_time != None) \
        .filter(CaseRepo.occur_time.like('%' + dtstr + '%')) \
        .filter(CaseRepo.area_name.like('%' + area_name + '%')) \
        .filter(or_(CaseRepo.finish_category_big.like('%' + type_id_big + '%'),
                    CaseRepo.assign_category_big.like('%' + type_id_big + '%')))

    bigcat_count1 = all.filter(CaseRepo.assign_category_big == CaseRepo.finish_category_big).all()
    bigcat_count2 = all.filter(CaseRepo.assign_category_big.is_(None), CaseRepo.finish_category_big.is_(None)).all()
    small_count1 = all.filter(CaseRepo.assign_category_small == CaseRepo.finish_category_small).all()
    small_count2 = all.filter(CaseRepo.assign_category_small.is_(None), CaseRepo.finish_category_small.is_(None)).all()
    depart_count = all.filter(CaseRepo.is_depart_correct == True).all()
    area_count = all.filter(or_(CaseRepo.is_depart_correct == True, CaseRepo.is_category_correct == True)).all()

    all_count = all.all()
    all_count = all_count[0][0]
    if all_count == 0:
        all_count = 1.0
    else:
        all_count = all_count * 1.0

    result = []
    result.append({'name': '大类', 'score': (bigcat_count1[0][0] + bigcat_count2[0][0]) / all_count})
    result.append({'name': '小类', 'score': (small_count1[0][0] + small_count2[0][0]) / all_count})
    result.append({'name': '部门', 'score': depart_count[0][0] / all_count})
    result.append({'name': '区县', 'score': area_count[0][0] / all_count})

    str_result['msg'] = result
    return json.dumps(str_result, encoding='utf8', ensure_ascii=False)


@app.route('/api/display/category', methods=['POST', ])
def count_category():
    """
    类别统计
    :return:
    """

    def _get_count_(id, lst):
        for i in range(0, len(lst)):
            if lst[i][1] == id:
                return lst[i][0]
        pass

    str_result = {'status': 1, 'msg': ''}

    try:
        data = json.loads(request.data.decode('utf8'))
    except Exception as msg:
        str_result['status'] = 0
        str_result['msg'] = '请使用Json对象上传参数' + str(msg)
        return jsonify(str_result)

    if 'date' not in data:
        dtstr = ''
    else:
        dtstr = data['date']
    if 'big_type' not in data or data['big_type'] == '':
        type_id_big = None
    else:
        type_id_big = get_category_id(data['big_type'], 'bigCat')
    if 'small_type' not in data or data['small_type'] == '':
        type_id_small = None
    else:
        type_id_small = get_category_id(data['small_type'], 'smallCat', type_id_big)
        if type_id_big == '':
            type_id_small = None

    if 'area' not in data:
        area_name = ''
    else:
        area_name = data['area']

    if 'top' not in data:
        top = 20
    else:
        top = data['top']
        if isinstance(top, int) is not True:
            str_result['status'] = 0
            str_result['msg'] = 'top参数只能是整数'
            return jsonify(str_result)

    db = load_session()

    """
    三种情况
    1.大类为空的时候选择大类统计数据
    2.大类不空，小类为空的时候，统计该大类下面的小类的数据
    3.大小类都不是空的情况下，统计改大小类对应的三类数据
    """

    if type_id_big is None:
        """
        统计大类的数据
        """
        all_count = db.query(func.count(CaseRepo.assign_category_big).label('query_count'),
                             CaseRepo.assign_category_big) \
            .filter(CaseRepo.deal_category_time.isnot(None), CaseRepo.deal_depart_time.isnot(None),
                    CaseRepo.finish_time.isnot(None)) \
            .filter(CaseRepo.occur_time.like('%' + dtstr + '%')) \
            .filter(CaseRepo.area_name.like('%' + area_name + '%')) \
            .group_by(CaseRepo.assign_category_big).order_by('query_count desc') \
            .all()

        all_info = db.query(func.count(CaseRepo.assign_category_big).label('query_count'), CaseRepo.assign_category_big) \
            .filter(CaseRepo.deal_category_time.isnot(None), CaseRepo.deal_depart_time.isnot(None),
                    CaseRepo.finish_time.isnot(None)) \
            .filter(CaseRepo.occur_time.like('%' + dtstr + '%')) \
            .filter(CaseRepo.area_name.like('%' + area_name + '%')) \
            .filter(CaseRepo.assign_category_big == CaseRepo.finish_category_big) \
            .group_by(CaseRepo.assign_category_big).order_by('query_count desc') \
            .all()

    elif type_id_small is None:
        """
        筛选出指定大类下小类满足条件的数量
        """
        all_count = db.query(func.count(CaseRepo.assign_category_small).label('query_count'),
                             CaseRepo.assign_category_small) \
            .filter(CaseRepo.deal_category_time is not None, CaseRepo.deal_depart_time is not None,
                    CaseRepo.finish_time is not None) \
            .filter(CaseRepo.occur_time.like('%' + dtstr + '%')) \
            .filter(CaseRepo.area_name.like('%' + area_name + '%')) \
            .filter(or_(CaseRepo.finish_category_big.like('%' + type_id_big + '%'),
                        CaseRepo.assign_category_big.like('%' + type_id_big + '%'))) \
            .group_by(CaseRepo.assign_category_small).order_by('query_count desc') \
            .all()
        all_info = db.query(func.count(CaseRepo.assign_category_small).label('query_count'),
                            CaseRepo.assign_category_small) \
            .filter(CaseRepo.deal_category_time is not None, CaseRepo.deal_depart_time is not None,
                    CaseRepo.finish_time is not None) \
            .filter(CaseRepo.occur_time.like('%' + dtstr + '%')) \
            .filter(CaseRepo.area_name.like('%' + area_name + '%')) \
            .filter(or_(CaseRepo.finish_category_big.like('%' + type_id_big + '%'),
                        CaseRepo.assign_category_big.like('%' + type_id_big + '%'))) \
            .filter(CaseRepo.assign_category_small == CaseRepo.finish_category_small) \
            .group_by(CaseRepo.assign_category_small).order_by('query_count desc') \
            .all()

    else:
        """
        筛选三类的数据
        """
        all_count = db.query(func.count(CaseRepo.assign_category_three).label('query_count'),
                             CaseRepo.assign_category_three) \
            .filter(CaseRepo.deal_category_time is not None, CaseRepo.deal_depart_time is not None,
                    CaseRepo.finish_time is not None) \
            .filter(CaseRepo.occur_time.like('%' + dtstr + '%')) \
            .filter(CaseRepo.area_name.like('%' + area_name + '%')) \
            .filter(or_(CaseRepo.finish_category_big.like('%' + type_id_big + '%'),
                        CaseRepo.assign_category_big.like('%' + type_id_big + '%'))) \
            .filter(or_(CaseRepo.finish_category_small.like('%' + type_id_small + '%'),
                        CaseRepo.assign_category_small.like('%' + type_id_small + '%'))) \
            .group_by(CaseRepo.assign_category_three).order_by('query_count desc') \
            .all()
        all_info = db.query(func.count(CaseRepo.assign_category_three).label('query_count'),
                            CaseRepo.assign_category_three) \
            .filter(CaseRepo.deal_category_time is not None, CaseRepo.deal_depart_time is not None,
                    CaseRepo.finish_time is not None) \
            .filter(CaseRepo.occur_time.like('%' + dtstr + '%')) \
            .filter(CaseRepo.area_name.like('%' + area_name + '%')) \
            .filter(or_(CaseRepo.finish_category_big.like('%' + type_id_big + '%'),
                        CaseRepo.assign_category_big.like('%' + type_id_big + '%'))) \
            .filter(or_(CaseRepo.finish_category_small.like('%' + type_id_small + '%'),
                        CaseRepo.assign_category_small.like('%' + type_id_small + '%'))) \
            .filter(CaseRepo.assign_category_three == CaseRepo.finish_category_three) \
            .group_by(CaseRepo.assign_category_three).order_by('query_count desc') \
            .all()

    result = []
    for cat in all_info:
        result.append({
            'name': get_category_name(cat[1]),
            'score': cat[0] / (_get_count_(cat[1], all_count) * 1.0)
        })

    result.sort(key=lambda obj: obj.get('score'), reverse=True)

    str_result['msg'] = result[0: top]
    return json.dumps(str_result, encoding='utf8', ensure_ascii=False)


@app.route('/api/display/area', methods=['POST', ])
def count_area():
    """
    统计区域的信息
    不使用区域作为筛选条件
    :return: 区域的统计信息
    """

    def _get_count_(name, lst):
        for i in lst:
            if name == i[1]:
                return i[0]
        pass

    str_result = {'status': 1, 'msg': ''}

    try:
        data = json.loads(request.data.decode('utf8'))
    except Exception as msg:
        str_result['status'] = 0
        str_result['msg'] = '请使用Json对象上传参数' + str(msg)
        return jsonify(str_result)

    if 'date' not in data:
        dtstr = ''
    else:
        dtstr = data['date']

    """
    只处理大类下面的区县的正确率
    """
    if 'big_type' not in data:
        type_id_big = ''
    else:
        type_id_big = get_category_id(data['big_type'])
        if type_id_big is None:
            type_id_big = ''

    if 'top' not in data:
        top = 20
    else:
        top = data['top']
        if isinstance(top, int) is not True:
            str_result['status'] = 0
            str_result['msg'] = 'top参数只能是整数'
            return jsonify(str_result)

    db = load_session()
    all_count = db.query(func.count(CaseRepo.area_name).label('query_count'), CaseRepo.area_name) \
        .filter(CaseRepo.deal_category_time.isnot(None), CaseRepo.deal_depart_time.isnot(None),
                CaseRepo.finish_time.isnot(None)) \
        .filter(CaseRepo.occur_time.like('%{}%'.format(dtstr))) \
        .filter(CaseRepo.finish_category_big.like('%{}%'.format(type_id_big))) \
        .group_by(CaseRepo.area_name).order_by('query_count desc') \
        .all()

    all_info = db.query(func.count(CaseRepo.area_name).label('query_count'), CaseRepo.area_name) \
        .filter(CaseRepo.deal_category_time.isnot(None), CaseRepo.deal_depart_time.isnot(None),
                CaseRepo.finish_time.isnot(None)) \
        .filter(CaseRepo.occur_time.like('%{}%'.format(dtstr))) \
        .filter(CaseRepo.finish_category_big.like('%{}%'.format(type_id_big))) \
        .filter(or_(CaseRepo.is_category_correct.is_(True), CaseRepo.is_depart_correct.is_(True))) \
        .group_by(CaseRepo.area_name).order_by('query_count desc') \
        .all()

    result = []
    for area in all_info:
        result.append({
            'name': area[1],
            'score': area[0] / (_get_count_(area[1], all_count) * 1.0)
        })

    result.sort(key=lambda obj: obj.get('score'), reverse=True)

    str_result['msg'] = result[0:top]
    return json.dumps(str_result, encoding='utf8', ensure_ascii=False)


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


if __name__ == '__main__':
    app.run('0.0.0.0', 8000)
