# MIX 2S 分阶段执行与验收计划

记录日期：2026-11-04（Asia/Shanghai）。以用户本次明确授权为执行边界；交接文档中的历史状态、推测及建议分别核对，不把它们视作已验证结论或刷机许可。

## 阶段 0：基线、连接与实况

- 备份 Windows export/boot.img，比较复制前后 SHA-256，原文件不覆盖。
- 核验源码包、原始源码备份、包脚本及历史构建日志。
- 通过临时 SSH ControlMaster 复用用户交互认证；不新建无口令私钥，不保存密码。
- 读取手机显示、输入、USB、固件、电源和启动日志；区分 journal 与完整 dmesg。
- 输出状态矩阵、构建环境说明及回退手册。

验收：备份哈希相同、SSH 可达、关键差异有文件或日志证据。

## 阶段 1：构建恢复、LCD 与触摸

- 从已验证的源码压缩包使用标准 APKBUILD 的解包、补丁、配置、build/package 阶段。
- 复现并记录 --src/rsync 的 timeconst.bc 排除问题。
- 单独保留交接中的 DIGTOP 实验；先构建只有诊断日志的 test01。
- 审计 probe 时 assigned-clock-parents、DISPCC parent-enable 和 PHY enable 的关系。
- 暂存匹配版本的内核、DTB 和模块；离线构造独立 boot-test 文件，记录组件校验值和分区尺寸检查。
- 上机前核对测试内核模块如何安全提供给完整 rootfs。仅 initramfs 匹配不足以保证切根后的所有驱动可加载。
- 首次设备启动实验另行提出具体操作、风险与回退依据，不自动执行 Fastboot。
- 实际验收包括像素输出、背光调整、触摸坐标/多点/边缘，而非仅节点存在。

## 阶段 2：替代通信与 USB Host（早期必须项）

- 审计 WLAN 缺失原因，优先固件、remoteproc 和驱动绑定。
- 建立 Wi-Fi SSH 或安排用户现场恢复。
- 审计 peripheral-only DTS、PMIC Type-C/ID 检测及 VBUS 电源控制，不只修改 dr_mode 字符串。
- 单独准备 Host 实验；用户连接 Hub、键鼠，验证枚举、输入、热插拔和回切 NCM。

验收：LCD + 触摸 + USB Host 全部通过实际硬件测试；当前 NCM 不计入 Host 验收。

## 阶段 3：GPU、无线、音频、蜂窝网络

- GPU 固件路径和 initramfs 一致性、DRM/KMS 及实际渲染。
- Wi-Fi 扫描/连接/重连；凭据交互输入，不保存明文秘密。
- 音频分别验证扬声器、耳机及麦克风，先低音量。
- 蜂窝分开验证 remoteproc、QRTR、SIM、注册、数据、短信、通话；不写基带/校准分区。

## 阶段 4：可靠性

- 充电/电池/温度可观测性，休眠与唤醒，通信恢复，持续负载和 USB 供电。
- 每阶段归档补丁、版本、构建/设备日志、失败原因、未解决项与回退方法。

## 设备操作边界

初始阶段仅授权软件开发；此后用户在现场明确授予自主刷机判断权限，已授权经核验的独立 boot 候选启动、写入及重启。继续保留工作基线、检查 product/分区尺寸/镜像哈希并记录结果。禁止擦除 userdata、修改 Qualcomm 启动链、基带/校准分区、重锁 Bootloader。手机的自动内核部署配置可能写 boot，因此不在手机运行 boot-deploy、mkinitfs 或内核软件包更新。Wi-Fi SSH 通过前不切换 USB Host；最新 Wi-Fi 验收见 `WIFI_AUDIT.md`。
