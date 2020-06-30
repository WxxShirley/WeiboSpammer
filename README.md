# WeiboSpammer
Course project of Social Network Mining(DATA130007.01), Supervised by [Deqing Yang](http://www.cs.fudan.edu.cn/?page_id=2393)

Copyright (c) 2020 by [Xiaoxin He](https://github.com/Cautiousss),Xixi Wu @Fudan Univerisity

###

## 😄使用我们的微博个性化报告
[前端效果](https://github.com/Cautiousss/Weibo)

在`./app/main.py`中，输入任意用户的id，即可生成该用户新浪微博个性化报告。
运行截图：
<img src="https://github.com/WxxShirley/WeiboSpammer/blob/master/imgs/app_log.png" width = "600" height = "600" alt="图片说明" align=center />

该个性化报告包括(这里我们以明星秦昊为例)：
* 微博内容词云
   ![wc](https://github.com/WxxShirley/WeiboSpammer/blob/master/app/derived/kw_1740197697.png)
* 好友在中国地图分布
   ![regoin](https://github.com/WxxShirley/WeiboSpammer/blob/master/app/derived/region_1740197697.png)
* 异常粉丝(调用我们预训练的虚假用户分类模型)
* 沉寂关注(最近半年没发微博)
* 发微博时间统计图
  <img src="https://github.com/WxxShirley/WeiboSpammer/blob/master/app/derived/date_1740197697.png" width = "400" height = "300" alt="图片说明" align=center />
   

## 工作介绍
* 新浪微博虚假用户检测
  * 爬取2k用户的详细个人信息与全部微博内容，人工标注类别，构建数据集
    > 数据集在 `./data`目录下，其中正负样本比例为83:17
  * 特征抽取
     * 社会特征：关注数 (F1)、粉丝数 (F2)、关注粉丝比 (F3)
     * 用户行为特征：月均微博 (F4)、时间间隔 (F5)、转发比 (F6)
     * 内容特征：URL 链接比 (F7)、微博评论比 (F8)、原创微博评论比 (F9)、微博平均长度 (F10)、博文余弦相似度(F11、F12)
  * 训练机器学习分类器，包括SVM、KNN、RF等。
     * 各个模型在测试集上的F1、AUC、Recall、Precision上基本都能达到90%以上，性能好
     * 随机森林模型效果最好，AUC、F1非常接近1

* 正常用户社交网络(NormNet)与虚假用户社交网络(SpamNet)可视化与分析
  * 构建方式：在上述数据集中随机选择1个正常用户与1个虚假用户，爬取三阶粉丝网络
  * 规模：
     - NormNet:节点909，边2659
     - SpamNet:节点891，边1423
  * 可视化部分:关注-被关注关系,微博转发关系,地域间关注关系
  * 网络属性分析:度分布、连通性、同质性

* 应用
   * 功能：输入任意一位新浪微博用户的id，生成他/她的个性化报告。
   * 包括：**微博内容词云图**、**好友分布的中国地图**、**沉寂关注**（关注的人中近半年没有发微博的）、**异常粉丝**（应用我们训练好的分类模型，检测粉丝中的虚假用户）


## 代码与文件介绍
#### 爬虫 `./crawler`
* `user_weibo.py`：指定用户id，爬取该用户详细个人信息与全部微博内容，写入csv文件中
    * 用户信息包括：id、昵称、地区、性别、信用、注册时间、微博数、关注数、粉丝数、个人简介
    * 微博内容包括：微博id、内容、发布时间（**精确到分**）、是否转发、长度、是否含url、点赞数、转发数、关注数
* `bfs_network.py`：指定用户id，爬取其三阶粉丝网络、写入csv文件中
> 注意：需要设定自己的cookie以及调整休眠时间（新浪微博api有限流）

#### 虚假用户检测二分类数据集 `./data`
* `UserDetail.csv` 用户信息 
  > 这些用户是从蔡徐坤微博评论中随机选择，因此虚假账号较多，而且非常典型
* `weibo.csv` 上述用户的微博信息

#### 两类网络分析 `./network_analysis`
* NormNet - 正常用户网络
  * `User.csv`,`Edge.csv`: 可直接导入Gephi，进行网络可视化和网络属性计算
  * `weibo.csv`: 该网络的用户微博（只爬取了最近的二十条）
  * `homogenetiy.py`: 网络同质性分析，包括：
     * 用户微博内容与好友微博内容相似度，计算方式在`textSimi.py`-余弦相似度计算
     * 任意一个用户与好友在中国地图上的分布图
     * 用户间微博转发关系，并可视化
* SpamNet - 虚假用户网络
   方法类似，因此只上传了数据
   
   

