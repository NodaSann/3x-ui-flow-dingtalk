import os
import requests
import json
import pickle
import time
import sys
import traceback
import logging
import socket
import urllib3

# 禁用不安全请求的警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 增加请求超时设置
REQUEST_TIMEOUT = 30  # 从10秒增加到30秒
CONNECT_TIMEOUT = 15  # 连接超时设置为15秒
# 针对青龙面板环境，默认不验证SSL证书
VERIFY_SSL = False
# 添加重试次数
MAX_RETRIES = 3

# 配置请求Session对象
def create_request_session():
    session = requests.Session()
    # 设置默认超时
    session.request = lambda method, url, **kwargs: super(requests.Session, session).request(
        method=method, 
        url=url, 
        timeout=kwargs.pop('timeout', (CONNECT_TIMEOUT, REQUEST_TIMEOUT)),
        verify=kwargs.pop('verify', VERIFY_SSL),
        **kwargs
    )
    # 设置连接池参数
    adapter = requests.adapters.HTTPAdapter(
        pool_connections=10,
        pool_maxsize=10,
        max_retries=MAX_RETRIES
    )
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def load_config():
    try:
        logger.info("开始加载配置文件...")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, "config.json")
        logger.info(f"配置文件路径: {config_path}")
        
        if not os.path.exists(config_path):
            logger.error(f"配置文件不存在: {config_path}")
            raise FileNotFoundError("配置文件 config.json 不存在，请创建并填写必要的配置")
            
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        # 只检查必要的配置项
        required_keys = ["base_url", "username", "password", "dingtalk_webhook"]
        for key in required_keys:
            if not config.get(key):
                logger.error(f"配置文件缺少必要项: {key}")
                raise ValueError(f"配置文件缺少必要项: {key}")
                
        logger.info("配置文件加载成功")
        return config
    except Exception as e:
        logger.error(f"加载配置时发生错误: {str(e)}")
        logger.debug(traceback.format_exc())
        return None

def save_cookies(session, config_file="config.json"):
    try:
        logger.info("开始保存cookies...")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, config_file)
        
        # 读取当前配置
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 将cookies转换为字典
        cookies_dict = requests.utils.dict_from_cookiejar(session.cookies)
        
        # 更新配置中的cookies和时间戳
        config['cookies'] = cookies_dict
        config['cookie_timestamp'] = time.time()
        
        # 写回配置文件
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
            
        logger.info(f"Cookies已保存到 {config_path}")
        return True
    except Exception as e:
        logger.error(f"保存cookies时发生错误: {str(e)}")
        logger.debug(traceback.format_exc())
        return False

def load_cookies(config_file="config.json"):
    try:
        logger.info("开始加载cookies...")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, config_file)
        
        if not os.path.exists(config_path):
            logger.warning("找不到配置文件，需要重新登录")
            return None
            
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 检查是否存在cookies
        if not config.get('cookies'):
            logger.warning("配置文件中没有cookies信息，需要重新登录")
            return None
            
        # 创建会话并加载cookies
        session = create_request_session()
        cookies = requests.utils.cookiejar_from_dict(config['cookies'])
        session.cookies = cookies
        
        logger.info(f"已从配置文件加载cookies")
        return session
    except Exception as e:
        logger.error(f"加载cookies时发生错误: {str(e)}")
        logger.debug(traceback.format_exc())
        return None

