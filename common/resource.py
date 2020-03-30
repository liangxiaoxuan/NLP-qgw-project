import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 分词算法所需文件
PALY = os.path.join(BASE_DIR, '../resources/word_bag/paly.model')
WORD_BAG = os.path.join(BASE_DIR, '../resources/word_bag/')

# 全新二级委派模型
YUNYAN_LBL = os.path.join(BASE_DIR, '../resources/new_tier2_model/yunyan/yunyan_lbl.joblib')
YUNYAN_TFIDF = os.path.join(BASE_DIR, '../resources/new_tier2_model/yunyan/yunyan_tfidf.joblib')
YUNYAN_VEC = os.path.join(BASE_DIR, '../resources/new_tier2_model/yunyan/yunyan_vec.joblib')
YUNYAN_RF = os.path.join(BASE_DIR, '../resources/new_tier2_model/yunyan/yunyan_rf.joblib')

NANMING_LBL = os.path.join(BASE_DIR, '../resources/new_tier2_model/nanming/nanming_lbl.joblib')
NANMING_TFIDF = os.path.join(BASE_DIR, '../resources/new_tier2_model/nanming/nanming_tfidf.joblib')
NANMING_VEC = os.path.join(BASE_DIR, '../resources/new_tier2_model/nanming/nanming_vec.joblib')
NANMING_RF = os.path.join(BASE_DIR, '../resources/new_tier2_model/nanming/nanming_rf.joblib')

BAIYUN_LBL = os.path.join(BASE_DIR, '../resources/new_tier2_model/baiyun/baiyun_lbl.joblib')
BAIYUN_TFIDF = os.path.join(BASE_DIR, '../resources/new_tier2_model/baiyun/baiyun_tfidf.joblib')
BAIYUN_VEC = os.path.join(BASE_DIR, '../resources/new_tier2_model/baiyun/baiyun_vec.joblib')
BAIYUN_RF = os.path.join(BASE_DIR, '../resources/new_tier2_model/baiyun/baiyun_rf.joblib')

HUAXI_LBL = os.path.join(BASE_DIR, '../resources/new_tier2_model/huaxi/huaxi_lbl.joblib')
HUAXI_TFIDF = os.path.join(BASE_DIR, '../resources/new_tier2_model/huaxi/huaxi_tfidf.joblib')
HUAXI_VEC = os.path.join(BASE_DIR, '../resources/new_tier2_model/huaxi/huaxi_vec.joblib')
HUAXI_RF = os.path.join(BASE_DIR, '../resources/new_tier2_model/huaxi/huaxi_rf.joblib')

WUDANG_LBL = os.path.join(BASE_DIR, '../resources/new_tier2_model/wudang/wudang_lbl.joblib')
WUDANG_TFIDF = os.path.join(BASE_DIR, '../resources/new_tier2_model/wudang/wudang_tfidf.joblib')
WUDANG_VEC = os.path.join(BASE_DIR, '../resources/new_tier2_model/wudang/wudang_vec.joblib')
WUDANG_RF = os.path.join(BASE_DIR, '../resources/new_tier2_model/wudang/wudang_rf.joblib')

GUANSHANHU_LBL = os.path.join(BASE_DIR, '../resources/new_tier2_model/guanshanhu/guanshanhu_lbl.joblib')
GUANSHANHU_TFIDF = os.path.join(BASE_DIR, '../resources/new_tier2_model/guanshanhu/guanshanhu_tfidf.joblib')
GUANSHANHU_VEC = os.path.join(BASE_DIR, '../resources/new_tier2_model/guanshanhu/guanshanhu_vec.joblib')
GUANSHANHU_RF = os.path.join(BASE_DIR, '../resources/new_tier2_model/guanshanhu/guanshanhu_rf.joblib')

QINGZHEN_LBL = os.path.join(BASE_DIR, '../resources/new_tier2_model/qingzhen/qingzhen_lbl.joblib')
QINGZHEN_TFIDF = os.path.join(BASE_DIR, '../resources/new_tier2_model/qingzhen/qingzhen_tfidf.joblib')
QINGZHEN_VEC = os.path.join(BASE_DIR, '../resources/new_tier2_model/qingzhen/qingzhen_vec.joblib')
QINGZHEN_RF = os.path.join(BASE_DIR, '../resources/new_tier2_model/qingzhen/qingzhen_rf.joblib')

