"""
爬取指定根节点用户的三阶粉丝网络
"""

import requests
import json
import csv 
import jsonpath
import random
from time import sleep
#https://m.weibo.cn/api/container/getIndex?containerid=231051_-_fans_-_6338550883&since_id=
# Settings
urlTemplate = "https://m.weibo.cn/api/container/getIndex?containerid=231051_-_fans_-_{uid}&since_id="

cookie = "YOUR_COOKIE"


def get_fans_network(user_id):
    """ 爬取指定用户的三阶粉丝网络 """
    users = ["6099859539"] # root user

    num = 0 # control the number you want to crawl
    
    # store following-relationship: {"source":source_user.id, "target":target_user.id} 
    followship = []

    # store user_info
    userInfo = []

    # store userId lists to avoid repeatment
    userId = ["6099859539"]  # this user's information is not append in nodes
    
    flag = True
    layer = 1
    while True:
        size = len(users)
        print("-------------Layer{layerNum}------------".format(layerNum=layer))
        for i in range(size):
            target_user = users[0]
            users = users[1:]
            sleep(random.randint(6, 10)) #随机休眠
            for offset in range(1,4):
                url = urlTemplate.format(uid = target_user) + str(offset)
                myHeader['User-Agent'] = random.choice(user_agents)
                response = requests.get(url,headers = myHeader)
                
                # unspecial conditions
                if response==b'':
                    break
                
                try:
                    result = json.loads(response.text)
                except Exception as e:
                    break
                if result['ok']==0:
                    break
                
                try:
                    cardgroup = jsonpath.jsonpath(result,"$..card_group")[0]
                except Exception as e:
                    break

                for fan in cardgroup:
                    try:
                        id = jsonpath.jsonpath(fan, "$..id")[0]
                        nickname = jsonpath.jsonpath(fan, "$..screen_name")[0]
                        followers_count = jsonpath.jsonpath(fan, "$..followers_count")[0]
                        following_count = jsonpath.jsonpath(fan, "$..follow_count")[0]
                        description = jsonpath.jsonpath(fan, "$..desc1")[0]
                        print(num,id,nickname,followers_count,following_count,description)
                        
                        if str(id) not in userId:
                            userId.append(str(id))
                            users.append(id)
                            userInfo.append({"id":id,"nickname":nickname,"followers_count":followers_count,"following_count":following_count,"description":description})
                            num += 1
                        followship.append({"source":id,"target":target_user})
                    except Exception as e:
                        print(e)
            if num>900:
                flag = False
                break
        if flag==False:
            break

        layer += 1
    
    # 结果写入csv
    f1 = open("User.csv",'w',encoding='utf-8-sig')

    csv_writer = csv.writer(f1)
    csv_writer.writerow(['id','昵称','粉丝数','关注数','个人简介'])
    for user_info in userInfo:
        csv_writer.writerow([val for val in user_info.values()])
    f1.close()

    f2 = open("Edge.csv",'w',encoding='utf-8-sig')
    csv_writer = csv.writer(f2)
    csv_writer.writerow(['source','target'])
    for edge in followship:
        csv_writer.writerow([edge["source"],edge["target"]])
    f2.close()


def generate_more_edges():
    """ 访问已经爬取的User.csv, Edge.csv，扩充边 """
    def getFollowing(user_id, follow_num):
        if follow_num>10000: #粉丝数太多，我们放弃爬取
            return []
        follow_num = min(1000,follow_num)
        page_num = int(follow_num/20) #确定爬取页数
        following = []
    
        for i in range(1,page_num+1):
            #微博用户关注列表JSON链接
            url = "https://m.weibo.cn/api/container/getSecond?containerid=100505{uid}_-_FOLLOWERS&page={page}".format(uid=user_id,page=i)
            try:
                req = requests.get(url)
                jsondata = req.text
                data = json.loads(jsondata)
                content = data["data"]['cards']
       
                #循环输出每一页的关注者各项信息
                for i in content:
                    followingId = i['user']['id']
                    following.append(followingId)
            except Exception as e:
                print(e)
                return following
        return following
        
    def getFans(user_id,fans_num):
        urlTemplate = "https://m.weibo.cn/api/container/getIndex?containerid=231051_-_fans_-_{uid}&since_id="
        if fans_num>10000:
            return []
        fans_num = min(fans_num,1000)
        page_num = int(fans_num/20)
        fans = []
    
        for offset in range(1,page_num+1):
            url = urlTemplate.format(uid = user_id) + str(offset)
            response = requests.get(url)
            result = json.loads(response.text)
            try:
                cardgroup = jsonpath.jsonpath(result,"$..card_group")[0]
            except Exception as e:
                print(e)
                return fans
                
                for fan in cardgroup:
                    try:
                        user_id = jsonpath.jsonpath(fan, "$..id")[0]
                        fans.append(user_id)
                    except Exception as e:
                        print(e)
        return fans


    ids = []
    users = []

    with open("User.csv",'r') as file:
        reader = csv.reader(file)
        users = list(reader)
    
    f2 = open('edges.csv','a+',encoding='utf-8-sig')
    edge_writer = csv.writer(f2)
    edge_writer.writerow(['source','target'])

    num = 1
    users = users[1:]
    
    for user in users:
        ids.append(user[0])

    for user in users:
        # 对每一位用户，爬取他的粉丝和关注的id集合，通过查看是否已经在我们的用户集合中的方式来增加边数
        sleep(random.randint(10,20)) #设置休眠时间
        id, follow_num, fans_num = user[0], int(user[3]), int(user[2])
        following = getFollowing(id,follow_num) #得到关注的id集合
       
        fans = getFans(id,fans_num) #得到粉丝的id集合
       
        for follow in following:
            if str(follow) in ids:
                f2 = open('edges.csv','a+',encoding='utf-8-sig')
                edge_writer = csv.writer(f2)
                edge_writer.writerow([id,follow])
                print('-'*20+str(id)+" FOLLOW "+str(follow)+'-'*20)
        for fan in fans:
            if str(fan) in ids:
                f2 = open('edges.csv','a+',encoding='utf-8-sig')
                edge_writer = csv.writer(f2)
                edge_writer.writerow([fan,id])
                print('-'*20+str(fan)+" FOLLOW "+str(id)+'-'*20)
        print('*'*20+"第"+str(num)+"用户处理完毕"+'*'*20)
        num+=1



if __name__ == "__main__":
    user_id = "USER_ID"
    get_fans_network(user_id)

    # 我们爬取的粉丝网络可能会比较稀疏
    # 比如根节点a的粉丝(b1,b2)，b1的粉丝(c1,c2),b2的粉丝(c3,c4,c5),但是我们不知道c1与c3是否有边
    # 可以通过下面的方式查询网络中的节点是否有边连接
    # 以此扩充数据集
    #generate_more_edges()