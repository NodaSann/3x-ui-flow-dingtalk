# 📊 x-ui 流量统计小工具

嘿，这是一个简单好用的小工具，用来监控你的x-ui面板流量使用情况，通过钉钉机器人发送通知，省心又方便。定期获取流量数据后推送到钉钉群里，这样你就能随时了解服务器的流量情况啦~

## 🌟 功能特点

- 🔄 自动登录x-ui管理面板
- 📈 获取所有入站流量数据
- ✨ 美化数据显示，清晰直观
- 🔔 钉钉机器人推送，及时提醒
- 🍪 保存cookies，减少登录次数

## 🔧 环境要求

- 🐍 Python 3.6+
- 🖥️ 已部署的x-ui面板
- 🤖 配置好的钉钉机器人

## 🚀 部署方式

咱们支持两种部署方式，看你喜欢哪种~

### 一、🐉 青龙面板部署

[青龙面板](https://github.com/whyour/qinglong)是个不错的定时任务管理平台，支持多种编程语言，特别适合跑这种定时脚本。

#### 1. 准备工作

- 装好青龙面板
- 确保青龙能访问到你的x-ui面板

#### 2. 部署步骤

1. **添加依赖**

   青龙面板里，找到"依赖管理" → "Python" → 添加：
   ```
   requests
   ```

2. **添加脚本**

   青龙面板里，找到"脚本管理" → "新建文件"：
   - 创建 `x-ui_flow.py` 文件，把本仓库 `main/x-ui_flow.py` 的内容复制进去
   - 创建 `config.json` 文件，参照 `main/config.template.json` 填写你自己的配置

3. **创建定时任务**

   青龙面板里，找到"定时任务" → "添加任务"：
   - 名称：x-ui流量统计
   - 命令：python3 x-ui_flow.py
   - 定时规则：比如 `0 8 * * *`（每天早8点跑一次）

4. **查看日志**

   任务跑完后，点"日志"看看执行得咋样

### 二、💻 本地部署

如果你想自己电脑或服务器上部署，可以这样搞：

#### 1. 下载代码

```bash
git clone https://github.com/yourusername/x-ui.git
cd x-ui
```

#### 2. 安装依赖

```bash
pip install -r requirements.txt
```

#### 3. 配置

复制模板改成你自己的配置：

```bash
cp main/config.template.json main/config.json
```

编辑 `main/config.json` 文件：

```json
{
    "base_url": "https://your-xui-panel.com:54321",  // 你的x-ui面板地址
    "username": "your_username",  // 登录用户名
    "password": "your_password",  // 登录密码
    "dingtalk_webhook": "https://oapi.dingtalk.com/robot/send?access_token=your_access_token"  // 钉钉机器人webhook
}
```

#### 4. 运行

手动运行一下试试：

```bash
python main/x-ui_flow.py
```

#### 5. 设置定时任务

##### Linux/macOS

编辑crontab：

```bash
crontab -e
```

添加定时任务：

```
0 8 * * * cd /path/to/x-ui && python3 main/x-ui_flow.py >> /path/to/log/x-ui.log 2>&1
```

##### Windows

1. 打开任务计划程序
2. 创建个基本任务
3. 设置时间（比如每天8点）
4. 设置操作：
   - 程序：`python`
   - 参数：`main/x-ui_flow.py`
   - 起始位置：`D:\path\to\x-ui`（改成你实际的路径）

## ⚙️ 配置文件说明

`config.json` 文件的配置项：

| 参数 | 说明 |
|------|------|
| base_url | x-ui面板的网址，带端口 |
| username | 登录用户名 |
| password | 登录密码 |
| dingtalk_webhook | 钉钉机器人webhook |
| cookies | 自动保存的登录信息，不用管它 |
| cookie_timestamp | 保存cookies的时间，不用管它 |

## 🤖 钉钉机器人配置小指南

1. 钉钉APP里创建个群
2. 群设置 → "智能群助手" → "添加机器人" → "自定义"
3. 起个名字，选个头像
4. 安全设置选"自定义关键词"，填个关键词（比如"流量"）
5. 创建好后，把webhook地址复制到配置文件

## ❓ 常见问题

**问：连不上x-ui面板怎么办？**  
答：检查一下网址对不对，还有看看你的网络能不能访问那个地址。

**问：钉钉消息发不出去？**  
答：确认webhook地址正确，还有检查消息内容有没有包含你设置的关键词。

## 📝 小贴士

- 🔒 配置文件要保管好，别泄露了
- 🔐 尽量用HTTPS访问x-ui面板，更安全
- 👀 时不时看看脚本运行情况，确保一切正常

## 📜 许可证

MIT License
