# 验证证据索引

所有公开记录来自2026-11-04至11-05的原实验，已脱敏，不是新设备的检测结果。

- reports/test06/test06-artifact-validation.json：镜像/CPIO往返、24个实际CMS签名、模块依赖闭包。
- test06-first-boot-01.log：运行release、实际boot哈希、充电DT、GUI/Wi-Fi启动。
- test06-sink-charge-01.log：SNK_READY、5000mV/1000mA请求、实际电池和输入电流、源输出关闭。
- test06-usb-input-01.log：键盘11对、鼠标14对/3427相对事件，全部零丢失；不含输入内容。
- test06-autostart-hub-01.log：新的boot周期和服务InvocationID、自动Host及键鼠重枚举。
- test06-reverse-cc-01.log：CC1/polarity0→CC2/polarity1、SRC_READY和重新枚举。
- test06-final-charge-01.log：从Host换回DCP自动充电，热插APSD输入750mA策略。
- gui-egl-hardware-01.json：freedreno FD630上下文；不是长期渲染基准。
- gui-restore-test05-boot-01.log、gui-boot-guard-verify-01.log：意外自动boot覆写恢复、后续防复发验证。

更早的故障、失败方案与出处保留在docs/history。公开日志只保留有证明力的内容；原始私有日志不作为公开附件上传。
