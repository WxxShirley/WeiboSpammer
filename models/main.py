import csv
import datetime
from dateutil.parser import parse
import jieba
from string import punctuation
import re
import emoji
from collections import Counter
import numpy as np


def cos_sim(vector_a, vector_b):
    """
    计算两个向量之间的余弦相似度
    :param vector_a: 向量 a
    :param vector_b: 向量 b
    :return: sim
    """
    vector_a = np.mat(vector_a)
    vector_b = np.mat(vector_b)
    num = float(vector_a * vector_b.T)
    denom = np.linalg.norm(vector_a) * np.linalg.norm(vector_b)
    cos = num / denom
    sim = 0.5 + 0.5 * cos

    return sim


def sentences_cos_sim(list_1,list_2):
    '''
    计算两个文本之间的余弦相似度
    '''
    # 1.分词
    wb_1=[]
    wb_2=[]
    if type(list_1)==list:
        for sentence in list_1:
            seg_list=seg_sentence(sentence)
            wb_1=wb_1+seg_list
        for sentence in list_2:
            seg_list=seg_sentence(sentence)
            wb_2=wb_2+seg_list
    else:
        seg_list = seg_sentence(list_1)
        wb_1 = wb_1 + seg_list
        seg_list = seg_sentence(list_2)
        wb_2 = wb_2 + seg_list

    # 2.统计所有词组：
    wb = wb_1+wb_2
    wb=list(set(wb))

    # 3.获取词频：
    wb_1=Counter(wb_1)
    wb_2=Counter(wb_2)
    vec_1=[]
    vec_2=[]
    for w in wb:
        if wb_1.__contains__(w):
            vec_1.append(wb_1[w])
        else:
            vec_1.append(0)
    for w in wb:
        if wb_2.__contains__(w):
            vec_2.append(wb_2[w])
        else:
            vec_2.append(0)

    # 4.复杂度计算：
    ans = cos_sim(vec_1, vec_2)
    return ans

def one_day_sim(mylist):
    if len(mylist)<=1:
        return 0
    ans=0
    count=0
    for i in range(0,len(mylist)):
        for j in range(i+1,len(mylist)):
            count+=1
            ans+=sentences_cos_sim(mylist[i],mylist[j])
    return ans/count

# 创建停用词list
def stopwordslist(filepath):
    stopwords = [line.strip() for line in open(filepath, 'r', encoding='utf-8').readlines()]

    return stopwords

stopwords = stopwordslist('baidu_stopwords.txt')  # 这里加载停用词的路径

# 对句子进行分词
def seg_sentence(sentence):
    # 去除emoji
    sentence = emoji.demojize(sentence)
    # 英文标点符号+中文标点符号
    punc = punctuation + u"., ;《》？！“”‘’@  # ￥%…&×（）——+【】{};；●，。&～、|\s:："
    sentence=re.sub(r"[{}]+".format(punc),"",sentence)
    # 分词
    sentence_seged = jieba.cut(sentence.strip())
    # 去除停用词
    # stopwords = stopwordslist('baidu_stopwords.txt')  # 这里加载停用词的路径
    outstr = []
    for word in sentence_seged:
        if word not in stopwords:
            if word != '\t':
                outstr.append(word)
    return outstr

def read_user_info():
    with open('UserInfo.csv', newline='') as f:
        reader = csv.reader(f)
        lines = list(reader)

    # id,昵称,性别,所在地,关注数,粉丝数,微博数,创建时间,等级,会员等级,个人简介,教育经历,公司,阳光信用,类别
    header=lines[0]
    print("headers:")
    print(header)
    lines=lines[1:]
    data={}
    for line in lines:
        dict={}
        id=line[0]
        username=line[1]
        followee=int(line[4]) #F1 关注数
        follower=int(line[5]) #F2 粉丝数
        if follower==0:
            followee_follower_ratio=0
        else:
            followee_follower_ratio=round(followee/follower,2) # F4 关注粉丝比
        weibo=int(line[6]) # F7 微博数
        if line[-2]=='0':
            label=0
        else:
            label=1
        dict['id']=id
        dict['username']=username
        dict['F1']=followee
        dict['F2']=follower
        # dict['F4']=followee_follower_ratio
        dict['F7']=weibo
        data[id]=dict
        dict['label']=label
    return data

