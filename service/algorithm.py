from sklearn import svm
from sklearn.externals import joblib
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.model_selection import train_test_split

from qgw_autoflow.common.resource import (DETAIL_TRAIN_FILE,
                                          TYPE_CLF_FILE, TYPE_TFIDF_FILE,
                                          TYPE_TRAIN_FILE, TYPE_VEC_FILE)


def cn_word_split(s):
    return s.split()


def get_train_data():
    """
        读取处理后的数据
        :return:案件详细列表，案件类别数字类别
        """
    detail_data = []
    type_data = []
    with open(DETAIL_TRAIN_FILE, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            detail_data.append(line.strip())
    with open(TYPE_TRAIN_FILE, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            type_data.append(int(line.strip()))
    # detail_data = detail_data[:10000]
    # type_data = type_data[:10000]
    return detail_data, type_data


def build_model():
    """
        构建模型,先将数据分为测试集和训练集，然后训练，保存模型，进行测试
        :return:
        """
    detail_data, type_data = get_train_data()

    train_data, test_data, train_label, test_label = train_test_split(detail_data, type_data, test_size=0.1)
    from qgw_autoflow.service.algorithm import cn_word_split
    vec = CountVectorizer(analyzer=cn_word_split)
    train_data_features = vec.fit_transform(train_data)
    tfidf = TfidfTransformer()
    train_data_tfidf = tfidf.fit_transform(train_data_features)

    # class_weight = {}
    # with open(CLASS_WEIGHT_FILE, 'r', encoding='utf-8') as f:
    #     for line in f.readlines():
    #         line = line.strip()
    #         k, v = line.split('$')
    #         k = int(k)
    #         if k in train_label:
    #             class_weight[k] = float(v)
    clf = svm.LinearSVC(C=1, )
    clf.fit(train_data_tfidf, train_label)
    joblib.dump(vec, TYPE_VEC_FILE)
    joblib.dump(tfidf, TYPE_TFIDF_FILE)
    joblib.dump(clf, TYPE_CLF_FILE)

    # 加载模型
    vec = joblib.load(TYPE_VEC_FILE)
    tfidf = joblib.load(TYPE_TFIDF_FILE)
    clf = joblib.load(TYPE_CLF_FILE)

    test_data_features = vec.transform(test_data)
    test_data_tfidf = tfidf.transform(test_data_features)

    print("测试结果：", clf.score(test_data_tfidf, test_label))


def main():
    build_model()
    # vec = joblib.load(TYPE_VEC_FILE)
    # tfidf = joblib.load(TYPE_TFIDF_FILE)
    # test_data_featuress = vec.transform(['有人 来电 乱 停车'])
    # x = vec.inverse_transform(test_data_featuress)
    #
    # test_data_tfidf = tfidf.transform(test_data_featuress)
    # y = vec.inverse_transform(test_data_tfidf)
    # print(test_data_featuress)
    # print(test_data_tfidf.data)
    pass


if __name__ == '__main__':
    main()
