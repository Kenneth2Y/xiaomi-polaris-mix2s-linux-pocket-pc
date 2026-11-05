# 设备操作顺序

## 先只读识别

设置未纳入Git的POLARIS_SSH_HOST和可选POLARIS_SSH_USER，执行scripts/device/read-only.sh。密码只在终端输入，不通过命令参数或环境变量传密码。沿用可信known_hosts；首次指纹由用户在可信通道核对，不关闭校验。

确认实际compatible=中包含xiaomi,polaris、运行内核、USB角色、外部输入/电池电流和温度、可用Wi-Fi及boot标签。换手机不能套用原设备分区路径。读完先核对文档差异。

## APK与GUI

任何APK更新前先处理已知钩子：发行版支持的/etc/deviceinfo覆盖deviceinfo_flash_kernel_on_update="false"，通过与boot-deploy相同的/usr/share/misc/source_deviceinfo核验。项目安装命令同时使用KERNEL_INSTALL_BYPASS=1与apk --preserve-env。

```bash
# 以下在手机上；默认仅输出计划
sh install-gui.sh
# 用户已授权并审核计划、供电和回退后才执行
sudo sh install-gui.sh --execute
```

先模拟依赖，不默认apk upgrade。Phosh最小包组合必须含stevia-schemas；仅有stevia二进制会因mobi.phosh.osk schema缺失退出。不要无意装入会接管现有USB实验链路的完整UI元包/USB-moded。

配置见configs/rootfs：DSI-1 scale=3、tty7图形登录、独立tty2恢复控制台。systemd依赖是累加关系，空Conflicts=不能抹掉vendor对tty1的冲突；不要机械复用早期失败drop-in。

## 内核候选部署

1. 生成独立镜像、release、匹配模块与公开证书，完成离线校验；保留可显示/联网的旧镜像和模块。
2. 核对当前设备、boot分区标签和尺寸、供电、电量/温度、候选哈希、回退通道与本次授权。
3. 先安装独立匹配模块，不覆盖旧版本；审核新release的systemd条件和加载顺序。
4. boot-only操作先保存当前分区备份；只处理动态解析的boot标签，不硬编码/dev/sde45。
5. 完成写入、fsync、实际镜像长度前缀回读后再正常重启。核对新boot-id、uname、实际DT与模块，不能只看Fastboot OKAY。
6. 首先确认Wi-Fi/GUI/回退，再手动测试新电源控制器；没有依据不提高电压/电流或启用PD。
7. source与sink分别验证：空口关闭源VBUS；DCP输入和电池电流为正；Hub源500mA、枚举/真实输入；断开、正反插、再回充电；最后验证自动加载和重启。

保留的开发现场写boot脚本位于archive/legacy-tools，仅用于复盘，不是新设备部署入口。维护脚本本次没有自动操作读者设备。

## Wi-Fi与秘密

连接时用nmcli --ask让用户在终端输入PSK。原方案使用systemd-creds的设备本地加密存储和LoadCredentialEncrypted，NetworkManager profile不保存明文PSK。无TPM时root和完整磁盘仍可能解密；这不是硬件密封。加密凭据、主机密钥、known_hosts和rootfs备份都不得上传。通用化加密配置安装器仍列入后续任务，历史实现仅供审阅。
