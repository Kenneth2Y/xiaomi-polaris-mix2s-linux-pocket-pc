# USB Host/电源审计

本轮实测当前链路为 USB NCM Gadget。静态源码及运行中 DT 都是 `dr_mode = "peripheral"`，没有读到 usb_role/typec class 接口；因此当前不能通过 sysfs 简单切换 Host，也不能把双角色内核配置视为已实现 Host。

最新结论：2026-11-05 test06 已通过充电/Host 切换、真实键鼠输入、USB-C 正反插与开机自动恢复；下面保留阶段历史，最新细节见末节。

上述为 test02 基线状态。2026-11-04 后续已完成 test03/test04 实机实验，当前进度见下文；尚不能宣称键盘或 USB Host 全部工作。

本地 7.1-rc1 源码已有 PMI8998 charger 驱动及节点，但 polaris DTS 没有启用 charger/电池节点。运行中 `/sys/class/power_supply` 无设备。这是供电可观测性和 VBUS 实验前需要解决的问题，不代表已判断电池硬件故障。

USB Type-C 需关注 PMI8998 第一代 SMB2 硬件，与现有 PM8150B 后端不同。2026-09-26 原始 RFC 中提出了 gen1 后端与 PMI8998 DT 节点；其供电部分仍依赖板级 VBUS 方案。仅改为 otg 或添加 usb-role-switch 不足以完整描述硬件。

参考的一手开发资料：

- gen1 RFC 原始邮件镜像：https://lkml.rescloud.iu.edu/hypermail/linux/kernel/2609.3/06016.html
- PMI8998 DT RFC：https://www.mail-archive.com/phone-devel%40vger.kernel.org/msg00685.html
- 作者项目：https://github.com/samcday/qcom-pmic-typec-smb2 （其声明尚未在手机运行；不能当作已验证驱动）

后续步骤：核对本机 charger/OTG boost、CC 检测、VBUS 防反灌及 Hub 供电；离线移植/构建适配。实际切换前，先有 Wi-Fi SSH 或用户现场进入 Fastboot 的安排。保持当前 NCM 镜像作为回退。

## 2026-11-04 test03：固定 Host 数据通路

用户确认同一套手机、无独立供电口的 Hub、键鼠在 Android 下可正常同时工作。Wi-Fi SSH 和加密凭据已通过拔 USB、用户重启、独立 Windows SSH 登录及 Agent 复核。

- `patches/0006-polaris-usb-fixed-host-diagnostic.patch` 只把 DWC3 `dr_mode` 从 peripheral 改为 host。独立 DTB 构建后恢复原 prepared 源码和 test02 DTB。
- `images/boot-test-03-usb-host.img` SHA-256：`83eda61cff344b3fa8486b5e34626ee7332dc2682d7edccc1abba6b2eae42eb0`。与 test02 的压缩内核、initramfs、模块完全相同。
- 18:27 仅 Fastboot 写 boot，18:28 重启。实际分区前缀与镜像哈希一致，运行 DT 为 host，两个 xHCI 根 Hub 正常出现，Wi-Fi 自动恢复。
- 用户接 Hub/键盘后没有外部 USB 设备或输入节点，键盘无响应。未改 PMIC/Type-C/charger/VBUS 寄存器。xHCI 的 USB3 根 Hub 描述不代表本机物理 USB3；板级 PHY 仍限制 USB2。
- 日志：`test03-first-boot-host-state-01.log`、`test03-host-verify-01.log`、`test03-hub-attach-no-enumeration-01.log`。

当前内核强制 integrity lockdown，DWC3 debugfs 可读写接口即使 root 读取也会被拒绝。没有关闭完整性保护、使用裸内存写入或加载未受信模块。

## test04：签名 SMB2 no-PD 驱动与受控供电实验

