### AI 教学链接
- https://grok.com/c/2e7d4a05-f937-4950-ac6d-9fed14db5620?rid=29f53cea-b51f-4370-acee-74160bca9da9

### 安装

- 安装 shadowsocks-libev

```shell
sudo apt update
sudo apt install shadowsocks-libev -y
```

- 准备配置文件

```shell
mkdir -p ~/.config/shadowsocks
vi ~/.config/shadowsocks/client.json
```

```json
{
    "server": "tt.goo0d2025.com",
    "server_port": 17014,
    "local_address": "127.0.0.1",
    "local_port": 10808,
    "password": "f026-eb8d-440c-9162-342",
    "timeout": 300,
    "method": "aes-128-gcm",
    "mode": "tcp_and_udp",
    "fast_open": true
}
```

### 使用

- 临时启动客户端

```bash
ss-local -c ~/.config/shadowsocks/client.json
```

启动成功后，终端会显示类似 `listening on 127.0.0.1:10808` 的信息。此时 Shadowsocks 已在运行。

- 后台运行：

```bash
nohup ss-local -c ~/.config/shadowsocks/client.json > /dev/null 2>&1 &
```

- 测试是否正常工作

```bash
curl -x socks5://127.0.0.1:10808 https://ifconfig.me
```

- 使用完毕后关闭客户端
- **如果是前台运行**：直接按 `Ctrl + C` 即可停止。
- **如果是后台运行**：执行以下命令停止：

```bash
pkill -f ss-local
```
或
```bash
ps aux | grep ss-local
```


**临时使用完整快捷命令示例**：

```bash
# 启动（后台）
nohup ss-local -c ~/.config/shadowsocks/client.json > /dev/null 2>&1 &

# 测试
curl -x socks5://127.0.0.1:10808 https://ifconfig.me

# 使用完毕后关闭
pkill -f ss-local
```

### 会话
```shell
export HTTP_PROXY=socks5://127.0.0.1:10808
export HTTPS_PROXY=socks5://127.0.0.1:10808

export http_proxy=http://127.0.0.1:10808
export https_proxy=http://127.0.0.1:10808
```
