# i-NUIST 南京信息工程大学校园网自动登录脚本

![Python](https://img.shields.io/badge/Python-3.x-blue.svg)
![NUIST](https://img.shields.io/badge/School-NUIST-green.svg)
![License](https://img.shields.io/badge/license-MIT-yellow.svg)

**南京信息工程大学-本部校园网自动认证脚本（最新版）**  
支持 Windows、Mac、iOS (Pythonista/Shortcuts)、Linux (OpenWrt/树莓派) 等多种平台。

---

## 📢 更新日志

### 2025.10.25 重大更新
- 🚨 **协议升级**：学校校园网进行了最新升级，认证地址变更为 `10.255.249.16` / `10.255.255.16`。
- 🔐 **加密算法**：针对所有登录请求信息加入了最新的 AES 加密逻辑。
- 🛠 **代码重构**：本仓库代码已完全重写以适配新的加密接口。

---

## ✨ 功能特性

- ✅ **自动获取 IP**：自动识别本机内网 IP，无需手动配置。
- ✅ **全运营商支持**：支持校园网、中国移动、中国电信、中国联通。
- ✅ **最新加密协议**：内置最新加密计算，完美模拟浏览器行为。
- ✅ **多平台兼容**：Python 编写，可在任何支持 Python 的设备上运行（含路由器）。
- ✅ **详细日志**：清晰的登录成功/失败反馈，包含错误原因解析。

---

## 🛠️ 安装与配置

### 1. 环境准备

本脚本依赖 Python 3.x 环境。请确保已安装以下依赖库：

```bash
# 安装依赖库 (requests 和 pycryptodome)
pip install requests pycryptodome
```

> **注意**：加密库请务必安装 `pycryptodome`，不要直接安装 `crypto`，否则可能会报错。

### 2. 下载脚本

```bash
git clone https://github.com/3355190239/i-NUIST.git
cd i-NUIST
```

### 3. 修改配置

打开脚本文件（例如 `i-NUIST_login.py`），找到 **--- 1. 配置 ---** 区域，填入你的账号信息：

```python
# ==============================================================================
# --- 1. 配置 ---
# ==============================================================================

# 基础常量 (如遇认证地址变更，请修改此处)
base_url = 'http://10.255.255.16' 

# --- 用户信息配置 ---
username = "202412xxxxx"  # 你的学号
password = "xxxxx"        # 你的上网密码

# 网络供应商配置
# "1": 校园网, "2": 中国移动, "3": 中国电信, "4": 中国联通
channel = "1" 
```

---

## 🚀 运行方法

### Windows / Mac / Linux

在终端或命令行中运行：

```bash
python login.py
```

如果登录成功，你将看到如下输出：

```text
===== i-NUIST校园网登录 =====
✅ 自动获取IP成功: 10.xxx.xxx.xxx

--- ✅ 登录成功! ---
用户名: 202412xxxxx
运营商: CMCC (中国移动)
登录IP: 10.xxx.xxx.xxx
```

---

## 🤖 自动化部署 (OpenWrt / Linux)

如果你拥有 OpenWrt 路由器或 Linux 服务器，可以通过 `crontab` 设置定时任务，实现掉线自动重连。

1.  确保路由器已安装 Python3 和必要的库（可能需要通过 `opkg` 安装）。
2.  编辑定时任务：

```bash
crontab -e
```

3.  添加如下规则（每 5 分钟检测一次）：

```bash
# 每5分钟运行一次脚本，日志输出到 /tmp/nuist_login.log
*/5 * * * * /usr/bin/python3 /root/i-NUIST/login.py >> /tmp/nuist_login.log 2>&1
```

---

## ⚠️ 常见错误代码说明

| 错误代码 | 含义 | 建议 |
| :--- | :--- | :--- |
| **Passwd_Err** | 密码错误 | 请检查配置文件中的密码 |
| **UserName_Err** | 用户名错误 | 请检查学号是否正确 |
| **status_Err** | 账号欠费/异常 | 检查宽带账户余额 |
| **Limit Users Err** | 超出并发限制 | 注销其他设备的登录状态 |
| **获取会话失败** | 网络不通 | 请确保已连接 i-NUIST WiFi 或网线 |

---

## ⚖️ 免责声明

本项目仅供学习交流使用，请勿用于任何商业用途或破坏学校网络安全。使用本脚本产生的任何后果由使用者自行承担。

---

**如果觉得好用，请给个 Star ⭐️ 吧！**
```
