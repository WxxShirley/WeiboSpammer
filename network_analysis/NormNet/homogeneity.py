"""
计算网络的同质性，包括
 - 好友网络间地区的一致性、微博内容的相似度
"""
import csv
from pyecharts import options as opts
from pyecharts.charts import Geo,Page,Graph
from pyecharts.globals import ChartType, SymbolType

import math

import numpy as np
import pickle
from pyecharts.render import make_snapshot
from snapshot_phantomjs import snapshot

import json
import matplotlib 
import matplotlib.pyplot as plt

import jieba
from wordcloud import WordCloud
import matplotlib.font_manager as fm
from imageio import imread
from PIL import Image
import wordcloud

from snapshot_selenium import snapshot

"""
该社交网络中，所有用户与好友间地区一致的平均比例为17.278%
微博内容相似度为18.024%

"""

from textSimi import segment,computeSimilarity

def generateRelation():
    """ 同质性：计算用户与好友间地区一致的比例 """
    with open("user_detail.csv",'r') as file:
        reader = csv.reader(file)
        users = list(reader)
    
    id2area = {}
    for u in users:
        if u[0] not in id2area.keys():
            id2area[u[0]] = u[3]

    with open("Edges.csv",'r') as file:
        reader = csv.reader(file)
        edges = list(reader)
    
    id2friend = {}
    for e in edges:
        if e[0] not in id2friend.keys():
            id2friend[e[0]] = [e[1]]
        else:
            if e[1] not in id2friend[e[0]]:
                id2friend[e[0]].append(e[1])
        if e[1] not in id2friend.keys():
            id2friend[e[1]] = [e[0]]
        else:
            if e[0] not in id2friend[e[1]]:
                id2friend[e[1]].append(e[0])
    
    id2areaSim = {}
    for id in id2friend.keys():
        friends = id2friend[id]
        if id not in id2area.keys():
            continue
        else:
            area = id2area[id].split(" ")[0]
            cnt = 0
            for f in friends:
                if f in id2area.keys():
                    f_area = id2area[f].split(" ")[0]
                    if f_area==area:
                        cnt+=1
            id2areaSim[id] = cnt/len(friends)

    total = sum(id2areaSim.values())
    print(total/len(id2friend))



def weiboSimilarity():
    """ 计算每位用户和好友的微博内容相似度 """
    with open("weibo.csv",'r') as file:
        reader = csv.reader(file)
        weibos = list(reader)
    
    id2weibo = {}

    for weibo in weibos:
        if weibo[1] not in id2weibo.keys():
            id2weibo[weibo[1]] = weibo[2]
        else:
            id2weibo[weibo[1]]+=weibo[1]
    
    ids = id2weibo.keys()

    print(len(ids))

    with open("Edges.csv",'r') as file:
        reader = csv.reader(file)
        edges = list(reader)
    
    id2sim = {}
    edges = edges[1:]
    for e in edges:
        source ,target = e[0],e[1]
        if source not in id2weibo.keys() or target not in id2weibo.keys():
            continue

        source_text, target_text = id2weibo[source],id2weibo[target]
        
        sim = computeSimilarity(segment(source_text),segment(target_text)) #余弦相似度 
        if source not in id2sim.keys():
            id2sim[source] = [[target,sim]]
        else:
            if [target,sim] not in id2sim[source]:
                id2sim[source].append([target,sim])
        if target not in id2sim.keys():
            id2sim[target] = [[source,sim]]
        else:
            if [source,sim] not in id2sim[target]:
                id2sim[target].append([source,sim])
    
    id2finalSim = {}

    for id in id2sim.keys():
        sim_list = id2sim[id]
        avg_sim = sum([sim_list[i][1] for i in range(len(sim_list))])/len(sim_list)
        id2finalSim[id] = avg_sim
    
    print(id2finalSim)

    val = id2finalSim.values()

    sorted(id2finalSim.items(), key = lambda d:d[1])

    with open("textSim.txt",'w') as file:
        for key in id2finalSim.keys():
            file.write(key+" "+str(id2finalSim[key])+"\n") #将每位用户和好友微博内容相似度写入txt文件

    return sum(val)/len(val) #返回均值



