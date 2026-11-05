# Xiaomi MIX 2S 原生 Linux Pocket PC

把 Xiaomi MIX 2S（polaris / Snapdragon 845）逐步维护成可实际使用的 ARM64 Linux 掌上电脑，并保留能解释、复现、升级和迁移的工程方案。

当前公开基线：**test06 / v0.1.0-alpha.1**。这是实验性移植成果，不是功能完整的日用发行版。最后一轮实机验收日期为 **2026-11-05**；文档记录的是该轮证据，不代替对当前设备的检测。

## 已验证到哪里

| 功能 | 本机实测 | 边界 |
|---|---|---|
| LCD / 触摸 | 登录控制台、Phosh 竖屏显示与触摸正常 | 多点上限与长期稳定性待测 |
| GUI / GPU | Phosh、Phoc、Stevia、Foot；freedreno FD630，GL4.6 / GLES3.2 上下文 | 不是持续GPU压力测试 |
| Wi-Fi | 2.4GHz自动连接、无线SSH、重启恢复 | 5GHz可扫描但认证仍失败 |
| USB Host | Hub＋Logitech键盘＋Razer鼠标，正反插，带Hub重启自动恢复 | USB2数据通路；未宣称USB3或PD |
| 输入 | 30秒键盘11对、鼠标14对及3427相对事件，零丢失 | 不保存键码、输入文字或密码 |
| 充电 | DCP输入上限1A、电池750mA；实测输入约0.72–0.80A，外部表0.8–0.82A | OTG仍500mA；满充/热循环/电量精度待测 |
| 其他 | 浏览器、文件管理器、中文字体已装 | 中文输入法、音频、蜂窝、蓝牙、休眠仍待完善 |

当前启动镜像SHA-256：

```text
e9c7591b9a044f63d3fc4036cee778217ce7fe31a9a31c3cc5205b4977c9adce
```

完整事实和测试证据见 [当前状态](docs/STATUS.md)、[测试索引](docs/EVIDENCE.md)。

## 三层保存

1. **Git源码**：内核补丁、DTS快照、配置、APKBUILD、维护脚本、工程文档及脱敏测试证据。
2. **版本归档**：[Releases](https://github.com/Kenneth2Y/xiaomi-polaris-mix2s-linux-pocket-pc/releases)保存实际boot、kernel、DTB、initramfs、匹配模块、构建元数据、上游源码包和SHA256SUMS。二进制不塞进Git历史。
3. **工程知识**：故障原因、失败方案、验证层级、设备操作顺序、恢复路径和上游来源。历史脚本以文本归档，不冒充可直接运行的入口。

此外，未实现能力、零星想法和偶发bug统一进入 [backlog](backlog/README.md)，不因一次聊天就丢失，也不把“谈到”当作“已决定实施”。

## 入口

- 新Agent：[AGENTS.md](AGENTS.md)，先读再改。
- 从新克隆准备源码：[复现说明](docs/REPRODUCE.md)。
- 设备操作：[操作规范](docs/DEVICE_OPERATIONS.md)与[恢复方法](docs/RECOVERY.md)。
- 发布与版本：[版本规则](docs/VERSIONING.md)、[归档规则](docs/ARCHIVING.md)。
- 未来规划：[路线图](backlog/ROADMAP.md)、[缺陷登记](backlog/BUGS.md)、[想法](backlog/IDEAS.md)、[收件箱](backlog/INBOX.md)。
- 贡献：[CONTRIBUTING.md](CONTRIBUTING.md)与[上游贡献计划](docs/UPSTREAM.md)。

```bash
git clone https://github.com/Kenneth2Y/xiaomi-polaris-mix2s-linux-pocket-pc.git
cd xiaomi-polaris-mix2s-linux-pocket-pc
python3 scripts/qa/check.py
python3 -m unittest discover -s tests -v
```

这些检查不编译内核、不连接手机、不刷写。源码准备/构建命令另见复现说明。

## 当前保存的是什么

这是最初开发工作区的**整理导入**，没有伪造过去的Git提交或测试时间。已验证二进制在建立本仓库前构建；版本清单将其与对应上游tag、补丁、配置和导入后的源码提交关联，不能声称它早已由某个Git提交构建。

GUI安装时曾触发系统原有mkinitfs/boot-deploy钩子意外覆写boot，已恢复并回读验证，随后明确部署test06。该经验完整记录于[事故复盘](docs/incidents/2026-11-04-auto-boot-deploy.md)，维护脚本默认先关闭自动刷写，并使用已验证的bypass。

许可证与来源见 [LICENSE](LICENSE)、[NOTICE.md](NOTICE.md)。内核及第三方代码保留各自许可证；固件不会因为本仓库开源而被重新授权。密码、私钥、令牌、Wi-Fi凭据和设备私有备份不进入Git或Release。
