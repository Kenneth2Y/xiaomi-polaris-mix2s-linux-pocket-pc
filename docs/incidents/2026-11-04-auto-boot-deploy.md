# GUI安装触发自动boot写入

## 发生了什么

审核新增图形依赖时没有新增内核/mkinitfs/boot-deploy，但系统里已经存在的APK trigger仍运行了mkinitfs和boot-deploy，并按deviceinfo_flash_kernel_on_update=true覆写boot。只检查“是否新增内核包”不足以阻止已有钩子。

## 发现、恢复与验证

安装后实际boot哈希检查失败，运行中的test05和无线SSH仍在。立即明确告知用户，核验归档test05、动态boot标签与64MiB尺寸，经受控boot-only写入恢复，并回读哈希确认；没有重启到意外生成镜像，也没有写其他分区。随后才明确部署独立test06。

## 固化的修复

1. 使用发行版支持的/etc/deviceinfo覆盖自动刷写为false，并通过boot-deploy同一loader核验。
2. 项目APK命令使用KERNEL_INSTALL_BYPASS=1与--preserve-env。实际测试确认在生成前输出Skipping mkinitfs。
3. 每次有部署影响的安装后检查实际分区，而不是/boot/boot.img文件。
4. 不删除系统trigger或把系统可执行文件替换为假程序。

维护入口scripts/device/install-gui.sh已经前置此规则。历史恢复与验证日志在reports/test06。原始镜像和所有已验证工作镜像独立保留。