独立构建树 `build/recipe-test04`；release `7.1.0-rc1-sdm845-polaris-test04`。配置只改变 LOCALVERSION 并增加 `CONFIG_TYPEC_QCOM_PMIC_SMB2=m`，保留完整性保护。模块导入自 [samcday/qcom-pmic-typec-smb2](https://github.com/samcday/qcom-pmic-typec-smb2)，固定 revision `4164801fa70216a8687cdfdc57026df740926a14`，保留许可证和作者。该上游仅有静态/构建验证，未有实机验证；本机结果须独立记录。

- 新 Type-C 驱动强制拒绝 PD-enabled connector。DTS 使用 `pd-disable`、普通 Type-C 默认电流；USB 恢复 otg + role switch、默认 peripheral。
- 修正 PMI8998 VBUS 电流表为 250 mA 步进，独立匹配 `qcom,pmi8998-vbus-reg`；不冒用 PM8150B 身份。source/sink 测试均限制 500 mA。
- 启用 charger/FG 节点并增加 battery phandle。4.4 V 上限来自 MiCode polaris-o-oss 的 ATL/COS 3400mAh 原厂电池 profile；初次测试把充电电流限制为 500 mA，并在 charger 各输入路径钳制输入电流。
- 补丁 `0007-polaris-smb2-nopd-test04.patch`、`0008-polaris-smb2-test04-bindings.patch`，checkpatch 均 0 错误/0 警告。完整内核与 1156 个匹配模块构建成功。
- 19 个 initramfs 模块和 Type-C/TCPM/VBUS/charger/FG 五个关键模块，共 24 个 CMS 签名经 OpenSSL 实际验证；签名证书确认位于新内核中。所有模块版本、依赖闭包和镜像/CPIO 往返通过。完整 dtschema 工具当前不可用，未把 DTC 编译等同于 schema 全通过。
- 镜像 `boot-test-04-usb-typec.img`，29,515,776 字节，SHA-256 `7de6ede15d2f4a7716cc138f909366e17dfa3fa174c8c6fbe04aec8bee0a76e5`。
- 手机只新增 `/usr/lib/modules/7.1.0-rc1-sdm845-polaris-test04` 和 `/etc/modprobe.d/polaris-usb-test04.conf`；initramfs 有相同黑名单，禁止自动加载 Type-C/charger/VBUS 三个实验模块。
- 18:53 仅刷 boot 并重启，Wi-Fi SSH 自动恢复。实际分区哈希正确；三个实验模块均未加载，role=device，FG 可读约 64%、3.81 V、30.5°C。FG 的 Charging 文本会按电流推断，尚未验证方向/充电准确性，不应作为完成充电验证的证据。

### 首次手动加载与失败证据

用户确认 USB-C 口无任何线缆后，手动加载签名模块：charger 和 VBUS provider 成功；VBUS 500000 µA、disabled；Type-C 端口注册，PD disabled。无插线检查通过，无 deferred device 或模块验证错误。

接 Hub 后用户观察到指示灯闪烁、键盘无响应。已采集并卸载实验控制器，不保留反复输出。再次使用签名模块自带 `dyndbg=+p` 进行限时调试，外部 systemd 计时器在 25 秒切断实验，正常采集后更早卸载：

- CC 检测实际读到 `status4=0x91`，CC1=Rd、CC2=Open，能识别下游设备。
- TCPM 在 SRC_ATTACH_WAIT → SRC_ATTACHED → SRC_UNATTACHED 间循环。
- 每次 `set_vbus: on (-110)`，即源 VBUS 确认 250 ms 超时后回退。控制器尚未完成进入 Host，外部 Hub 没有枚举。
- ADC 限时采样 80 次，VBUS ADC 最大 0 µV，其中调压器命令状态 enabled 10 次。该观测尚不能单独排除源模式 ADC/状态位语义差异；需要 OTG 专用硬件状态确认。
- 日志：`test04-usb-idle-load-01.log`、`test04-hub-flashing-stop-01.log`、`test04-bounded-cc-debug-02.log`、`test04-bounded-vbus-adc-01.log`。

对比小米原厂 `smb-lib.c`，PMI8998 的 VBUS enable 先通过受保护写入暂停 buck/boost 的 1-in-8 模式，再置 OTG_EN；disable 反序恢复。现通用 PM8150B provider 缺少该时序。原厂 `smb-reg.h` 定义 OTG_STATUS=0x1109、soft-start-done=BIT(3)、enabled-state=2；不能把推测的寄存器位直接用于设备。

下一版先修正专用升压时序、加入真实软启动/故障状态核验和失败锁止，继续保持 no-PD 与 500mA 上限。当前实验 Type-C 控制器已卸载，自动加载黑名单仍保留。

## 回退

优先 Fastboot `flash-test --profile test02`、`reboot --profile test02`，恢复 LCD＋触摸＋Wi-Fi＋USB NCM 基线；只读备份 `baseline/boot-lcd-wifi-test02-20261104.img`。原 test01 和最初 SSH-only 镜像也保留。新版本模块目录独立，回退后不会混用。黑名单文件可在结束实验后精确删除；不运行 boot-deploy、mkinitfs 或内核包自动部署钩子。

用户提供的 [nixalpha Android common tree](https://github.com/nixalpha/android_device_xiaomi_mi845-mainline) 已读取 BoardConfig、init、模块及内核配置片段。它指向单独内核树，所查文件没有本机 Type-C driver；其 boot header v1/Android 分区方案未引入本项目。详见 `logs/nixalpha-mi845-reference-audit.json`。


## test05：真实升压就绪检测与首次 Hub/HID 枚举

独立 release `7.1.0-rc1-sdm845-polaris-test05`；镜像 SHA-256 `ac2d4496089a3f7658b8cbdae6b6b364ffe81855b42d4434bf3943198eb1cb95`，29,515,776 字节。补丁 `0009-polaris-pmi8998-boost-start-test05.patch` 增加原厂 1-in-8 halt 时序、OTG 专用软启动/故障核验、失败锁止及可选 source-aware 检测；无 PD，source/sink 电流仍限 500 mA。1156 个匹配模块独立安装，24 个关键模块 CMS 实际验证通过；DTB 与 test04 相同，配置仅更改 release。

19:22 仅刷 boot 并重启，Wi-Fi 自动恢复；`test05-inert-boot-audit-01.log` 已核验实际 boot 前缀、release、黑名单和初始未加载状态。无插线加载后 VBUS disabled、500000 µA，通过 idle 检查。

### 默认检测失败与定位

用户接 Hub 后观察到闪一下即熄灭，键盘无反应。首次尝试因 Type-C VBUS 位确认失败而关断；后续 source_start_failed 锁止，TCPM 仍有软件循环，但不再反复开启升压。已卸载控制器停止该轮测试。

内核 journal 保留了首个原始升压结果：`cmd=0x1 status=0xa fault=0x0 result=0`，软启动完成、enabled state=2、无故障；默认 TYPE_C_STATUS_4 的 VBUS 位仍不能确认源供电。`test05-boost-history-01.log` 记录两次同样结果，关闭后 provider 为 disabled/off/500000 µA。因此未执行输入 suspend 假设测试，也未提高电流。

### source_otg_ready=1 的对照实验

在同一个签名内核/模块上，以 `source_otg_ready=1` 加载；此参数仅在本机源模式下通过 regulator_is_enabled 获取 provider 的真实软启动和故障状态，绝不是仅信任 OTG_EN 命令位。sink 检测仍用原 Type-C 检测路径。

25 秒独立 systemd 自动停止保护下，TCPM 达到 SRC_READY，data role=host、power role=source；VBUS enabled，升压同样 status=0xa/fault=0。实际枚举：GenesysLogic 05e3:0610 USB2.1 Hub、05e3:0751 USB Storage、Logitech 046d:c31d USB Keyboard；出现三个 Logitech evdev 输入节点。USB Storage 只是枚举到的接口，未挂载或读写介质。详见 `test05-bounded-ready-01.log`。

随后重新加载相同参数供交互输入和热插拔验证。第一次加载脚本因重启已清空 /tmp 的输入监测程序而退出，并由 EXIT trap 关闭控制器；补传只读程序并核对 SHA-256 后，第二次加载成功。日志 `test05-host-ready-load-01.log` 和 `-02.log` 保留全部过程。

当前只证明 Hub/HID 枚举成功，输入事件、鼠标、拔插、充电/电脑 sink 转换和开机自动加载仍在逐项实测；黑名单保留，未提前启用自动加载。source_otg_ready 默认为 false，普通重启还不能据此宣称自动 Host 可用。


### 真实键盘输入、用户验收与充电切换缺陷

`test05-usb-input-01.log` 的只读 evdev 采集记录 107 次按下、107 次松开、4 次重复、167 帧，SYN_DROPPED=0；VBUS enabled/on/500000 µA。用户实际在屏幕登录并运行 top，确认键盘和 Hub 正常。随后加入 Razer DeathAdder Essential 1532:006e，三个接口与四个输入节点枚举成功。

鼠标事件采集 `test05-usb-input-mouse-01.log` 遇实际拔 Hub，read 返回 ENODEV，因此没有可用的完整鼠标计数；不能把枚举/用户操作等同于已统计的相对移动事件。用户等待期间改接充电器，再接回 Hub 后键盘仍可用；23:21 后 Agent 恢复过期 Wi-Fi SSH 并实读 Host/source、Hub、Razer、Logitech 枚举，见 `test05-working-hub-state-02.log`。日志显示 xHCI 注销后重新注册和外部设备重枚举，不只是旧节点残留。

当时 FG 电量读数仅 4%，立即卸载控制器关闭源 VBUS，接充电器，手动通过 charger 的标准 STATUS/CURRENT_MAX ABI 恢复输入，不做裸寄存器写入。输入约 0.47–0.49 A，电量读数从 4% 升到 9%，约 30.8–31.3°C。FG 状态文本依然错误：get_current() 已转成充电为正，而 fallback 状态比较仍把负值标为充电。独立补丁 `0010-pmi8998-fg-fallback-current-sign.patch` 已 checkpatch 0/0，并在独立目录编译 ARM64 对象通过；没有修改或部署已归档 test05。

进一步在充电器接入时加载 source_otg_ready=1，角色确实 device/sink、源调压器 disabled，但输入限流=0，VBUS ADC 5.08 V、输入仅约 28 mA，电池电流为负（放电）。因此 sink 充电验收失败；EXIT trap 卸载控制器并恢复 500 mA，随后实读输入约 493 mA，电量读数继续恢复。见 `test05-sink-charge-01.log`、`test05-low-battery-charge-01.log`、`test05-charge-trend-01.log`。

根因在 TCPM 的 tcpm_get_current_limit()：Rp-default 时若 tcpc->get_current_limit 缺失，返回 0。SMB2 只注册了 setter。修复草案 `0011-polaris-smb2-default-sink-current.patch` 按 BC1.2 DCP/CDP 给 500 mA、未知/未配置 SDP 给 100 mA；checkpatch 0/0，独立 ARM64 对象编译通过，尚未形成/部署新的签名内核。不能提前宣称此补丁实机修复成功。

当前保持 charger 加载、Type-C 控制器卸载、输入 500 mA、黑名单保留，以便低电量恢复。开机 Host 自动加载暂缓，待 sink 补丁完整构建并实机验证。下一阶段按用户要求安装图形界面，不为此提前刷入未验证电源修复。


## 2026-11-05 test06：充电修复、GUI 键鼠与自动启动验收完成

### 代码、构建和独立镜像

- `0010` 修正 FG fallback 电流符号；`0011` 补齐 TCPC get_current_limit，防止 Rp-default 被 TCPM 设为 0mA；`0012` 按已确认 5V/2A DCP 电源设置 DCP 请求最多1A、CDP 500mA、未知/未配置 SDP 100mA，电池快充750mA，FG power-supplies 连接 charger。OTG 源仍500mA，PD仍禁用。
- test06 与 test05 有效内核配置仅 LOCALVERSION 不同，保留 integrity lockdown、模块签名和原 LCD/Wi-Fi 修复。三个新补丁 checkpatch 0 errors / 0 warnings。独立 `build/recipe-test06`；构建日志 `logs/test06-kernel-build.log`，1156 个匹配模块。
- 19 个 initramfs 模块与 Type-C/TCPM/VBUS/charger/FG，共24个 CMS签名实际验证，证书在内核；依赖闭包、镜像/CPIO 往返及损坏拒绝检查通过。完整 dtschema 工具仍不可用，没有将 DTC 编译等同于完整 schema 验证。
- `images/boot-test-06-usb-charge.img`，29,515,776 字节，SHA-256 `e9c7591b9a044f63d3fc4036cee778217ce7fe31a9a31c3cc5205b4977c9adce`。独立只读基线 `baseline/boot-lcd-touch-wifi-usb-gui-test06-20261105.img`；GUI在根文件系统，不是全部包含于boot镜像。
- 独立匹配模块归档 SHA-256 `eac4ccbf674c6ffe88aac49d403d2492cc3fb32740dd19d17f4cae580bbdbeae`。安装到 `/usr/lib/modules/7.1.0-rc1-sdm845-polaris-test06`，所有旧版本保留。

### 部署与首次重启

沿用用户明确的自主刷机授权，并保持用户提供的5V/2A电源连接，经Wi-Fi执行受控手机本地 boot 写入，不需要换线到电脑：先核对旧test05实际boot前缀、设备树身份/64MiB boot标签设备、电量/温度、候选和匹配模块；保存完整64MiB分区到手机 root-only `/var/lib/polaris-lab/test06-20261105/boot-partition-before.bin`，再仅写独立test06，fsync及回读哈希后正常重启。没有运行APK部署钩子。见 `test06-deploy-boot-01.log`。Windows Fastboot恢复副本与脚本test06 profile已准备。

新 release/实际boot哈希、DTS输入1A/电池750mA均实读确认。Wi-Fi、图形登录、tty2文字回退、charger-only初始化自动恢复；FG正确显示Charging，原先缺charger supply警告消失。见 `test06-first-boot-01.log`。

### DCP 充电修复与测量

手动加载现有签名 Type-C 模块 `source_otg_ready=1` 后，TCPM从SNK_DISCOVERY进入SNK_READY，明确请求5000mV/1000mA。实际输入约0.79–0.80A，电池正向0.74A，温度30.0°C，source调压器始终disabled。用户外部电源显示0.8–0.82A，与内核输入电流吻合。见 `test06-sink-charge-01.log`、`test06-sink-steady-01.log`。

1A是上限，不是保证恒定输入。后续热插回DCP时，TCPM先以未知源100mA启动，charger约1.5s延迟完成BC1.2，再按其现有APSD策略将输入设为电池快充上限750mA。最终自动输入实测约0.723–0.728A、电池约0.644–0.647A，温度29°C，持续正向充电。该略低于1A的结果不是0mA回归；后续可进一步解耦DCP输入和电池快充限流，目前未做额外改动。见 `test06-final-charge-01.log`。未验证满充、不同线材/电源、长期热循环和电量计容量精度。

### Host、真实键鼠、正反插

拔充电线接Hub后自动进入Host/source，真实升压状态0xa、fault0，OTG500mA。GenesysLogic Hub、Logitech键盘和Razer鼠标均枚举；用户在新内核用硬件键盘输入锁屏密码。

30秒只读采样：Razer鼠标14次按下/14次松开、3427个相对移动/滚动事件、3006帧；Logitech键盘11次按下/11次松开、23帧；全部SYN_DROPPED=0。不记录键码/输入内容，不独占或注入输入。见 `test06-hub-gui-state-01.log`、`test06-usb-input-01.log`。

用户将手机端插头翻转180°后确认“一切正常”。只读TCPM记录CC1/Rd、polarity0切到CC2/Rd、polarity1，两次都SRC_READY；USB实际断开并重新枚举全部键鼠。随后再接DCP，自动回device/sink、源VBUSoff并恢复充电。见 `test06-reverse-cc-01.log`、`test06-final-charge-01.log`。

### 开机自动角色与第二次重启

`polaris-usb-role-test06.service` 仅在test06启用，明确依赖charger初始化，先加载VBUS provider，再以source_otg_ready=1加载Type-C；在greetd之前启动。udev/initramfs黑名单仍保留，供电模块由受审查服务明确加载。ExecStop使用rmmod只卸载Type-C，避免modprobe -r连带移除charger/FG供应者。

保持Hub/键鼠接入再正常重启，新的boot-id和service InvocationID已核验，不是旧会话。约9.35s注册Type-C，10.82s升压ready，12.48s以内键鼠全部枚举；Wi-Fi SSH和GUI自动恢复，无需手动modprobe。见 `test06-role-service-install-01.log`、`test06-reboot-host-01.log`、`test06-autostart-hub-01.log`。

当前手机已换回用户5V/2A电源并持续Charging，最后电量约31%；角色服务、GUI、Wi-Fi自动连接和tty2均enabled。USB PC/NCM在动态角色切换后的重新绑定、重负载外设、带PD供电Hub、休眠唤醒、长时间充电仍待后续验证。没有宣称USB3物理速率或USB PD可用。
