import requests
import json
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import sys

# ==============================================================================
# --- 1. 用户信息配置 ---
# 您只需要修改这部分
# ==============================================================================
username = "202412XXXXX"
password = "XXXXXXX"

# --- 默认网络供应商配置 ---
# "1": 校园网, "2": 中国移动, "3": 中国电信, "4": 中国联通
DEFAULT_NETWORK_ID = "1"

# ==============================================================================
# --- 2. 核心逻辑 (通常无需修改) ---
# ==============================================================================
DEFAULT_KEY_PREFIX = "axaQiQpsdFAacccs"
BASE_URL = 'http://10.255.255.16'
# BASE_URL = 'http://a.nuist.edu.cn'


class NuistLogin:
    """南京信息工程大学校园网登录类，封装所有加密和请求逻辑。"""

    def __init__(self, username, password):
        """
        初始化登录实例。
        :param username: 学号/用户名
        :param password: 密码
        """
        self.username = username
        self.password = password
        self.ip = None
        self.session = requests.Session()
        self.session.headers = {
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "Content-Type": "application/json;charset=gbk",
            "Origin": BASE_URL,
            "Referer": f"{BASE_URL}/",
        }
        # 预先计算加密盐
        self.salt_from_username = self._get_salt_from_username(self.username)

    def get_ip(self):
        """自动获取并设置当前设备的IP地址。"""
        url_ip = f"{BASE_URL}/api/v1/ip"
        try:
            response_ip = requests.get(url_ip, timeout=5)
            response_ip.raise_for_status()
            ip_address = response_ip.json().get("data")
            if ip_address:
                print(f"✅ 自动获取IP成功: {ip_address}")
                self.ip = ip_address
                return True
            else:
                print(f"❌ 获取IP失败：服务器未返回IP地址。", file=sys.stderr)
                return False
        except Exception as e:
            print(f"❌ 自动获取IP失败: {e}", file=sys.stderr)
            return False

    def _get_salt_from_username(self, username: str) -> str:
        """模拟JS的加密盐生成逻辑。"""
        combined_string = DEFAULT_KEY_PREFIX + username
        sha256_hash = hashlib.sha256(combined_string.encode('utf-8')).hexdigest()
        return sha256_hash[:16]

    def _encrypt_aes_ecb(self, data: str, key: str) -> str:
        """模拟JS的AES加密逻辑。"""
        cipher = AES.new(key.encode('utf-8'), AES.MODE_ECB)
        padded_data = pad(data.encode('utf-8'), AES.block_size)
        encrypted_data = cipher.encrypt(padded_data)
        return encrypted_data.hex()

    def login(self, channel_id: str, ifautologin: str = "1") -> dict:
        """
        执行单步加密登录。
        :param channel_id: 网络供应商ID (e.g., "1")
        :param ifautologin: 是否自动登录 ("1" or "0")
        :return: 服务器响应的JSON字典
        """
        if not self.ip:
            print("IP地址未设置，无法登录。请先调用 get_ip()。", file=sys.stderr)
            return None

        # 加密所有字段
        encrypted_data = {
            "username": self._encrypt_aes_ecb(self.username, DEFAULT_KEY_PREFIX),
            "password": self._encrypt_aes_ecb(self.password, self.salt_from_username),
            "ifautologin": self._encrypt_aes_ecb(ifautologin, self.salt_from_username),
            "channel": self._encrypt_aes_ecb(channel_id, self.salt_from_username),
            "pagesign": self._encrypt_aes_ecb("secondauth", self.salt_from_username),
            "usripadd": self._encrypt_aes_ecb(self.ip, self.salt_from_username)
        }
        # print(encrypted_data)

        data_binary = json.dumps(encrypted_data, separators=(',', ':')).encode('gbk')
        url_login = f"{BASE_URL}/api/v1/login"

        # 发送请求
        try:
            with self.session.post(url=url_login, data=data_binary, timeout=10) as response:
                response.raise_for_status()
                return response.json()
        except requests.exceptions.RequestException as e:
            print(f"网络请求失败: {e}", file=sys.stderr)
        except json.JSONDecodeError:
            print(f"解析服务器响应失败，内容: {response.text}", file=sys.stderr)
        return None


def main():
    """主执行函数"""
    try:
        print("\n===== 开始登录 =====")

        # 1. 实例化登录对象
        nuist = NuistLogin(username=username, password=password)

        # 2. 自动获取IP地址
        if not nuist.get_ip():
            print("登录流程中断。")
            return

        # 3. 执行登录
        # 直接使用顶部配置的DEFAULT_NETWORK_ID
        response_json = nuist.login(channel_id=DEFAULT_NETWORK_ID)

        if not response_json:
            print("\n登录流程中断，未收到服务器有效响应。")
            return

        # print("\n===== 登录结果 =====")
        # print(json.dumps(response_json, indent=2, ensure_ascii=False))

        # 4. 处理响应结果
        if response_json.get("code") == 200 and response_json.get("data", {}).get("username"):
            print("\n--- 登录成功! ---")
            data = response_json['data']
            print(f"用户名: {data.get('username')}\n"
                  f"运营商: {data.get('outport')}\n"
                  f"登录IP: {data.get('usripadd')}")
        else:
            print('\n--- 登录失败! ---')
            error_data = response_json.get('data', {})
            error_msg = error_data.get('text', '未知错误')

            error_map = {
                'Passwd_Err': '密码错误',
                'UserName_Err': '用户名错误',
                'User_locked': '账号被锁定',
                'status_Err': '账号欠费或状态异常',
                'BindAttr_Err': '账号绑定属性错误',
                'Limit Users Err': '超出最大并发限制'
            }

            print('错误原因: ' + error_map.get(error_msg, error_msg))

    except Exception as e:
        print(f"\n发生未知错误: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()

