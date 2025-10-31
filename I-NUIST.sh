#!/bin/bash

# ==============================================================================
# --- 1. 用户信息配置 ---
# 请将这些值替换为您的真实信息
# ==============================================================================
USERNAME="2024124XXXX"
PASSWORD="XXXX"

# --- 默认网络供应商配置 ---
# "1": 校园网, "2": 中国移动, "3": 中国电信, "4": 中国联通
DEFAULT_NETWORK_ID="1"

# ==============================================================================
# --- 2. 核心逻辑 (通常无需修改) ---
# ==============================================================================

# --- 脚本设置 ---
# 当任何命令失败时立即退出脚本
set -e

# --- 依赖检查 ---
# 确保 curl, openssl, jq, xxd, 和 shasum/sha256sum 已安装
for cmd in curl openssl jq xxd; do
    if ! command -v "$cmd" > /dev/null 2>&1; then
        echo "错误: 依赖 '$cmd' 未安装。请先安装它。" >&2
        exit 1
    fi
done

# 自动选择SHA256命令
SHA256_CMD=""
if command -v sha256sum > /dev/null 2>&1; then
    SHA256_CMD="sha256sum"
else
    SHA256_CMD="shasum -a 256"
fi

# --- 加密与网络常量 ---
readonly DEFAULT_KEY_PREFIX="axaQiQpsdFAacccs"
readonly BASE_URL='http://10.255.255.16' # 请确保这是您学校的正确认证网关地址

# --- 函数定义 ---

#
# 模拟JS的加密盐生成逻辑
#
get_salt_from_username() {
    username="$1"
    combined_string="${DEFAULT_KEY_PREFIX}${username}"
    # 使用反引号进行命令替换
    salt=`printf "%s" "$combined_string" | $SHA256_CMD | awk '{print $1}' | cut -c1-16`
    echo "$salt"
}

#
# 模拟JS的AES加密逻辑 (AES/ECB/PKCS7)
#
encrypt_aes_ecb() {
    data_to_encrypt="$1"
    key="$2"
    key_hex=`printf "%s" "$key" | xxd -p`
    # 使用反引号进行命令替换
    encrypted_data=`printf "%s" "$data_to_encrypt" | openssl enc -aes-128-ecb -K "$key_hex" -nosalt | xxd -p | tr -d '\n'`
    echo "$encrypted_data"
}

#
# 自动获取IP地址
#
get_ip() {
    url_ip="${BASE_URL}/api/v1/ip"

    # 使用反引号进行命令替换
    response=`curl -s -f --connect-timeout 5 "$url_ip"`
    if [ $? -ne 0 ]; then
        echo "❌ 自动获取IP失败: 无法连接到认证网关 (${BASE_URL})。" >&2
        echo "   请检查: 1. 是否已连接到校园网Wi-Fi。 2. 网关地址是否正确。" >&2
        return 1
    fi

    # 使用反引号进行命令替换
    ip_address=`echo "$response" | jq -r '.data'`

    # 使用兼容性更好的 [ ... ] 和 =
    if [ -z "$ip_address" ] || [ "$ip_address" = "null" ]; then
        echo "❌ 获取IP失败：服务器未返回有效的IP地址。" >&2
        echo "   服务器响应: $response" >&2
        return 1
    fi

    echo "$ip_address"
}

# ==============================================================================
# --- 3. 主程序 ---
# ==============================================================================

main() {
    echo "===== 校园网自动登录脚本 ====="
    echo "===== 正在自动获取IP地址... ====="

    # 使用反引号进行命令替换
    current_ip=`get_ip`

    echo "✅ 自动获取IP成功: $current_ip"

    echo "===== 开始登录流程 ====="

    echo "--- [步骤 1/4]: 生成加密盐 ---" >&2
    salt=`get_salt_from_username "$USERNAME"`
    echo "   盐已生成。" >&2

    echo "--- [步骤 2/4]: 加密所有登录字段 ---" >&2
    encrypted_username=`encrypt_aes_ecb "$USERNAME" "$DEFAULT_KEY_PREFIX"`
    encrypted_password=`encrypt_aes_ecb "$PASSWORD" "$salt"`
    encrypted_ifautologin=`encrypt_aes_ecb "1" "$salt"`
    encrypted_channel=`encrypt_aes_ecb "$DEFAULT_NETWORK_ID" "$salt"`
    encrypted_pagesign=`encrypt_aes_ecb "secondauth" "$salt"`
    encrypted_usripadd=`encrypt_aes_ecb "$current_ip" "$salt"`
    echo "   字段加密完成。" >&2

    echo "--- [步骤 3/4]: 构造JSON请求体 ---" >&2
    payload=`printf '{"username":"%s","password":"%s","ifautologin":"%s","channel":"%s","pagesign":"%s","usripadd":"%s"}' \
        "$encrypted_username" \
        "$encrypted_password" \
        "$encrypted_ifautologin" \
        "$encrypted_channel" \
        "$encrypted_pagesign" \
        "$encrypted_usripadd"`
    echo ${payload}

    echo "--- [步骤 4/4]: 发送登录请求 ---" >&2
    login_response=`curl -s -X POST \
        -H "Content-Type: application/json;charset=gbk" \
        -H "Accept: application/json, text/plain, */*" \
        -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36" \
        -H "Origin: ${BASE_URL}" \
        -H "Referer: ${BASE_URL}/" \
        -d "$payload" \
        "${BASE_URL}/api/v1/login"`

    echo -e "\n===== 登录结果 ====="

    if ! echo "$login_response" | jq . > /dev/null 2>&1; then
        echo "❌ 登录失败：服务器响应格式错误，非JSON。"
        echo "   原始响应: $login_response"
        exit 1
    fi

    echo "$login_response" | jq .

    code=`echo "$login_response" | jq -r '.code'`
    username_from_response=`echo "$login_response" | jq -r '.data.username'`

    if [ "$code" = "200" ] && [ "$username_from_response" != "null" ]; then
        echo -e "\n--- ✅ 登录成功! ---"
        outport=`echo "$login_response" | jq -r '.data.outport'`
        user_ip=`echo "$login_response" | jq -r '.data.usripadd'`
        echo "用户名: $username_from_response"
        echo "运营商: $outport"
        echo "登录IP: $user_ip"
    else
        echo -e '\n--- ❌ 登录失败! ---'
        error_msg=`echo "$login_response" | jq -r '.data.text'`

        case "$error_msg" in
            "Passwd_Err") echo '错误原因: 密码错误' ;;
            "UserName_Err") echo '错误原因: 用户名错误' ;;
            "User_locked") echo '错误原因: 账号被锁定' ;;
            "status_Err") echo '错误原因: 账号欠费或状态异常' ;;
            "BindAttr_Err") echo '错误原因: 账号绑定属性错误' ;;
            "Limit Users Err") echo '错误原因: 超出最大并发限制' ;;
            *) echo "错误原因: ${error_msg:-未知错误，请查看上方JSON详情}" ;;
        esac
    fi
}

# --- 脚本执行入口 ---
main
