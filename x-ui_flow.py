import os
import requests
import json
import pickle
import time
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

def load_config():
    try:
        # 从环境变量中读取配置
        config = {
            "base_url": os.getenv("XUI_BASE_URL"),
            "username": os.getenv("XUI_USERNAME"),
            "password": os.getenv("XUI_PASSWORD"),
            "dingtalk_webhook": os.getenv("DINGTALK_WEBHOOK")
        }
        if not all(config.values()):
            raise ValueError("环境变量配置不完整，请检查 XUI_BASE_URL, XUI_USERNAME, XUI_PASSWORD, DINGTALK_WEBHOOK")
        return config
    except Exception as e:
        print(f"加载配置时发生错误: {str(e)}")
        return None

def save_cookies(session, cookie_file="cookies.pkl"):
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        cookie_path = os.path.join(script_dir, cookie_file)
        with open(cookie_path, 'wb') as f:
            pickle.dump({
                'cookies': session.cookies,
                'timestamp': time.time(),
            }, f)
        print(f"Cookies已保存到 {cookie_path}")
        return True
    except Exception as e:
        print(f"保存cookies时发生错误: {str(e)}")
        return False

def load_cookies(cookie_file="cookies.pkl"):
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        cookie_path = os.path.join(script_dir, cookie_file)
        if not os.path.exists(cookie_path):
            print("找不到cookies文件，需要重新登录")
            return None
        with open(cookie_path, 'rb') as f:
            cookie_data = pickle.load(f)
        session = requests.Session()
        session.cookies = cookie_data['cookies']
        print(f"已从 {cookie_path} 加载cookies")
        return session
    except Exception as e:
        print(f"加载cookies时发生错误: {str(e)}")
        return None

def login_to_3xui():
    config = load_config()
    if not config:
        return None
    base_url = config.get("base_url")
    username = config.get("username")
    password = config.get("password")
    if not all([base_url, username, password]):
        print("配置错误: 必须提供base_url, username和password")
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
    session = requests.Session()
    try:
        response = session.post(login_url, data=login_data, headers=headers)
        if response.status_code == 200:
            try:
                result = response.json()
                if result.get("success"):
                    print("登录成功!")
                    save_cookies(session)
                    return session
                else:
                    print(f"登录失败: {result.get('msg', '未知错误')}")
                    return None
            except json.JSONDecodeError:
                print("无法解析服务器响应")
                return None
        else:
            print(f"登录请求失败，状态码: {response.status_code}")
            return None
    except Exception as e:
        print(f"登录过程中发生错误: {str(e)}")
        return None

def get_inbound_list():
    config = load_config()
    if not config:
        return None
    base_url = config.get("base_url")
    if not base_url:
        print("配置错误: 缺少base_url")
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
            response = session.post(url, headers=headers, verify=True)
            if response.status_code == 200:
                data = response.json()
                if data.get("success") is True:
                    print("使用保存的cookies请求成功!")
                    return data
                else:
                    print("保存的cookies已过期，尝试重新登录...")
            else:
                print(f"使用保存的cookies请求失败，状态码: {response.status_code}")
        except Exception as e:
            print(f"使用保存的cookies时发生错误: {str(e)}")
    else:
        print("未找到有效的保存cookies，尝试重新登录...")
    session = login_to_3xui()
    if not session:
        print("无法获取有效会话，请检查登录凭据")
        return None
    try:
        response = session.post(url, headers=headers, verify=True)
        if response.status_code == 200:
            print("重新登录后请求成功!")
            data = response.json()
            return data
        else:
            print(f"请求失败，状态码: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"发生错误: {str(e)}")
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
    return message

def send_dingtalk_message(message):
    config = load_config()
    if not config:
        print("无法加载配置文件")
        return False
    webhook_url = config.get("dingtalk_webhook")
    if not webhook_url:
        print("配置错误：缺少钉钉webhook地址")
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
        response = requests.post(webhook_url, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            result = response.json()
            if result.get("errcode") == 0:
                print("钉钉消息发送成功")
                return True
            else:
                print(f"钉钉消息发送失败：{result.get('errmsg')}")
                return False
        else:
            print(f"请求失败，状态码：{response.status_code}")
            return False
    except Exception as e:
        print(f"发送钉钉消息时发生错误：{str(e)}")
        return False

def main():
    data = get_inbound_list()
    if not data:
        print("无法获取入站列表数据")
        return
    message = process_traffic_data(data)
    print("\n生成的钉钉消息预览：")
    print("="*50)
    print(message)
    print("="*50)
    send_result = send_dingtalk_message(message)
    if send_result:
        print("流量统计已成功推送到钉钉")
    else:
        print("推送到钉钉失败")

if __name__ == "__main__":
    print("开始执行 3x-ui 流量统计脚本...")
    main()