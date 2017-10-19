# momo
微信记账助手


# 测试使用请关注微信公号(April_Louisa)测试

![](http://media.gusibi.mobi/Hy8XHexmzppNKuekLuGxWy8LjdGrQAzZA3mH_e9xltoiYgTFWdvlpZwGWxZESrbK)

## 实现功能

* 微信聊天机器人
* 支持训练
* 特定用户发送图片返回七牛地址
* 支持记账
* 支持用户名查询

## TODO

* 对记账结果统计

## 安装& 使用

### 获取代码


```
git clone git@github.com:gusibi/momo.git
git co -b chatterbot
git pull origin chatterbot

```

### 安装依赖

```
pip install -r requirements.txt -i http://pypi.douban.com/simple --trusted-host pypi.douban.com
```

### 运行

```
python manage.py
```

## spuervisord 启动命令

```
supervisord -c supervisor.conf                             通过配置文件启动supervisor
supervisorctl -c supervisor.conf status                    察看supervisor的状态
supervisorctl -c supervisor.conf reload                    重新载入 配置文件
supervisorctl -c supervisor.conf start [all]|[appname]     启动指定/所有 supervisor管理的程序进程
supervisorctl -c supervisor.conf stop [all]|[appname]      关闭指定/所有 supervisor管理的程序进程
```
