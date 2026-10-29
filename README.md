

# 项目介绍
本项目使用python+flask+websocket+小程序+taro，打造最小小程序后端。主要服务于小区内。

### 迭代进度
- 新增状态删除
- 新增聊天室
- 新增文章功能



### 

## Configuration and credential safety

Provide `REDIS_PASSWORD`, `MINIAPP_APP_ID`, and `MINIAPP_SECRET` in the
application process environment. Missing or blank required values stop startup.
`REDIS_HOST` defaults to `127.0.0.1`; `REDIS_PORT` defaults to `6379`.
`.env.example` lists names only: copying it does not load environment variables.
Use your deployment's secret store or protected process configuration; never
commit real values, private keys, or local `.env` files. Keep TLS private keys
outside this repository and configure TLS at your reverse proxy.

Previously committed credentials and private keys must be treated as exposed.
Repository cleanup does not rotate credentials or invalidate old copies. Replace
credentials through their provider before deploying; provision a new TLS key and
certificate as appropriate. This code change does not change any live service.

Run offline configuration regression checks with:
`python -m unittest discover -s tests -p 'test_*.py'`.