def read_weibo_single(id):
    with open('data/'+id+'.csv', newline='') as f:
        reader = csv.reader(f)
        lines = list(reader)
    # id,用户id,内容,发布时间,是否含url,评论数,转发数,点赞数,长度,是否原创
    total_weibo=len(lines)
    comments=0
    comments_origin=0
    origins=0
    urls=0
    lens=0
    months=[]
    now=datetime.datetime.now()
    most_recent=parse(lines[1][3])
    header=lines[0]
    lines=lines[1:]
    date_contents={}

    for line in lines:
        content=line[2]
        time=line[3]
        y_m=time.split(' ')[0][:-3]
        y_m_d = time.split(' ')[0]
        months.append(y_m)
        is_url = line[4]
        comment=int(line[5])
        repost=line[6]
        likes=line[7]
        length=int(line[8])
        is_origin=line[-1]

        if(is_origin):
            comments_origin=comments_origin+1
        comments=comments+comment
        origins=origins+int(is_origin)
        urls=urls+int(is_url)
        lens=lens+length

        # seg_list = seg_sentence(content)
        # print(content)
        # print(", ".join(seg_list))
        # print(seg_list)

        if not date_contents.__contains__(y_m_d):
            date_contents[y_m_d]=[]
        date_contents[y_m_d].append(content)

    months=list(set(months))

    F8=round(total_weibo/len(months),2)
    F9 = (now - most_recent).days
    F10=round((total_weibo-origins)/total_weibo,2) # 转发比(F10)
    F11=round((urls/total_weibo),2) # URL 链接比(F11)
    F12=round(comments/total_weibo,2) # 微博评论比(F12)
    if(origins==0):
        F13=0
    else:
        F13=round(comments_origin/origins,2)# 原创微博评论比(F13)
    F14=round(lens/total_weibo,2)

    mylist=[]
    for date,content in date_contents.items():
        mylist.append(content)
    if len(mylist)>1:
        sum=0
        for i in range(0,len(mylist)-1):
            sum+=sentences_cos_sim(mylist[i],mylist[i+1])
        F15=round(sum/(len(mylist)-1),2)
    else:
        F15=0
    sum=0
    for i in mylist:
        sum+=one_day_sim(i)

    F16=round(sum/len(mylist),2)

    dict={'F8':F8,'F9':F9,'F10':F10,'F11':F11,'F12':F12,'F13':F13,'F14':F14,'F15':F15,'F16':F16}
    return dict



def read_weibo(data):
    with open("weibo.csv") as f:
        reader=csv.reader(f)
        lines=list(reader)
    print("len(lines)",len(lines))
    # id,用户id,内容,发布时间,是否含url,评论数,转发数,点赞数,长度,是否原创
    header=lines[0]
    lines=lines[1:]
    weibo={}
    ids=[]
    for line in lines:
        id=line[1]
        ids.append(id)
        if not weibo.__contains__(id):
            weibo[id]=[]
        weibo[id].append(line)

    # write files out: one file per user
    for key,value in weibo.items():
        with open("data/"+key+".csv",'w',newline='') as f:
            wr = csv.writer(f)
            wr.writerow(header)
            wr.writerows(value)

    ids=list(set(ids))
    print("dataset contains ",len(ids),"users");


    for id in ids:
        dict=read_weibo_single(id)
        if data.__contains__(id):
            data[id]={**data[id],**dict}
            print(id,data[id])
            keys = data[id].keys()
            print("keys:",keys)
            with open('test_2.csv', 'a+') as output_file:
                dict_writer = csv.DictWriter(output_file, keys)
                dict_writer.writerow(data[id])
        else:
            print("id:",id,"not in userinfo.csv")

def main():
    data=read_user_info()
    ids_1=[value['id'] for key,value in data.items()]
    print(len(list(set(ids_1))))

    read_weibo(data)
    # for i in data.items():
    #     print(i)

if __name__  == '__main__':
    main()
