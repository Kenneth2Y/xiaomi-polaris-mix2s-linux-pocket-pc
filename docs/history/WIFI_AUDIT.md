# Wi-Fi 恢复与替代 SSH 链路

2026-11-04，Asia/Shanghai。用户指定优先连接 5 GHz `<5GHz热点>`，备用 2.4 GHz `<2.4GHz热点>`；无线密码由用户在自己的终端输入，禁止写入项目文件或 NetworkManager 持久凭据。

## 已确认的阻塞与修复

1. ath10k_snoc 已绑定，但没有 ieee80211 接口。modem remoteproc 的 MBA 固件请求使用 `qcom/sdm845/Xiaomi/polaris/`，现有文件位于 `qcom/sdm845/polaris/`。
2. `tools/wifi-firmware-stage-root.sh` 在手机增加 12 个相对软链接；原有 GPU 别名内容核验通过，未覆盖文件。受控重试既有 remoteproc 后 mpss running，但 ath10k 报 `host capability request rejected: 1`。没有刷写 modem 或校准分区，没有启动 ModemManager 或蜂窝数据。
3. 恢复 pmaports 历史提交 `8e1bb335ca403ab1cad09747e371583e09fb78ca` 中 Icenowy Zheng 的 polaris 补丁，存为 `patches/0005-polaris-ath10k-host-cap-skip.patch`。当前内核已支持该属性，只需给 Wi-Fi 节点增加 `qcom,snoc-host-cap-skip-quirk`。

## 构建与镜像

`tools/build-wifi-dtb-internal.sh` 只编译 DTB；`tools/assemble-wifi-test02.py` 要求反编译设备树仅有上述一行差异，保留 test01 的压缩内核和 initramfs。模块和签名不变，uname 仍为 `7.1.0-rc1-sdm845-polaris-test01`，验收必须检查实际设备树，不能仅凭 uname。

- 镜像：`images/boot-test-02-wifi.img`，29,515,776 字节。
- SHA-256：`6f01281de6087dea502462f373b67daedc0a33403cd41c451753736b25de8922`。
- DTB SHA-256：`ff6eb1abd808d17b9cb116a0bfa70df61cc2e43481627838f681abdd7bb1ed32`。
- 构建、单行差异、校验日志：`logs/test02-wifi-dtb-build.log`、`logs/test02-dtb-difference.patch`、`logs/test02-image-assembly.log`。

14:20 Fastboot 临时 boot 返回 OKAY，USB SSH 随后可用，但实际设备树没有新增属性，仍报 host capability rejected。**临时命令成功不代表新设备树已生效**；原因尚未确定。14:26 核对实际 boot 仍匹配 test01 后，按照用户已授予的自主刷机权限写入 test02，仅修改 boot 分区，14:27 reboot。实际设备树属性、boot 分区前缀哈希和扫描均已核验。

## 验收与凭据

验收顺序为实际设备树 → 无线接口 → 扫描指定 SSID → 用户交互认证 → DHCP/路由 → WSL 到无线地址的 SSH。USB 在 Wi-Fi SSH 通过前保持连接。NetworkManager 密码标志使用 not-saved，不在日志、命令行或 keyfile 中保存无线密码。

### 实测结果

- `<5GHz热点>`：5240 MHz 扫描成功，但认证帧超时，尚未进入 WPA 密码握手。不能据此认定密码错误；5 GHz 尚未修复。
- `<2.4GHz热点>`：2462 MHz、WPA2 连接成功，DHCP `<设备无线地址>/24`，网关 `192.168.11.1`。
- Wi-Fi SSH 实际两端为 WSL `192.168.11.35` 与手机 `<设备无线地址>`，分别走 eth1/wlan0；主机密钥通过 `HostKeyAlias=172.16.42.1` 与既有受信手机密钥匹配。十次 SSH 命令全部成功。
- 拔线前 40/40 ping、拔线后 30/30 ping，均 0% 丢包，平均约 74 ms。最初五次短测曾丢一包，长期稳定性和延迟仍待后续测试。
- 用户实际拔掉 USB，WSL 的 USB 接口消失、172.16.42.1 TCP22 超时，无线 SSH 仍成功。
- 用户随后主动重启并独立从 Windows 登录 Wi-Fi SSH；18:16 Agent 再次登录，确认加密凭据服务成功、无线地址相同。

### 用户授权的持久凭据

用户明确要求将凭据保存在手机。`tools/save-device-wifi-credential.sh` 让用户在自己的终端输入，`tools/wifi-save-encrypted-root.sh` 仅在手机本地处理密码：

- 密文：`/etc/credstore.encrypted/polaris-wifi-low`，root:0600，systemd-creds AES-256-GCM。
- 系统对称密钥：`/var/lib/systemd/credential.secret`，root:0400。无 TPM；密钥所在文件系统未加密，拥有 root 或完整系统盘的人可解密。不是硬件密封存储。
- `/etc/systemd/system/polaris-wifi-autoconnect.service` 通过 `LoadCredentialEncrypted=` 把凭据交给运行时内存目录；`/usr/local/libexec/polaris-wifi-autoconnect` 使用 nmcli passwd-file 连接。服务禁用 core dump 和交换。
- `/etc/systemd/system/polaris-wifi-autoconnect.timer` 开机 20 秒开始、断开后周期重试。NM 的 `psk-flags=2` 和 `connection.autoconnect=no` 保留，由加密服务负责自动连接。当前无线 MAC 固定为已使用的本地地址，以保持 DHCP 租约稳定。
- 已认证解密并检查格式；两个 NM 配置均无明文 PSK 字段。没有把密文、系统密钥或密码复制到 WSL 项目。
- `logs/wifi-persistence-post-user-reboot-01.log` 记录重启后复核；不能把之前因执行器额度而未执行的主动断线测试写成成功。

用户交互 shell：`bash <旧开发工作区>/tools/device-wifi-shell.sh`。地址记录在 `build/ssh/wifi-address`（仅公共 IP）；DHCP 改变时可传入新地址。

机制参考：[systemd-creds](https://www.freedesktop.org/software/systemd/man/latest/systemd-creds.html)、[systemd.exec credentials](https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html)、[nmcli passwd-file](https://networkmanager.dev/docs/api/latest/nmcli.html)。

## 回退

Fastboot 下运行 `python3 -B tools/fastboot-test01.py flash-test --profile test01`，再执行 `reboot --profile test01`，恢复已验证的 LCD、触摸与 USB SSH 基线。test01 和最初 SSH-only 镜像均独立保留。固件路径修复独立于 boot；如需撤销，只移除本次新增且目标仍为 `../../polaris/<原文件名>` 的 12 个链接，保留原有 a630_zap 链接和固件文件。不要停掉正在运行的 mpss。

test02 本身现已成为 LCD＋触摸＋Wi-Fi＋USB NCM 工作基线，独立只读备份为 `baseline/boot-lcd-wifi-test02-20261104.img`，哈希与上述 test02 相同。后续 USB Host 实验优先用 `flash-test --profile test02` 回退。删除持久无线凭据时先停用自建 timer，再删除该项目密文、service/timer/helper；不要删除系统 `credential.secret`，它可能被其他凭据复用。
