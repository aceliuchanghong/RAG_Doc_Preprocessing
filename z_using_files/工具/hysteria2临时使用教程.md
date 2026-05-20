## Hysteria

### 1. 下载 Hysteria 2 客户端二进制文件（临时使用）
```bash
mkdir -p ~/hysteria2 && cd ~/hysteria2

# 适用于大多数 Ubuntu
curl -Lo hysteria https://download.hysteria.network/app/latest/hysteria-linux-amd64
chmod +x hysteria
```

### 2. 创建客户端配置文件
```bash
vi config.yaml
```


```yaml
server: jp1.lovehonor.top:9005   # IP:端口

auth: f064f526-eb8d-440c-9162-3b39026a3742           # 服务器提供

bandwidth:
  up: 20 mbps                     # 根据网络带宽调整，不要超过实际带宽
  down: 100 mbps

socks5:
  listen: 127.0.0.1:10808         # 使用的端口

http:
  listen: 127.0.0.1:10809

tls:
  insecure: true                    # 跳过证书验证（临时使用）
  sni: jp1.lovehonor.top        #  SNI
```


### 3. 启动 Hysteria 2 客户端

**前台运行（临时）：**
```bash
cd ~/hysteria2
./hysteria -c config.yaml
```

**后台运行：**
```bash
nohup ./hysteria -c config.yaml > ~/hysteria.log 2>&1 &
```

启动成功会看到 “connected to server” 等提示。

### 4. 测试是否生效
```bash
curl -x socks5://127.0.0.1:10808 https://ifconfig.me
curl -x http://127.0.0.1:10809 https://ifconfig.me

curl -I -x http://127.0.0.1:10809 https://pypi.org/simple/
```
### 5. 使用完毕后停止
```bash
pkill -f hysteria
```

**后续使用 uv** 与之前 Shadowsocks 相同：

```shell
# uv 使用
export UV_INDEX_URL="https://pypi.tuna.tsinghua.edu.cn/simple"

export HTTP_PROXY=socks5://127.0.0.1:10808
export HTTPS_PROXY=socks5://127.0.0.1:10808

export HTTP_PROXY=http://127.0.0.1:10809
export HTTPS_PROXY=http://127.0.0.1:10809
export ALL_PROXY=http://127.0.0.1:10809

export NO_PROXY="localhost,127.0.0.1,::1"

unset HTTP_PROXY
unset HTTPS_PROXY
unset ALL_PROXY
unset NO_PROXY

unset http_proxy
unset https_proxy
unset all_proxy
unset no_proxy
```


使用 git 参考其设置文件