def repostNetwork_prepare():
    """ 构成用户微博内容的转发关系网络 """
    def getATidx(s):
        i = 0
        for i in range(len(s)):
            if s[i]=='@':
                break
            else:
                i+=1
        return i
    def get1st(s,start):
        i = 0
        for i in range(start,len(s)):
            if s[i]==':' or s[i]==' ':
                break
            else:
                i+=1
        return i
    

    # get network all names && id2nickname
    id2nickname ,nicknames2fannum= {},{}

    with open("User.csv",'r') as file:
        reader = csv.reader(file)
        users = list(reader)
    nicknames = []
    for u in users:
        if u[1] not in nicknames:
            nicknames.append(u[1])
        id2nickname[u[0]] = u[1]
        if u[2]!= "fans_num":
            nicknames2fannum[u[1]] = eval(u[2])

    # 保存转发关系
    repost = [] # [[source_nickname, target_nickname]]

    with open("weibo.csv",'r') as file:
        reader = csv.reader(file)
        weibos = list(reader)
    names = []
    for weibo in weibos:
        content, user_nickname = weibo[2],id2nickname[weibo[1]]
        i=getATidx(content)
        if i!=len(content):
            j = get1st(content,i)
            name = content[i+1:j] #得到微博转发的用户名
            if '@' in name:  # 根据微博内容中的"@"关系来得到转发关系，截取出被转发的用户
                lis = name.split("@")
                for n in lis:
                    if n in nicknames:  
                        repost.append(user_nickname,n)
            else:
                if name in nicknames:
                    repost.append([user_nickname,name])
    
    # 我们用Echarts进行网路可视化，因此需要准备 nodes.json, links.json, category.json三个文件
    # nodes.json  节点（必须唯一，否则渲染的网络界面是空白)
    # links.json  节点间连接关系
    # category.json 被转发的节点集合
    
    nodes, cats = [], []
    nicks ,links, category = [], [], []
    for rep in repost:
        source, target = rep[0], rep[1]
        if source not in nicks:
            nicks.append(source)
            nodes.append({"name":source,"category":target,"symbolSize":15,"draggable":"True","value":nicknames2fannum[source]})
        if target not in nicks:
            nicks.append(target)
            nodes.append({"name":target,"symbolSize":25,"draggable":"True","value":nicknames2fannum[target]})
        if source!=target:
            links.append({"source":source,"target":target})
        if target not in cats:
            category.append({"name":target})
            cats.append(target)
    
    with open("./repost_json/nodes.json",'w',encoding="utf-8-sig") as file:
        json.dump(nodes,file,indent=2,sort_keys=True, ensure_ascii=False)
    file.close()

    with open("./repost_json/links.json",'w',encoding="utf-8-sig") as file:
        json.dump(links,file,indent=2,sort_keys=True, ensure_ascii=False)
    file.close()
    
    with open("./repost_json/category.json",'w',encoding="utf-8-sig") as file:
        json.dump(category,file,indent=2,sort_keys=True, ensure_ascii=False)
    file.close()


# 读转发网络的数据，Echarts可视化网络
def generateRepostNetwork():
    # 加载数据
    with open("./repost_json/nodes.json",'r',encoding='utf-8-sig') as f:
        nodes = json.load(f)
    with open("./repost_json/links.json",'r',encoding='utf-8-sig') as f:
        links = json.load(f)
    with open("./repost_json/category.json",'r',encoding='utf-8-sig') as f:
        category = json.load(f)
    
    c = (
        Graph()
        .add(
            "",nodes,links, category, repulsion=180,linestyle_opts=opts.LineStyleOpts(curve=0.5),
            label_opts=opts.LabelOpts(is_show=True),
        )
        .set_global_opts(
            legend_opts=opts.LegendOpts(is_show=False),
            title_opts=opts.TitleOpts(title="正常用户网络中转发关系图")
        )
    )
    return c
    
