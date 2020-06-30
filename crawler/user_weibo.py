"""
爬取用户的个人详细信息与微博信息，写入csv文件
"""

import codecs
import copy
import csv
import json
import os
import random
import re
import shutil
import sys
import traceback
from collections import OrderedDict
from datetime import date, datetime, timedelta
from time import sleep

import requests
from absl import app, flags
from lxml import etree
from requests.adapters import HTTPAdapter
from tqdm import tqdm

cookie = "YOUR_COOKIE"


class Weibo(object):
    def __init__(self,user_id):
        """ weibo类初始化 """
        self.cookie = cookie
        self.user = {}
        self.got_num = 0
        self.weibo = []
        self.weibo_id_list = []
        self.user_id = user_id
    
    def is_date(self, since_date):
        """ 判断日期格式是否正确 """
        try:
            if ':' in since_date:
                datetime.strptime(since_date, '%Y-%m-%d %H:%M')
            else:
                datetime.strptime(since_date, '%Y-%m-%d')
            return True
        except ValueError:
            return False
    
    def str_to_time(self, text):
        """ 将字符串转换成时间类型 """
        if ':' in text:
            result = datetime.strptime(text, '%Y-%m-%d %H:%M')
        else:
            result = datetime.strptime(text, '%Y-%m-%d')
        return result

    def handle_html(self, url):
        """ 处理html """
        try:
            html = requests.get(url,headers = {"Cookie":self.cookie}).content
            selector = etree.HTML(html)
            return selector
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def handle_garbled(self, info):
        """ 处理乱码 """
        try:
            info = (info.xpath('string(.)').replace(u'\u200b', '').encode(
                sys.stdout.encoding, 'ignore').decode(sys.stdout.encoding))
            return info
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()
    
    def get_json(self,params):
        """ 获取网页中json数据 """
        url = "https://m.weibo.cn/api/container/getIndex?"
        r = requests.get(url,params=params,headers = {"Cookie":self.cookie})
        return r.json()
    
    def get_weibo_json(self,page):
        """ 获取网页中微博json数据 """
        params = {'containerid':'107603'+str(self.user_id),'page':page}
        js = self.get_json(params)
        return js
    
    def get_user_info(self):
        """ 获取用户信息 """
        params = {'containerid':'100505'+str(self.user_id)}
        js = self.get_json(params)
        if js['ok']:
            info = js['data']['userInfo']
            user_info = OrderedDict()
            user_info['id'] = self.user_id
            user_info['screen_name'] = info.get('screen_name', '')
            user_info['gender'] = info.get('gender', '')
            params = {
                'containerid':
                '230283' + str(self.user_id) + '_-_INFO'
            }
            zh_list = [
                u'生日', u'所在地', u'小学', u'初中', u'高中', u'大学', u'公司', u'注册时间',
                u'阳光信用'
            ]
            en_list = [
                'birthday', 'location', 'education', 'education', 'education',
                'education', 'company', 'registration_time', 'sunshine'
            ]
            for i in en_list:
                user_info[i] = ''
            js = self.get_json(params)
            if js['ok']:
                cards = js['data']['cards']
                if isinstance(cards, list) and len(cards) > 1:
                    card_list = cards[0]['card_group'] + cards[1]['card_group']
                    for card in card_list:
                        if card.get('item_name') in zh_list:
                            user_info[en_list[zh_list.index(
                                card.get('item_name'))]] = card.get(
                                    'item_content', '')
            user_info['statuses_count'] = info.get('statuses_count', 0)
            user_info['followers_count'] = info.get('followers_count', 0)
            user_info['follow_count'] = info.get('follow_count', 0)
            user_info['description'] = info.get('description', '')
            user_info['profile_url'] = info.get('profile_url', '')
            user_info['profile_image_url'] = info.get('profile_image_url', '')
            user_info['avatar_hd'] = info.get('avatar_hd', '')
            user_info['urank'] = info.get('urank', 0)
            user_info['mbrank'] = info.get('mbrank', 0)
            user_info['verified'] = info.get('verified', False)
            user_info['verified_type'] = info.get('verified_type', 0)
            user_info['verified_reason'] = info.get('verified_reason', '')
            user = self.standardize_info(user_info)
            self.user = user
            return user
    
    def user_detail2csv(self):
        """ 将爬取到的用户信息写入csv """
        f = open('user_detail.csv','a+',encoding='utf-8-sig')
        csv_writer = csv.writer(f)
        gender = u'女' if self.user['gender'] == 'f' else u'男'
        lis = [self.user["id"],self.user["screen_name"],gender, self.user["location"],self.user["education"],self.user["sunshine"],self.user["registration_time"],self.user["statuses_count"],self.user["followers_count"],self.user["follow_count"],self.user["description"]]
        csv_writer.writerow(lis)
    
    
    def standardize_info(self,weibo):
        """ 标准化信息，去除乱码  """
        for k,v in weibo.items():
            if 'bool' not in str(type(v)) and 'int' not in str(type(v)) and 'list' not in str(type(v)) and 'long' not in str(type(v)):
                weibo[k] = v.replace(u"\u200b", "").encode(sys.stdout.encoding, "ignore").decode(sys.stdout.encoding)
        return weibo
    


    def get_page_num(self, selector):
        """ 获取微博总页数 """
        try:
            if selector.xpath("//input[@name='mp']") == []:
                page_num = 1
            else:
                page_num = (int)(
                    selector.xpath("//input[@name='mp']")[0].attrib['value'])
            return page_num
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()
    
    def get_long_weibo(self, weibo_link):
        """ 获取长原创微博 """
        try:
            for i in range(5):
                selector = self.handle_html(weibo_link)
                if selector is not None:
                    info = selector.xpath("//div[@class='c']")[1]
                    wb_content = self.handle_garbled(info)
                    wb_time = info.xpath("//span[@class='ct']/text()")[0]
                    weibo_content = wb_content[wb_content.find(':') +
                                               1:wb_content.rfind(wb_time)]
                    if weibo_content is not None:
                        return weibo_content
                sleep(random.randint(6, 10))
        except Exception as e:
            return u'网络出错'
            print('Error: ', e)
            traceback.print_exc()


    def get_original_weibo(self, info, weibo_id):
        """获取原创微博"""
        try:
            weibo_content = self.handle_garbled(info)
            weibo_content = weibo_content[:weibo_content.rfind(u'赞')]
            a_text = info.xpath('div//a/text()')
            if u'全文' in a_text:
                weibo_link = 'https://weibo.cn/comment/' + weibo_id
                wb_content = self.get_long_weibo(weibo_link)
                if wb_content:
                    weibo_content = wb_content
            return weibo_content
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()


    def get_long_retweet(self, weibo_link):
        """获取长转发微博"""
        try:
            wb_content = self.get_long_weibo(weibo_link)
            weibo_content = wb_content[:wb_content.rfind(u'原文转发')]
            return weibo_content
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def get_retweet(self, info, weibo_id):
        """获取转发微博"""
        try:
            weibo_content = self.handle_garbled(info)
            weibo_content = weibo_content[weibo_content.find(':') +
                                          1:weibo_content.rfind(u'赞')]
            weibo_content = weibo_content[:weibo_content.rfind(u'赞')]
            a_text = info.xpath('div//a/text()')
            if u'全文' in a_text:
                weibo_link = 'https://weibo.cn/comment/' + weibo_id
                wb_content = self.get_long_retweet(weibo_link)
                if wb_content:
                    weibo_content = wb_content
            retweet_reason = self.handle_garbled(info.xpath('div')[-1])
            retweet_reason = retweet_reason[:retweet_reason.rindex(u'赞')]
            original_user = info.xpath("div/span[@class='cmt']/a/text()")
            weibo_content = retweet_reason 
            return weibo_content
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def is_original(self, info):
        """ 判断微博是否为原创微博 """
        is_original = info.xpath("div/span[@class='cmt']")
        if len(is_original) > 3:
            return False
        else:
            return True

    def get_weibo_content(self, info, is_original):
        """获取微博内容"""
        try:
            weibo_id = info.xpath('@id')[0][2:]
            if is_original:
                weibo_content = self.get_original_weibo(info, weibo_id)
            else:
                weibo_content = self.get_retweet(info, weibo_id)
            return weibo_content
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()
    
    def get_publish_time(self, info):
        """获取微博发布时间"""
        try:
            str_time = info.xpath("div/span[@class='ct']")
            str_time = self.handle_garbled(str_time[0])
            publish_time = str_time.split(u'来自')[0]
            if u'刚刚' in publish_time:
                publish_time = datetime.now().strftime('%Y-%m-%d %H:%M')
            elif u'分钟' in publish_time:
                minute = publish_time[:publish_time.find(u'分钟')]
                minute = timedelta(minutes=int(minute))
                publish_time = (datetime.now() -
                                minute).strftime('%Y-%m-%d %H:%M')
            elif u'今天' in publish_time:
                today = datetime.now().strftime('%Y-%m-%d')
                time = publish_time[3:]
                publish_time = today + ' ' + time
                if len(publish_time) > 16:
                    publish_time = publish_time[:16]
            elif u'月' in publish_time:
                year = datetime.now().strftime('%Y')
                month = publish_time[0:2]
                day = publish_time[3:5]
                time = publish_time[7:12]
                publish_time = year + '-' + month + '-' + day + ' ' + time
            else:
                publish_time = publish_time[:16]
            return publish_time
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()
    

    def get_weibo_footer(self, info):
        """获取微博点赞数、转发数、评论数"""
        try:
            footer = {}
            pattern = r'\d+'
            str_footer = info.xpath('div')[-1]
            str_footer = self.handle_garbled(str_footer)
            str_footer = str_footer[str_footer.rfind(u'赞'):]
            weibo_footer = re.findall(pattern, str_footer, re.M)

            up_num = int(weibo_footer[0])
            footer['up_num'] = up_num

            retweet_num = int(weibo_footer[1])
            footer['retweet_num'] = retweet_num

            comment_num = int(weibo_footer[2])
            footer['comment_num'] = comment_num
            return footer
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()
    
    def get_one_weibo(self, info):
        """获取一条微博的全部信息"""
        try:
            weibo = OrderedDict()
            is_original = self.is_original(info)
           
            weibo['id'] = info.xpath('@id')[0][2:]
            weibo['content'] = self.get_weibo_content(info,  is_original)  # 微博内容
             
            weibo['publish_time'] = self.get_publish_time(info)  # 微博发布时间
            footer = self.get_weibo_footer(info)
            weibo['up_num'] = footer['up_num']  # 微博点赞数
            weibo['retweet_num'] = footer['retweet_num']  # 转发数
            weibo['comment_num'] = footer['comment_num']  # 评论数
            
            weibo['length'] = len(weibo['content']) # 长度
            
            urlRegex = re.compile(r"https?://")
            weibo['contain_url'] = False
            if re.findall(urlRegex,weibo['content']):
                weibo['contain_url'] = True
            
            return weibo
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()
    

    def print_one_weibo(self, weibo):
        """打印一条微博"""
        print(weibo['content'])
        print(u'发布时间：%s' % weibo['publish_time'])
        print(u'点赞数：%d' % weibo['up_num'])
        print(u'转发数：%d' % weibo['retweet_num'])
        print(u'评论数：%d' % weibo['comment_num'])
        
        contain_url = u'是' if weibo['contain_url']==True else u'否'
        print(u'是否包含url: %s' % contain_url)

        original = u'否' if weibo['content'].startswith(u'转发理由') else u'是'
        print(u'是否原创: %s'%original)
        
        print(u'长度: %d'%weibo['length'])

        print(u'url：https://weibo.cn/comment/%s' % weibo['id'])
    

    def get_one_page(self, page):
        """获取第page页的全部微博"""
        try:
            url = 'https://weibo.cn/%s?page=%d' % (self.user_id, page)
            selector = self.handle_html(url)
            info = selector.xpath("//div[@class='c']")
            is_exist = info[0].xpath("div/span[@class='ctt']")
            if is_exist:
                for i in range(0, len(info) - 2):
                    weibo = self.get_one_weibo(info[i])
                    if weibo:
                        if weibo['id'] in self.weibo_id_list:
                            continue
                        publish_time = self.str_to_time(weibo['publish_time'])
                       
                        print(u'{}已获取{}的第{}页微博{}'.format( '-' * 30, self.user_id, page, '-' * 30))
                        #self.print_one_weibo(weibo)
                        self.weibo.append(weibo) 

                        # TODO: write2csv()
                        self.write2csv4weibo(weibo)
                        self.weibo_id_list.append(weibo['id'])
                        self.got_num += 1
                        print('-' * 100)
           
            return True
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()
    

    def get_weibo_info(self):
        """ 获取微博信息 """
        try:
            url = 'https://weibo.cn/%s' % (self.user_id)
            selector = self.handle_html(url)
           
            page_num = self.get_page_num(selector)  # 获取微博总页数
            wrote_num = 0
            page1 = 0

            random_pages = random.randint(1, 5)
            page_num = min(page_num,100)
            self.start_time = datetime.now().strftime('%Y-%m-%d %H:%M')
            for page in range(1,page_num+1):
                if page%3==0:
                    sleep(random.randint(6,10))
                is_end = self.get_one_page(page)  # 获取第page页的全部微博
            
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()
    

    def write2csv4weibo(self,weibo):
        # 用户id,id,内容,发布时间,是否含url,评论数,转发数,点赞数,长度,是否原创
        f = open('Weibo.csv','a+',encoding='utf-8-sig')
        csv_writer = csv.writer(f)
        contain_url = 1 if weibo['contain_url']==True else 0
        original = 0 if weibo['content'].startswith(u'转发理由') else 1
        lis = [weibo['id'],self.user_id,weibo['content'],weibo['publish_time'],contain_url,weibo['comment_num'],weibo['retweet_num'],weibo['up_num'],weibo['length'],original]
        csv_writer.writerow(lis)  
        f.close()


    def start(self):
        """ 运行爬虫 """
        try:
            print('*' * 30+user_id+'*'*30)
            self.get_user_info()
            self.user_detail2csv()
            self.get_weibo_info()
            
            print(u'信息抓取完毕')
            print('*' * 100)
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()


if __name__ == "__main__":
    try:
        user_id = "USER_ID_YOU_WANT_TO_CRAWL"
        wb = Weibo(user_id)
        wb.start()
    except Exception as e:
        print('Error: ',e)
        traceback.print_exc()