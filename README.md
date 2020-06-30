# WeiboSpammer
Course project of Social Network Mining(DATA130007.01), Supervised by [Deqing Yang](http://www.cs.fudan.edu.cn/?page_id=2393)

Copyright (c) 2020 by [Xiaoxin He](https://github.com/Cautiousss),Xixi Wu @Fudan Univerisity


## 前端展示
[前端效果](https://github.com/Cautiousss/Weibo)

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
  * 可视化部分
     - 关注-被关注关系可视化
     - 微博转发关系可视化
     - 地域间关注关系
  * 网络属性分析
     - 度分布。NormNet重尾效应显著、能拟合出幂律分布
     - 连通性。NormNet强连通分量数目少，平均路径长度5.22，非常接近**六度空间理论**
     - 同质性。典型用户与好友微博内容比较。活跃时间比较

* 应用
   功能：输入任意一位新浪微博用户的id，生成他/她的个性化报告。
   包括：微博内容词云图、好友分布的中国地图、沉寂关注（关注的人中近半年没有发微博的）、异常粉丝（应用我们训练好的分类模型，检测粉丝中的虚假用户）


## 代码与文件介绍