def login_to_3xui():
    config = load_config()
    if not config:
        return None
    base_url = config.get("base_url")
    username = config.get("username")
    password = config.get("password")
    if not all([base_url, username, password]):
        logger.error("配置错误: 必须提供base_url, username和password")
        return None
    login_url = f"{base_url}/login"
    login_data = {
        "username": username,
        "password": password
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest"
    }
    session = create_request_session()
    try:
        logger.info("开始登录到3x-ui...")
        response = session.post(login_url, data=login_data, headers=headers)
        if response.status_code == 200:
            try:
                result = response.json()
                if result.get("success"):
                    logger.info("登录成功!")
                    save_cookies(session)
                    return session
                else:
                    logger.error(f"登录失败: {result.get('msg', '未知错误')}")
                    return None
            except json.JSONDecodeError:
                logger.error("无法解析服务器响应")
                return None
        else:
            logger.error(f"登录请求失败，状态码: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"登录过程中发生错误: {str(e)}")
        logger.debug(traceback.format_exc())
        return None

def get_inbound_list():
    config = load_config()
    if not config:
        return None
    base_url = config.get("base_url")
    if not base_url:
        logger.error("配置错误: 缺少base_url")
        return None
    url = f"{base_url}/panel/inbound/list"
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "origin": base_url,
        "referer": f"{base_url}/panel/inbounds",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest"
    }
    session = load_cookies()
    if session:
        try:
            logger.info("使用保存的cookies请求入站列表...")
            response = session.post(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if data.get("success") is True:
                    logger.info("使用保存的cookies请求成功!")
                    return data
                else:
                    logger.warning("保存的cookies已过期，尝试重新登录...")
            else:
                logger.error(f"使用保存的cookies请求失败，状态码: {response.status_code}")
        except Exception as e:
            logger.error(f"使用保存的cookies时发生错误: {str(e)}")
            logger.debug(traceback.format_exc())
    else:
        logger.warning("未找到有效的保存cookies，尝试重新登录...")
    session = login_to_3xui()
    if not session:
        logger.error("无法获取有效会话，请检查登录凭据")
        return None
    try:
        logger.info("重新登录后请求入站列表...")
        response = session.post(url, headers=headers)
        if response.status_code == 200:
            logger.info("重新登录后请求成功!")
            data = response.json()
            return data
        else:
            logger.error(f"请求失败，状态码: {response.status_code}")
            logger.debug(response.text)
            return None
    except Exception as e:
        logger.error(f"发生错误: {str(e)}")
        logger.debug(traceback.format_exc())
        return None

def format_bytes(size):
    size = float(size)
    units = ["B", "KB", "MB", "GB", "TB"]
    idx = 0
    while size >= 1024 and idx < len(units) - 1:
        size /= 1024.0
        idx += 1
    return f"{size:.2f} {units[idx]}"

def process_traffic_data(data):
    if not data or not data.get("success") or "obj" not in data:
        logger.error("获取流量数据失败或数据格式不正确")
        return "获取流量数据失败或数据格式不正确"
    inbounds = data["obj"]
    message = "### 📊 3x-ui 流量统计\n"
    for inbound in inbounds:
        remark = inbound.get("remark", "未命名用户")
        up = inbound.get("up", 0)
        down = inbound.get("down", 0)
        total = up + down
        message += f"\n**👤 {remark}**\n"
        message += f"> ⬆️ {format_bytes(up)} | ⬇️ {format_bytes(down)} | 📈 {format_bytes(total)}\n"
    logger.info("流量数据处理完成")
    return message

def send_dingtalk_message(message):
    config = load_config()
    if not config:
        logger.error("无法加载配置文件")
        return False
    webhook_url = config.get("dingtalk_webhook")
    if not webhook_url:
        logger.error("配置错误：缺少钉钉webhook地址")
        return False
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "msgtype": "markdown",
        "markdown": {
            "title": "流量统计",
            "text": message
        }
    }
    try:
        logger.info("开始发送钉钉消息...")
        session = create_request_session()
        response = session.post(webhook_url, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            result = response.json()
            if result.get("errcode") == 0:
                logger.info("钉钉消息发送成功")
                return True
            else:
                logger.error(f"钉钉消息发送失败：{result.get('errmsg')}")
                return False
        else:
            logger.error(f"请求失败，状态码：{response.status_code}")
            return False
    except Exception as e:
        logger.error(f"发送钉钉消息时发生错误：{str(e)}")
        logger.debug(traceback.format_exc())
        return False

def main():
    logger.info("开始执行 3x-ui 流量统计脚本...")
    data = get_inbound_list()
    if not data:
        logger.error("无法获取入站列表数据")
        return
    message = process_traffic_data(data)
    logger.info("生成的钉钉消息预览：")
    logger.info("="*50)
    logger.info(message)
    logger.info("="*50)
    send_result = send_dingtalk_message(message)
    if send_result:
        logger.info("流量统计已成功推送到钉钉")
    else:
        logger.error("推送到钉钉失败")

if __name__ == "__main__":
    main()