# 图形界面安装与验证

更新时间：2026-11-05，Asia/Shanghai。本阶段已完成 Phosh 图形桌面的安装和实机触摸/屏幕键盘/终端验收。用户原话：“触摸正常、屏幕能显示正常。输入密码的小键盘正常”；随后对完整屏幕键盘输入 pwd、字体及终端测试反馈“一切良好”。随后test06阶段完成两次实际重启：图形登录与Wi-Fi自动恢复，第二次同时验证Hub键鼠自动加载。

## 选择与产物

选择 Phosh/Phoc 手机界面，兼顾 1080×2160 竖屏触摸与外接键鼠。配置 DSI-1 scale=3，逻辑尺寸 360×720。系统约 5.6 GiB 内存、103 GiB 可用空间；基础 GUI 运行时实读 used 约 611 MiB、available 约 4.3 GiB，不能把这个瞬时读数视为多应用压力测试。

- Phosh 0.58（Nura systemd 版本号 99990.58.0-r0）、Phoc 0.58、Phrog 0.53 登录器。
- Stevia 0.58 完整屏幕键盘；虚拟旧包名 phosh-osk-stub 提供者为 stevia，还必须显式安装 stevia-schemas。
- Foot 1.28 图形终端、GNOME Web/Epiphany 50.6、GNOME Files/Nautilus 51.1。
- Noto CJK 中文字形、GNOME 默认壁纸、grim 截图工具。只安装中文显示字体，尚未配置中文输入法或更改系统界面语言。
- 没有使用完整 postmarketos-ui-phosh 元包，避免 USB-moded 依赖介入现有实验 USB。