XIFENG_LBL = os.path.join(BASE_DIR, '../resources/new_tier2_model/xifeng/xifeng_lbl.joblib')
XIFENG_TFIDF = os.path.join(BASE_DIR, '../resources/new_tier2_model/xifeng/xifeng_tfidf.joblib')
XIFENG_VEC = os.path.join(BASE_DIR, '../resources/new_tier2_model/xifeng/xifeng_vec.joblib')
XIFENG_RF = os.path.join(BASE_DIR, '../resources/new_tier2_model/xifeng/xifeng_rf.joblib')

KAIYANG_LBL = os.path.join(BASE_DIR, '../resources/new_tier2_model/kaiyang/kaiyang_lbl.joblib')
KAIYANG_TFIDF = os.path.join(BASE_DIR, '../resources/new_tier2_model/kaiyang/kaiyang_tfidf.joblib')
KAIYANG_VEC = os.path.join(BASE_DIR, '../resources/new_tier2_model/kaiyang/kaiyang_vec.joblib')
KAIYANG_RF = os.path.join(BASE_DIR, '../resources/new_tier2_model/kaiyang/kaiyang_rf.joblib')

XIUWEN_LBL = os.path.join(BASE_DIR, '../resources/new_tier2_model/xiuwen/xiuwen_lbl.joblib')
XIUWEN_TFIDF = os.path.join(BASE_DIR, '../resources/new_tier2_model/xiuwen/xiuwen_tfidf.joblib')
XIUWEN_VEC = os.path.join(BASE_DIR, '../resources/new_tier2_model/xiuwen/xiuwen_vec.joblib')
XIUWEN_RF = os.path.join(BASE_DIR, '../resources/new_tier2_model/xiuwen/xiuwen_rf.joblib')


# 分派案件所需模型
# WEIGHT_MATRIX = os.path.join(BASE_DIR, '../resources/Case_Assign/time_weight_matrix2.npy')
# EVENT_CAT = os.path.join(BASE_DIR, '../resources/Case_Assign/案件类别.txt')

MINI_WORD = os.path.join(BASE_DIR, '../resources/Case_Assign/mini_word_database.csv')
TIER2_GRID = os.path.join(BASE_DIR, '../resources/Case_Assign/tier2_grid_assign.csv')
TIER3_GRID = os.path.join(BASE_DIR, '../resources/Case_Assign/tier3_grid_assign.csv')

TIER2_LINK = os.path.join(BASE_DIR, '../resources/Case_Assign/tier2_prop.csv')
TIER2_LINK_KEYWORD = os.path.join(BASE_DIR, '../resources/Case_Assign/tier2_linkunit_keyword.txt')
TIER3_LINK = os.path.join(BASE_DIR, '../resources/Case_Assign/tier3_prop.csv')
TIER3_LINK_KEYWORD = os.path.join(BASE_DIR, '../resources/Case_Assign/tier3_linkunit_keyword.txt')
TIER4_LINK = os.path.join(BASE_DIR, '../resources/Case_Assign/tier4_prop.csv')
TIER4_LINK_KEYWORD = os.path.join(BASE_DIR, '../resources/Case_Assign/tier4_linkunit_keyword.txt')


# 自学习部分
CLOSE_EVENT = os.path.join(BASE_DIR, '../resources/Case_Assign/CloseEvent.csv')
MATRIX_NEW2 = os.path.join(BASE_DIR, '../resources/Case_Assign/matrix_new2.npy')
STOP_WORDS1 = os.path.join(BASE_DIR, '../resources/Case_Assign/stop_words1.txt')


DATA_FILE = os.path.join(BASE_DIR, '../resources/data.txt')
DATA_TYPE_FILE = os.path.join(BASE_DIR, '../resources/data_type.txt')
DATA_UNIT_FILE = os.path.join(BASE_DIR, '../resources/data_unit.txt')

# 训练的数据
DETAIL_TRAIN_FILE = os.path.join(BASE_DIR, '../resources/train_data/detail_train.txt')
TYPE_TRAIN_FILE = os.path.join(BASE_DIR, '../resources/train_data/type_train.txt')

