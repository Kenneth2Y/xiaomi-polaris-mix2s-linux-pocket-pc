# 固件路径审计

当前 polaris DTS 使用带厂商目录的 `qcom/sdm845/Xiaomi/polaris/`，蓝牙使用 `qca/Xiaomi/polaris/`。现有固件软件包则主要安装在 `qcom/sdm845/polaris/` 和 `qca/polaris/`。

完整 dmesg 已证实 zap、IPA、CDSP、Venus、modem MBA、蓝牙 NVM 请求路径缺失。文件实际存在于旧路径；不能把这些 -2 都视为缺少固件二进制，也不能因为路径修正就宣称相应硬件已经工作。

`patches/0003-firmware-polaris-vendor-aliases.patch`：

- 保留旧文件位置，为 Qualcomm 目录的现有文件和 polaris 蓝牙 NVM 添加相对软链接。
- 修改 GPU initramfs 清单为旧源文件到当前请求目标的映射。
- 独立 recipe 在 `build/firmware-recipe`；打包函数在本地临时 pkgdir 实际执行。
- 14 个链接均可解析、都落在暂存包内部，对应文件 SHA-256 记录在 `logs/firmware-alias-validation.json`。
- 未安装固件软件包；test01 镜像单独修复早期 GPU zap 路径。Wi-Fi 阶段通过 `tools/wifi-firmware-stage-root.sh` 在 rootfs 增加 12 个 Qualcomm 相对别名，保留原有 GPU 别名；没有覆盖固件文件。重试现有 mpss remoteproc 后启动成功，test02 冷启动也确认 mpss/CDSP running。未运行 mkinitfs/boot-deploy，未刷写基带分区。

initramfs 基线审计显示：zap 只有旧路径，内核又在 0.7 秒左右请求新路径。因此完整 rootfs 中已有的单文件软链接不能修正这一早期失败。测试镜像的离线 initramfs 将额外包含正确目标路径的相同固件内容。

仍需逐项检查实际硬件功能。WLAN 另需 polaris host-cap skip quirk；test02 已枚举 wlan0 并扫描到用户指定的 2.4/5 GHz 热点，详见 `WIFI_AUDIT.md`。mpss/CDSP running 不代表音频或蜂窝服务已验证。蓝牙 NVM 路径仍待修复。