# 生成词云统计 用户微博内容与好友微博内容
def plotWordColud(user_id):
    user_text, friend_text = "",""
    with open("weibo.csv",'r') as file:
        reader = csv.reader(file)
        weibos = list(reader)
    
    with open("Edges.csv",'r') as file:
        reader = csv.reader(file)
        edges = list(reader)
    friends = []
    for edge in edges:
        if edge[0]==user_id:
            if edge[1] not in friends:
                friends.append(edge[1])
        if edge[1]==user_id:
            if edge[0] not in friends:
                friends.append(edge[0])
    
    for weibo in weibos:
        if weibo[1]==user_id:
            user_text+=weibo[2]
        if weibo[1] in friends:
            friend_text+=weibo[2]
    
    user_text_list = segment(user_text)
    friend_text_list = segment(friend_text)

    user_ = ",".join(user_text_list)
    friend_ = ",".join(friend_text_list)
    
    #设定指定的背景
    jpg = imread('logo.jpg') 
    mask = np.array(Image.open('logo.jpg'))
    image_colors = wordcloud.ImageColorGenerator(mask)
    
    #保存
    wc = WordCloud(background_color="white",max_words=200,min_font_size=10,max_font_size=35,width=400,font_path="/Users/wu/Downloads/msyh/msyh.ttf",mask=mask,color_func=image_colors)
    wc.generate(user_)
    file_path = "./wordCloud/user_.png"
    wc.to_file(file_path)

    wc.generate(friend_)
    file_path = "./wordCloud/friend_.png"
    wc.to_file(file_path)


def targetuser_fansMap(user_id):
    """ 画某个用户粉丝的地图流向图 """
    # ID:5573397816 / 1088908201（江苏）
    fans ,follows = [], []
    with open("Edges.csv",'r') as file:
        reader = csv.reader(file)
        edges = list(reader)
    for edge in edges:
        if edge[1]==user_id and edge[0] not in fans:
            fans.append(edge[0])
        if edge[0]==user_id and edge[1] not in follows:
            follows.append(edge[1])

    id2area = {}

    with open("user_detail.csv") as file:
        reader = csv.reader(file)
        users = list(reader)
    
    for user in users:
        location = user[3].split(" ")[0]
        id2area[user[0]] = location
    
    target = id2area[user_id]
    source ,fs = {},{}

    provin = '北京，天津，上海，重庆，河北，山西，辽宁，吉林，黑龙江，江苏，浙江，安徽，福建，江西，山东，河南，湖北，湖南，广东，海南，四川，贵州，云南，陕西，甘肃，青海，台湾，内蒙古，广西，西藏，宁夏，新疆，香港，澳门'
    provins = provin.split("，")

    for fan in fans:
        if fan in id2area.keys() and id2area[fan] in provins:
            if id2area[fan] not in source.keys():
                source[id2area[fan]]=1
            else:
                source[id2area[fan]]+=1
    
    for f in follows:
        if f in id2area.keys() and id2area[f] in provins:
            if id2area[f] not in fs.keys():
                fs[id2area[f]]=1
            else:
                fs[id2area[f]]+=1
    
    fans_key = [key for key in source.keys() if source[key]>1]
    follows_key = [key for key in fs.keys() if fs[key]>1]
    
    keys = set(fans_key+follows_key)
    pairs = []
    for key in keys:
        cnt = 0
        if key in source.keys():
            cnt+=source[key]
        if key in fs.keys():
            cnt+=fs[key]
        
        pairs.append([key,cnt])


    edge1 = [ (key,target) for key in fans_key  ]
    edge2 = [(target,key) for key in follows_key]
    new_edges = edge1+edge2
    
    c = ( 
        Geo()
        .add_schema(maptype="china",)
        .add("城市",pairs,type_=ChartType.HEATMAP)
        .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
        .set_global_opts(
            visualmap_opts=opts.VisualMapOpts(),
            title_opts=opts.TitleOpts(title="城市分布"),
        )
        .add("流向",new_edges,type_=ChartType.LINES, linestyle_opts=opts.LineStyleOpts(curve=0.3,color="#63B8FF"),
          effect_opts=opts.EffectOpts(symbol=SymbolType.ARROW,symbol_size=1,color="#FF7F00"),
          label_opts=opts.LabelOpts(is_show=False)
        )
        .set_global_opts(
            visualmap_opts=opts.VisualMapOpts(min_=1,max_=10)
        )
    )
    return c




if __name__ == "__main__":
    #generateRelation()
    #print(weiboSimilarity())

    #weiboInteraction()
 
    #generateRepostNetwork().render(u'./repost_json/repost_network.html')

    #plotWordColud("6096280483")
    #targetuser_fansMap("1088908201") #5573397816
    
    make_snapshot(snapshot,targetuser_fansMap("5573397816").render(),"./network_ChinaMap/user2.png")
    
    