TYPE_SET_FILE = os.path.join(BASE_DIR, '../resources/type_set.txt')
TYPE_ADDRESS_TRAIN_FILE = os.path.join(BASE_DIR, '../resources/type_address_train.txt')
DEPARTMENT_TRAIN_FILE = os.path.join(BASE_DIR, '../resources/department_train.txt')
DEPARTMENT_SET_FILE = os.path.join(BASE_DIR, '../resources/department_set.txt')
NEW_TYPE_MAPPING_FILE = os.path.join(BASE_DIR, '../resources/new_type_mapping.txt')
TYPE_ORG_UNIT_FILE = os.path.join(BASE_DIR, '../resources/type_org_unit.txt')

# 训练的模型
TYPE_VEC_FILE = os.path.join(BASE_DIR, '../resources/model_data/vec_count.joblib')
TYPE_CLF_FILE = os.path.join(BASE_DIR, '../resources/model_data/clf.joblib')
TYPE_TFIDF_FILE = os.path.join(BASE_DIR, '../resources/model_data/vec_tfidf.joblib')

JIEBA_USER_DICT_FILE = os.path.join(BASE_DIR, '../resources/extra_dict/user_dict.txt')
JIEBA_USER_DICT_ALL_FILE = os.path.join(BASE_DIR, '../resources/extra_dict/user_dict_all.txt')
JIEBA_USER_DICT_SHORT_FILE = os.path.join(BASE_DIR, '../resources/extra_dict/user_dict_short.txt')
JIEBA_USER_DICT_STOP_WORDS_FILE = os.path.join(BASE_DIR, '../resources/extra_dict/stop_words.txt')
JIEBA_SYS_STUDY_DICT_FILE = os.path.join(BASE_DIR, '../resources/extra_dict/sys_study_dict.txt')

# 区、县
DISTRICT_COUNTY_FILE = os.path.join(BASE_DIR, '../resources/location/district_county.txt')
# 街道、乡、镇
STREETS_TOWNSHIPS_TOWNS_FILE = os.path.join(BASE_DIR, '../resources/location/streets_townships_towns.txt')
# 居委会、村
COMMUNITIES_VILLAGES_FILE = os.path.join(BASE_DIR, '../resources/location/communities_villages.txt')

PAID_INDEX_PICKLE_FILE = os.path.join(BASE_DIR, '../resources/paid_index.txt')

DEPARMENT_LIST = os.path.join(BASE_DIR, '../resources/department/department.txt')

JAVA_WORD_DETAIL_TRAIN_FILE = os.path.join(BASE_DIR, '../resources/java_word_dict/detail_train_set.txt')
JAVA_WORD_TYPE_TRAIN_FILE = os.path.join(BASE_DIR, '../resources/java_word_dict/type_train_set.txt')

#处理数据时生成的文件
NONE_DEPARTMENT_FILE = os.path.join(BASE_DIR, '../resources/none_department.txt')
TYPE_WEIGHT_DATA_FILE = os.path.join(BASE_DIR, '../resources/type_weight_data.txt')
UNIT_WEIGHT_DATA_FILE = os.path.join(BASE_DIR, '../resources/unit_weight_data.txt')

LOG_CONF = os.path.join(BASE_DIR, '../conf/logger.conf')
OLD_DATA_FILE = os.path.join(BASE_DIR, '../resources/old_data.txt')
NEW_DATA_FILE = os.path.join(BASE_DIR, '../resources/new_data.txt')
CLASS_WEIGHT_FILE = os.path.join(BASE_DIR, '../resources/class_weight.txt')
CASE_SOURCE_FILE = os.path.join(BASE_DIR, '../resources/visualize_data/case_source.txt')
AREA_FILE = os.path.join(BASE_DIR, '../resources/visualize_data/area.txt')
CATEGORY_FILE = os.path.join(BASE_DIR, '../resources/案件类别.csv')

ALL_NEW_DATA_FILE = os.path.join(BASE_DIR, '../resources/自流程初始化数据2017-05-10.xlsx')

CASE_FINISHED_JSON_FILE = os.path.join(BASE_DIR, '../resources/validate_data/case_finished.json')


def main():
    with open(DISTRICT_COUNTY_FILE, 'r', encoding='utf-8') as f:
        for row in f.readlines():
            print(row)


if __name__ == '__main__':
    main()
