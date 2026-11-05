# 最后已验证状态

基线test06，验收日期2026-11-05。不是对读者当前设备的远程检测。

2026-11-05 后续对原开发机设置了 Phosh 不因空闲而黑屏、锁屏、调暗或自动挂起，具体回读结果、限制和回退见 [操作记录](codex-operation-records/2026-11-05-17-36-45-phosh-idle.md)。这是该设备用户配置，不是 Release 镜像或新装系统的默认值。

- Nura edge / systemd，ARM64，Linux 7.1.0-rc1-sdm845-polaris-test06。
- LCD、触摸、Phosh图形界面、Stevia字母键盘、Foot输入用户验收通过。
- Mesa26.2.6真实freedreno FD630，上下文EGL1.5、GL4.6、GLES3.2成功；未做长时间性能测试。
- 2.4GHz Wi-Fi和无线SSH拔USB、重复重启恢复通过；凭据只在设备本地加密，公开归档没有凭据。
- USB2 Host：Hub、Logitech键盘、Razer鼠标联用；CC1/CC2正反插；保持Hub接入重启自动恢复。
- 充电：DCP上限1A、电池750mA、源OTG500mA；输入约0.72–0.80A，独立电源显示0.8–0.82A。普通热插后APSD可选750mA输入，属于已知策略。
- GUI与角色服务已enabled并实际重启验证。tty2文字控制台回退保留。
- 中文字体、GNOME Web、GNOME Files已装并启动验证；不等于中文输入法和全部应用功能完成。

实际boot SHA-256：e9c7591b9a044f63d3fc4036cee778217ce7fe31a9a31c3cc5205b4977c9adce。

rootfs配置保留历史服务名polaris-charger-test05.service，但其条件明确允许test05/06；角色服务polaris-usb-role-test06.service只允许test06。新内核用render-config.py离线生成配置并审阅，不能以旧unit未运行误判驱动失效。

未验证/未完成：5GHz连接、音频回放录音、蜂窝注册/数据/通话、蓝牙、中文输入法、休眠唤醒、满充和长期功耗、USB PC/NCM动态重新绑定、带PD/大负载Hub。见backlog/BUGS.md和ROADMAP.md。
