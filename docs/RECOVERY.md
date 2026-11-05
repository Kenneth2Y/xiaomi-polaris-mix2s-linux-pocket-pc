# 恢复与回退

本项目所有公开镜像都只是boot相关产物，不是完整rootfs备份。当前基线test06，SHA-256：

```text
e9c7591b9a044f63d3fc4036cee778217ce7fe31a9a31c3cc5205b4977c9adce
```

Release保存实际已刷入镜像和匹配模块，先下载SHA256SUMS并校验。开发原件另有独立只读本地备份；原SSH-only、test01、test02、test05均保留，没有被当前版本覆盖。

## 运行时回退

通过无线SSH：停止图形登录可用sudo systemctl stop greetd，再sudo chvt 2；恢复sudo systemctl start greetd。外接键盘Ctrl+Alt+F2进入tty2，Ctrl+Alt+F7返回图形界面。

需要停止test06角色控制器：

```sh
sudo systemctl stop polaris-usb-role-test06.service
sudo systemctl restart polaris-charger-test05.service
```

后者是历史命名的charger-only回退，允许test05/06，并先恢复500mA输入。正常使用的角色服务会自动管理充电/Host，不需日常手动执行。新release须先渲染并审核条件，不能以旧unit跳过来判断硬件坏了。

## boot恢复

若SSH不可用，现场进入Fastboot，核验只有一个设备、product=polaris、Bootloader已解锁、boot尺寸与镜像哈希。再仅恢复已验证boot并重启。示例是操作顺序，不是默认自动刷写：

```sh
fastboot getvar product
fastboot getvar partition-size:boot
fastboot getvar unlocked
# 检查SHA256SUMS并确认相应rootfs模块已存在后，按本次授权执行：
fastboot flash boot boot-polaris-test06.img
fastboot reboot
```

不要擦除其他分区、改Qualcomm启动链或重锁Bootloader。单台旧手机的既有授权不继承到新设备。

**手机/boot/boot.img不是可靠回退来源。** GUI安装曾使它被系统钩子重建，文件与实际boot分区不同。要使用Release中的已验证镜像和记录的SHA256，参见事故复盘。

旧test02是USB NCM/Wi-Fi基线，但test06的PC/NCM动态角色重新绑定尚未验收。Wi-Fi保留作为当前调试通道，不能把role=device当作NCM已实际可用。
