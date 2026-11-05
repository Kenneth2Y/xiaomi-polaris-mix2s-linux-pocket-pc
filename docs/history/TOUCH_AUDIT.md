# 触摸事件验证

2026-11-04，用户确认准备后采集 60 秒。程序实际运行于当前基线内核，ioctl 返回设备名 Synaptics S3330；ARM64 input_event 长度 24 字节。

结果：events=0，frames=0，contacts=0。之后读取 /proc/interrupts：msmgpio 125 / rmi4_i2c（Linux IRQ147）、F01（IRQ148）、F12（IRQ149）均为零。input3 inhibited=0；I2C runtime_status=unsupported，不能据此推断已休眠。

因此节点注册不能作为触摸可用证据。当前尚未判断是传感器未发 ATTN、引脚/中断配置还是 RMI 功能初始化问题。没有通过写寄存器、修改电源、重绑定、GPIO 强制操作来尝试唤醒。

随后只读 debugfs 显示 GPIO125 为输入高电平、16mA、下拉，与当前 DTS 的 default 配置一致；触摸 vdd/vio consumer 有引用，tp_vddio 为 1.8V。尚无证据把零事件简单归因于 runtime suspend，亦未据此修改引脚拉电阻。

`tools/touch-readonly.c` 使用内核 nolibc 编译静态 ARM64 程序，只打开 /dev/input/event3 的只读非阻塞句柄，并拒绝与已知设备名不一致的设备；不使用 EVIOCGRAB，不写设备，仅统计触点/坐标/丢帧。持续时间上限 60 秒。

构建/验证：`python3 -B tools/build-touch-monitor.py`；日志 `logs/touch-monitor-build.log`、`logs/touch-monitor-upload.log`、`logs/touch-events-20261104.log`、`logs/touch-state-20261104.log`。

手机唯一新增文件为 /tmp/polaris-touch-readonly-20261104（用户所有、0700），SHA-256：8118cdf955c25a43db382eef4a6d4bcaf241d8a3203e8356462dc1ea73dbad1b。未安装软件包；可在后续维护中删除，重启也可能清理 /tmp。

## test01 持久启动后的成功复测

用户明确要求再次测试。监听 READY 后告知用户开始动作，采集 60 秒：

- events=46252，frames=5757，contacts=66，dropped=0。
- X=4..1074，Y=3..2155，覆盖接近 1080x2160 的屏幕范围。
- GPIO125 / RMI F12 IRQ 总计由 578 增至 9053。
- 日志：`logs/test01-touch-retest-02.log`，及同名前缀的 irq-before/irq-after 日志。

基本触摸与坐标流现已实测通过。此前零事件窗口不足以认定硬件/IRQ 损坏；当前正证据已经排除“完全不产生中断/事件”的结论。程序没有统计同时活动 slot 的峰值，因此不能据此声称最大多点数量或所有手势均通过；这属于后续验收。