官方参考：[Phosh](https://phosh.mobi/)、[Nura ARM64 Phosh 元包及依赖](https://pkgs.nura.eco/package/main/postmarketos/aarch64/postmarketos-ui-phosh)。

## GPU 与输入实测

普通 user 经 Wi-Fi SSH 执行 `timeout 20 eglinfo -B -p surfaceless`，返回 0：Mesa Project EGL 1.5；真实 freedreno/FD630；OpenGL 4.6 core/compat 和 OpenGL ES 3.2 上下文均成功。实际 Phoc/Phosh 会话、Stevia 和 Foot 进程持续工作；非 llvmpipe 软件渲染。没有做持续 GPU 性能/功耗基准。见 `logs/gui-egl-hardware-01.json`、`logs/gui-user-keyboard-terminal-01.log`。

用户以密码在手机登录，user/tty7 Wayland 会话实际建立；完整 OSK 和 Foot 后续验收通过。截图 `logs/screenshots/phosh-lockscreen-20261104.png` 为锁屏数字键盘，仅用来核对布局，不是桌面主页截图，也没有明文密码。

Stevia 首次启动缺 mobi.phosh.osk schema 而中止，独立 stevia-schemas 安装后修复。修复期间用户已从 greeter 登录为 user，因此重启旧 greetd 用户总线的首次命令失败；随后在真实 user 总线 reset-failed/start，服务 active、Foot active，保留全过程日志。

## 软件源和安装边界

原五条仓库顺序保留，只改为官方 HTTPS，镜像重命名到 mirror.nura.eco。手机 root-only `/var/lib/polaris-lab/gui-20261104` 保存 repositories/world/installed DB、精确模拟计划和最终包清单。installed DB 备份只用于审计，不能用直接覆盖数据库的方式卸载包。

用户提供局域网代理 <本地代理>，安装进程临时使用，不写全局代理或任何凭据。签名验证没有关闭。首次直连索引刷新超时，代理成功。APK3 --no-network 会屏蔽未缓存包，模拟应在正常仓库候选模式。第一次正式安装停在 TTY 交互确认，未下载/提交；核对数据库与备份相同后终止，增加 --no-interactive。实际首批安装 428 个新增包，无核心升级/删除；加 schema 与应用/字体后总计 875 包、APK installed-size 约 1797.9 MiB。

## 已处理的自动 boot-deploy 意外

首批图形包没有新增内核/mkinitfs/boot-deploy，但触发**系统原本已安装**的 postmarketos-mkinitfs APK trigger。它重新生成 /boot 文件，并按设备的 deviceinfo_flash_kernel_on_update=true 写 boot。Agent 事前仅审核新增依赖而未禁止已有 trigger，是本次执行疏漏；用户已被明确告知。

当前运行内核/Wi-Fi 未中断，没有重启。立即将已归档 test05 镜像传回，核验大小与 SHA-256、boot 标签实际块设备及 64 MiB 尺寸后，仅用 dd 恢复 boot。回读前 29,515,776 字节 SHA-256 为 `ac2d4496089a3f7658b8cbdae6b6b364ffe81855b42d4434bf3943198eb1cb95`，与原 test05 一致。其他分区和启动链未改；WSL 原始只读基线全部保留。详见 `logs/gui-restore-test05-boot-01.log`。

防复发已完成两层措施：

1. 官方支持的 `/etc/deviceinfo` 本地覆盖：`deviceinfo_flash_kernel_on_update="false"`。经与 boot-deploy 相同的 `/usr/share/misc/source_deviceinfo` 读取，实读 false。
2. 项目图形安装脚本 `KERNEL_INSTALL_BYPASS=1` + `apk --preserve-env`。已实际执行带 bypass 的 mkinitfs，确认在生成前输出 “Skipping mkinitfs”；并再次核对 boot 不变。后续 schema/应用安装后也核对正确。没有为此删除系统 trigger 或替换系统可执行文件。

`/boot/boot.img` 目前是那次自动生成的文件，SHA-256 `f74068989b9fcfeca6ac7b756285e04bb2067db34971e13222519f207c141723`；它不等于实际已恢复的 boot 分区，不应再被当作原始备份或直接刷入。见 `logs/gui-boot-guard-verify-01.log`、`logs/gui-closeout-01.log`。

## 持久配置与回退

- `/etc/phosh/phoc.ini` 和 `/etc/phrog/phoc.ini` 设置 DSI-1 scale=3。
- `/etc/systemd/system/greetd.service.d/50-polaris.conf` 只选择官方 `/etc/phrog/greetd-config.toml`（tty7）。greetd/display-manager.service 已 enabled、active。
- vendor greetd 仍会冲突 tty1；依赖不能用空列表 drop-in 删除，已经去掉无效尝试，另启用 getty@tty2 作为文字回退。外接键盘 Ctrl+Alt+F2 进入文字登录，Ctrl+Alt+F7 返回 GUI。
- Wi-Fi SSH 保留。通过 SSH 停止 GUI 可执行 `sudo systemctl stop greetd`，再 `sudo chvt 2`；重新启动 `sudo systemctl start greetd`。
- 当前 test05 Type-C sink 有 0mA 缺陷，控制器保持未加载。新增 charger-only 初始化服务 polaris-charger-test05.service，500mA 上限，当前启动/状态校验通过；不能把“已 enable”当作已重启实测。USB 自动 Host 仍未启用。
- 用户 5V/2A 可显示电流电源已识别 DCP，实读约 4.80V/0.488A，电池正向充电；此前充电宝在低电流时关断，已经用户确认。下一版内核单独处理电流/自动角色，GUI 不要求卸载。
- GUI 卸载前先停止/disable greetd，模拟 `apk del phosh phosh-osk-stub stevia-schemas foot greetd-phrog mesa-utils epiphany nautilus grim font-noto-cjk gnome-backgrounds`，核对差异后执行。不要复制旧 installed DB。设备本地配置原件/不存在标记在 root-only 审计目录；保留禁止自动刷写的修复，除非有明确理由恢复。

## 后续

图形开机重启验收、GUI 下 USB 键鼠联用、休眠/唤醒/电池策略、中文输入法及音频仍待后续阶段。test06 已完成构建、部署和实机充电/USB自动角色/重启/正反插验收，见 USB_HOST_AUDIT.md。当前实际 boot 为 test06，test05/test02/原始基线保留。


## test06 后续验收更新

2026-11-05 已实际运行7.1.0-rc1-sdm845-polaris-test06，boot SHA-256为e9c7591b9a044f63d3fc4036cee778217ce7fe31a9a31c3cc5205b4977c9adce。首次重启验证图形登录自动恢复；启用USB角色服务后，保持Hub接入再次重启，GUI、Wi-Fi、键盘和鼠标全部自动恢复。用户以硬件键盘解锁，并确认正反插后正常。

电源策略缺陷已在test06修复：DCP请求上限1A、电池快充750mA，OTG500mA，未知/未配置SDP100mA、CDP500mA；不支持PD。实测输入0.72–0.80A，外部电源0.8–0.82A与首次1A请求后的ADC读数吻合。FG状态符号与charger引用已修复。普通热插回DCP时APSD现有策略会选750mA输入，因此1A是上限而非固定值。

charger-only服务历史名称仍为polaris-charger-test05.service，现在内核条件显式允许test05或test06，初始化500mA；test06专属polaris-usb-role-test06.service随后管理实际角色和电流。两者加greetd、Wi-Fi timer、tty2均已enabled并实际重启验证。角色服务停止时只rmmod控制器，不递归移除charger。当前GUI阶段后续事项为中文输入法、休眠/唤醒/长期功耗及其他设备功能；核心GUI安装和基础验收完成。
