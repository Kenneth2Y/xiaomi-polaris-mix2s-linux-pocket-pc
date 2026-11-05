# test01 上机记录与后续规则

2026-11-04，用户在现场明确授权：“刷机吧。全新授权：你可以自己觉得是否刷机。”此授权覆盖原计划中对本次 boot 启动/刷写的逐次确认要求；没有扩大到启动链、基带或校准分区。

## 本次执行

1. 核对唯一 Fastboot 设备为 polaris，Bootloader 已解锁，boot 分区为 0x4000000（64 MiB）。
2. 原始 boot.img 与已保留备份哈希相同；进入 Fastboot 前实际 boot 分区前缀也与原基线一致。
3. 13:52（Asia/Shanghai）临时 fastboot boot 成功；SSH 恢复，运行 test01。用户看到左上角 login，方向正确。
4. 13:56 仅执行 flash boot，将同一候选写入，Fastboot 发送/写入均返回 OKAY，随后 reboot。
5. SSH 再次恢复，uname 为 7.1.0-rc1-sdm845-polaris-test01。实际 boot 分区前 29,515,776 字节的 SHA-256 与候选一致。
6. 持久启动 dmesg 无原 DCS 初始化 -22 和 GPU zap 加载错误；早期 PLL probe warning 仍存在，正常 PHY enable 后 PLL 锁定成功。
7. 用户要求缩小字体，最终配置24x48、45行x45列。修正了 systemd 对大字体探测的兼容问题，字体服务 active；没有为字体再做额外重启。
8. 再次进行60秒触摸测试，收到了46252事件、5757帧、66次触点建立，无SYN_DROPPED，坐标覆盖接近全屏。

## 当前工作基线

- Windows：C:\polaris-lab\export\boot-test-01-lcd-candidate.img。
- 独立备份：baseline/boot-lcd-ssh-test01-20261104.img。
- SHA-256：68093f62b6aa40abfa5fdd3704d6ab33c97b31ae92993118d1f5ba51b427fd46。
- 原始 SSH-only 基线仍保留，详见 images/ROLLBACK.md。
- /boot/boot.img 仍是旧文件；实际 Android boot 分区已经是 test01。

## 后续规则

继续遵守用户已授予的自主软件开发和 boot 测试授权，不对普通步骤反复询问。每次设备启动实验仍核对镜像、product、分区和恢复条件；需要物理按键或连接硬件时明确告知用户。不要把这项授权延伸到擦除 userdata、写启动链/基带/校准分区或重锁 Bootloader。

USB Host 尚未测试，切换前必须先准备替代可达通道或现场恢复。test01 未加入 DIGTOP 供电实验。多点触摸峰值、GPU实际渲染、无线、声音及蜂窝网络仍需后续实测。
