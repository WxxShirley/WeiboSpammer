"""
计算文本相似度
"""

import csv
import numpy as np
import jieba
from math import sqrt


#中文分词
def segment(text):
    f = open("baidu_stopwords.txt","r")
    stopwords = {}.fromkeys(f.read().split("\n"))
    f.close()

    jieba.load_userdict("baidu_stopwords.txt")
    segs = jieba.cut(text)

    text_list = []
    for seg in segs:
        if seg not in text_list and seg!="":
            text_list.append(seg.replace(" ",""))
    return text_list

#文本相似度计算
def computeSimilarity(text1,text2):
    lis = text1+text2
    lis = set(lis)
    vec1,vec2 = {},{}
    for key in lis:
        vec1[key] = 0
        vec2[key] = 0
    
    for key in vec1.keys():
        for word in text1:
            if word==key:
                vec1[key]+=1
        for word in text2:
            if word==key:
                vec2[key]+=1
    val1 = [val for val in vec1.values()]
    val2 = [val for val in vec2.values()]

    sim = sum([val1[i]*val2[i] for i in range(len(val1))])/(sqrt(sum([v*v for v in val1]))*sqrt(sum([v*v for v in val2])))
    return sim

if __name__ == "__main__":
    
    with open("weibo.csv",'r') as file:
        reader = csv.reader(file)
        weibos = list(reader)
    
    id2weibo = {}

    for weibo in weibos:
        if weibo[1] in id2weibo.keys():
            id2weibo[weibo[1]][0]+=weibo[2]
        else:
            id2weibo[weibo[1]] = [weibo[2]]

    root = "6529218955"
    num = 0
    
    for id in id2weibo.keys():
        if id!=root:
            text1 = id2weibo[id][0]
            text2 = id2weibo[root][0]
            sim = computeSimilarity(segment(text1),segment(text2))
            num+=1
            print("-----------第{i}位用户处理完毕，微博内容相似度为{sim}------------".format(i=num,sim=sim))
            id2weibo[id].append(sim)
    
    total_sim = sum([id2weibo[id][1] for id in id2weibo.keys() if id!=root])
    
    print("-----------所有用户处理完毕，平均微博内容相似度为{sim}------------".format(sim=total_sim/num))


