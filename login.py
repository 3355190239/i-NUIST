"""
==============================================================================
GitHub: https://github.com/3355190239/i-NUIST
Author: 3355190239
Description: 南京信息工程大学校园网自动登录脚本
==============================================================================
"""
import requests
import json
import hashlib
import sys
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

# ==============================================================================
# --- 1. 配置 ---
# ==============================================================================

# 基础常量
base_url = 'http://10.255.255.16'


# --- 用户信息配置 ---
# 您只需要修改这部分
username = "202412xxxxx"
password = "xxxxx"

# 默认网络供应商配置
# "1": 校园网, "2": 中国移动, "3": 中国电信, "4": 中国联通
channel = "1"

# 是否自动登录 ('1' 或 '0')
ifautologin = '1'


# 网络供应商ID映射
network_channel_map = {
    "1": "校园网",
    "2": "中国移动",
    "3": "中国电信",
    "4": "中国联通",
}

# ==============================================================================
# --- 2. 核心逻辑 ---
# ==============================================================================

class NuistLogin:
    """南京信息工程大学校园网登录类，封装所有加密和请求逻辑。"""

    # 登录错误码映射表
    ERROR_MAP = {
        'Passwd_Err': '密码错误',
        'UserName_Err': '用户名错误',
        'User_locked': '账号被锁定',
        'status_Err': '账号欠费或状态异常',
        'BindAttr_Err': '账号绑定属性错误',
        'Limit Users Err': '超出最大并发限制',
        '账户信息不完整': '请刷新页面或重新连接网络再试',
        '用户登录认证信息不完整': '请刷新页面或重新连接网络再试',
        '获取会话信息失败': '请连接i-NUIST网络后重试',
        'Status_Err': '状态错误，请确认运营商宽带账号是否欠费'
    }

    def __init__(self, username, password, channel, ifautologin):
        self.url = base_url # 引用更新
        self.username = username
        self.password = password
        self.channel = channel
        self.ifautologin = ifautologin
        self.ip = None
        self.session = requests.Session()
        self.DEFAULT_KEY_PREFIX = "axaQiQpsdFAacccs"

        # 预设请求头
        self.session.headers = {
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "Content-Type": "application/json;charset=gbk",
            "Origin": self.url,
            "Referer": f"{self.url}/",
        }

        # 预先计算加密盐
        self.salt_from_username = self._get_salt_from_username(self.username)

    def get_ip(self):
        """自动获取并设置当前设备的IP地址。"""
        url_ip = f"{self.url}/api/v1/ip"
        try:
            # 使用 session 发送请求，保持一致性
            response_ip = self.session.get(url_ip, timeout=5)
            response_ip.raise_for_status()
            ip_address = response_ip.json().get("data")
            if ip_address:
                print(f"✅ 自动获取IP成功: {ip_address}")
                self.ip = ip_address
                return True
            else:
                print(f"❌ 获取IP失败：服务器未返回IP地址。", file=sys.stderr)
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ 自动获取IP失败: {e}", file=sys.stderr)
            return False
        except json.JSONDecodeError:
            print(f"❌ 解析IP响应失败: {response_ip.text}", file=sys.stderr)
            return False

    def _get_salt_from_username(self, username: str) -> str:
        """模拟JS的加密盐生成逻辑 (SHA256截取)。"""
        combined_string = self.DEFAULT_KEY_PREFIX + username
        sha256_hash = hashlib.sha256(combined_string.encode('utf-8')).hexdigest()
        return sha256_hash[:16]

    def _encrypt_aes_ecb(self, data: str, key: str) -> str:
        """模拟JS的AES加密逻辑 (ECB模式)。"""
        try:
            cipher = AES.new(key.encode('utf-8'), AES.MODE_ECB)
            # 确保数据是字节串
            padded_data = pad(data.encode('utf-8'), AES.block_size)
            encrypted_data = cipher.encrypt(padded_data)
            return encrypted_data.hex()
        except ValueError as e:
            # 密钥长度不符合要求 (必须是 16, 24, 或 32 字节)
            print(f"❌ AES加密错误：密钥长度不合法。请检查 key: '{key}'", file=sys.stderr)
            raise e

    def login(self):
        """执行单步加密登录。"""
        if not self.ip:
            print("❌ IP地址未设置，无法登录。请先调用 get_ip()。", file=sys.stderr)
            return None

        # 加密所有字段
        try:
            encrypted_data = {
                "username": self._encrypt_aes_ecb(self.username, self.DEFAULT_KEY_PREFIX),
                "password": self._encrypt_aes_ecb(self.password, self.salt_from_username),
                "ifautologin": self._encrypt_aes_ecb(self.ifautologin, self.salt_from_username),
                "channel": self._encrypt_aes_ecb(self.channel, self.salt_from_username),
                "pagesign": self._encrypt_aes_ecb("secondauth", self.salt_from_username),
                "usripadd": self._encrypt_aes_ecb(self.ip, self.salt_from_username)
            }
        except Exception as e:
            print(f"❌ 数据加密失败: {e}", file=sys.stderr)
            return None

        # 将加密数据序列化为 gbk 编码的 JSON 字符串
        data_binary = json.dumps(encrypted_data, separators=(',', ':')).encode('gbk')
        url_login = f"{self.url}/api/v1/login"

        # 发送请求
        try:
            response = self.session.post(url=url_login, data=data_binary, timeout=10)
            response.raise_for_status()
            response_json = response.json()

            if not response_json:
                print("\n登录流程中断，未收到服务器有效响应。")
                return None

            # 检查登录成功状态
            if response_json.get("code") == 200 and response_json.get("data", {}).get("username"):
                print("\n--- ✅ 登录成功! ---")
                data = response_json['data']
                print(f"用户名: {data.get('username')}\n"
                      f"运营商: {data.get('outport')} ({network_channel_map.get(self.channel, '未知')})\n" # 引用更新
                      f"登录IP: {data.get('usripadd')}")
            else:
                print('\n--- ❌ 登录失败! ---')
                error_data = response_json.get('data', {})
                error_msg = error_data.get('text', '未知错误')

                print('错误原因: ' + self.ERROR_MAP.get(error_msg, f'服务器返回: {error_msg}'))

            return response_json

        except requests.exceptions.RequestException as e:
            print(f"❌ 网络请求失败: {e}", file=sys.stderr)
        except json.JSONDecodeError:
            print(f"❌ 解析服务器响应失败，内容: {response.text}", file=sys.stderr)

        return None


def main():
    """主执行函数"""
    try:
        print("\n===== I-NUIST校园网登录 =====")

        # 1. 实例化登录对象
        nuist = NuistLogin(
            username=username,
            password=password,
            channel=channel,
            ifautologin=ifautologin
        )

        # 2. 自动获取IP地址
        if not nuist.get_ip():
            print("登录流程中断。")
            return

        # 3. 执行登录
        nuist.login()

    except Exception as e:
        print(f"\n发生未知错误: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
