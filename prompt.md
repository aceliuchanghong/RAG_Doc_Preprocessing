提示词

---

我想做...



---

### 新服务器快速登录指南

1. 查看本机 `C:\Users\changhong.liu\.ssh` 下面 `id_rsa.pub`
2. `putty` 右键粘贴密码登录上来 找到 `.ssh/authorized_keys` 保存进去,然后执行`ssh-keygen -t rsa`生成服务器公钥`cat .ssh/id_rsa.pub`保存到`github`
3. 初步查看显卡 `nvidia-smi`
4. `ctrl+shift+p`打开`Remote-ssh`,保存,登录上去 eg:`ssh -p 24104 linux@175.155.64.171`
5. 创建环境等,放置项目
```shell
mkdir llch
cd llch/
git clone xxx
```
6. 设置git
```bash
git config --global user.email "aceliuchanghong.@gmail.com"
git config --global user.name "lawrence"

git config user.name
git config user.email
```

---




---




---




---



---




---



---




---



---




---



---




---



---




---



---




---



---




---



---




---



---




---



---




---



---




---



---




---



---




---



---




---



---




---



---




---



---




---



---




---



---




---



---




---
