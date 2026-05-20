## 加速下载

```bash
git config --global user.email "aceliuchanghong.@gmail.com"
git config --global user.name "lawrence-pc"

git config user.name
git config user.email
```

```bash
# 只能是 http 相关的才可以,ssh 不行
export http_proxy=http://127.0.0.1:10808
export https_proxy=http://127.0.0.1:10808

# powershell
$env:http_proxy = "http://127.0.0.1:10808"
$env:https_proxy = "http://127.0.0.1:10808"

$Env:NO_PROXY="127.0.0.1,localhost,::1"
```

修改了`~/.ssh/config`:

```
Host github.com
  User git
  ProxyCommand connect -S 127.0.0.1:10808 %h %p
```
