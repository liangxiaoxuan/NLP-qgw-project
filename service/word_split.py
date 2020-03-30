import re
import zipfile
import sys
import os
from qgw_autoflow.common.resource import PALY, WORD_BAG

# 正则匹配日期，数字，英语单词
date_rg = r'(\d{4}年\d{1,2}月\d{1,2}日)|(\d{4}\S\d{1,2}\S\d{1,2})|([A-Za-z0-9]*)'
# 标记非中文字符
flags = list(range(47, 56)) + list(range(64, 90)) + list(range(96, 123))
ds = dict(map(lambda x: (x, True), flags))
deviation = int()  # 最大词语个数
d = dict()
ls_length = 0


def read_txt(filename):
    """
    读取文本
    :param filename: 文本名
    :return: 有序链表
    """
    with open(file=WORD_BAG+filename, mode='r', encoding='utf-8')as fs:
        s = [f[:-1] for f in fs]
        ls = sorted(s)
        fs.close()
        return ls


def load(max_auto=False):
    """
    加载默认词语(来源于搜狗全部词条：700万个词语)包括90%的领域词，详细请看 https://gitee.com/tyoui/word/raw/master/README.md
    加载百度百科全部词条。大概1400万个词语
    加载维基百科中文全部词条。大概800万个词语
    除去单字，非中文词。乱词。非法词等，大概1700万词语.
    所包括的领域上千种。最长的词语100多字，是有机化学名
    :param max_auto: 是否开启最大识别词语个数
    :return: 默认词条链表
    """
    global deviation, ls_length, d
    fs = zipfile.ZipFile(PALY, 'r')
    f = fs.open(fs.namelist()[0], mode='r')
    s = list()
    flag_head = ['龙', 0]
    flag = 0
    while True:
        st = f.readline()
        if st:
            st = st.decode('utf-8')
            s.append(st[:-1])
            flag_tail = st[0]
            if flag_head[0] != flag_tail:
                d[flag_head[0]] = [flag_head[1], flag - 1]
                flag_head[0] = flag_tail
                flag_head[1] = flag
        else:
            break
        flag += 1
    ls_length = len(s)

    if max_auto:
        max_ls(s)
    else:
        deviation = 10
    return s


def max_ls(ls):
    """
    识别所有词语中最大的个数
    :param ls: 全部词条
    :return: None
    """
    global deviation
    deviation = max(map(lambda x: len(x), ls))


def search(ls, key, quick=False):
    """
    匹配算法：二分法算法
    :param ls: 加载所有的词条
    :param key: 需要分割的其中一个词语
    :param quick:是否启用快速查找
    :return: 找到返回词语位置
    """
    if quick:
        dc = d.get(key[0])
        if dc:
            low = dc[0]
            high = dc[1]
        else:
            low = 0
            high = ls_length - 1
    else:
        low = 0
        high = len(ls) - 1
    while low <= high:
        mid = (low + high) // 2

        if key < ls[mid]:
            high = mid - 1
        elif key > ls[mid]:
            low = mid + 1
        else:
            return mid
    return -1


def mate_num(obj):
    """
    需要匹配数字，英语，日期这些特殊词
    :param obj: 从识别开头是非中文字符到后10位的词语
    :return: 匹配到返回匹配的开始和结束
    """
    r = re.match(date_rg, obj, re.M | re.I)
    if r:
        return r.span()
    return None


def mates(ls, words):
    """
    匹配算法
    :param ls: 全部的词条
    :param words: 需要分割的词语
    :return: 分割后的词语
    """

    stop_ls = read_txt('stop.txt')
    text = list()
    m = len(words)
    k = 0
    while k < m:
        flag = 0
        ws = words[k]
        if ds.get(ord(ws)):  # 判断当前这个字。是否是非中文字符
            num = mate_num(words[k:k + 10])  # 提取当前到后10位作为词语进行非中文匹配
            if num:
                word = words[k:k + num[1]]
                k += num[1]
                if search(stop_ls, word) == -1:
                    text.append(word)
                continue
        for d in range(deviation):  # 词语分割的偏移量
            word = words[k:k + 2 + d]
            if search(ls, word, quick=True) > -1:
                ws = word
                flag = k + 2 + d
            if k + 2 + d >= m:
                break
        if flag:  # 时候分割到词语，flag=0,说明当前这个不是词语
            k = flag
        else:
            k += 1
        if search(stop_ls, ws) == -1:
            text.append(ws)
    text = " ".join(text)
    return text


if __name__ == '__main__':
    ls = load(True)
    a = mates(ls, '观山湖区有人打架')
    print(a)
