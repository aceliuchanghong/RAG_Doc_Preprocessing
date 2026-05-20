## 生成

```bash
ssh-keygen -t rsa
```

1. 查看本机 `C:\Users\xx\.ssh` 下面 `id_rsa.pub`
2. `putty` 右键粘贴密码登录上来 找到 `.ssh/authorized_keys` 保存进去,然后执行`ssh-keygen -t rsa`生成服务器公钥`cat .ssh/id_rsa.pub`保存到`github`
3. 初步查看显卡 `nvidia-smi`
4. `ctrl+shift+p`打开`Remote-ssh`,保存,登录上去 eg:`ssh -p 24104 linux@175.155.64.171`
5. 创建环境等,放置项目
