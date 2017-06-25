# momo
微信记账助手

# 测试使用请关注微信公号(April_Louisa)测试

![](http://media.gusibi.mobi/Hy8XHexmzppNKuekLuGxWy8LjdGrQAzZA3mH_e9xltoiYgTFWdvlpZwGWxZESrbK)

## 实现功能

* 微信聊天机器人
* 支持训练
* 特定用户发送图片返回七牛地址

## TODO

* 支持记账
* 对记账结果统计
* 详细配置过程


# 启动命令

```
supervisord -c supervisor.conf                             通过配置文件启动supervisor
supervisorctl -c supervisor.conf status                    察看supervisor的状态
supervisorctl -c supervisor.conf reload                    重新载入 配置文件
supervisorctl -c supervisor.conf start [all]|[appname]     启动指定/所有 supervisor管理的程序进程
supervisorctl -c supervisor.conf stop [all]|[appname]      关闭指定/所有 supervisor管理的程序进程
```
