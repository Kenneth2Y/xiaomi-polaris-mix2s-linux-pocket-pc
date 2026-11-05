# DSI 与构建审计

## 已定位的构建故障

`pmbootstrap/pmb/build/backend.py` 的 --src 路径把源码 `.gitignore` 直接传给 rsync 的 `--exclude-from`。Linux 的规则包含 `*.bc` 和例外 `!kernel/time/timeconst.bc`，但两套规则语义不同。

最小只读 dry-run 已得到 `hiding file timeconst.bc`，保存在 `logs/rsync-exclude-probe.log`。这解释了原目录与 source-override 有文件、local-source-copy 缺文件的现象。没有删除源码中的 timeconst.bc，也不需伪造该文件。

本阶段绕开 --src，保留原来的 libbpf 和 dynamic-ftrace 补丁，使用标准源码包 + 独立补丁流程。原始 pmaports 工作区及交接时源码未覆盖；实验 recipe 在 `build/recipe/`。

最初 GCC 缺失发生在带 CC/CROSS_COMPILE 环境的 pmbootstrap cross-native 构建中。当前清洁 LLVM 环境已经越过此处；还没有把原始每个失败的具体子命令都复现，因此不声称所有 pmbootstrap cross-native 环境问题均已修复。

## DSI 证据与风险

- 本地 SDM845 DISPCC 的 pclk0/pclk1 源时钟有 `CLK_OPS_PARENT_ENABLE`。
- SDM845 DTS 中 DSI host 有 assigned clocks/parents。
- 正常显示 enable 路径先使能 PHY，再启动 host；但 probe 阶段的 CCF reparent 可能更早准备 PLL。
- 10nm 正常 PHY enable 明确设置 CTRL_0 的 bit 6 和 bit 5；原 PLL bias 只控制 bit 5。
- 完整实机 dmesg 已采集：0.453715 秒 PLL lock failed；随后调用栈为 `dsi_phy_driver_probe → devm_of_clk_add_hw_provider → of_clk_add_hw_provider → clk_core_reparent_orphans → __clk_set_parent_after`。
- 因而本机已证实的触发点是 provider 注册时的 orphan clock reparent，不能照抄邮件中其他平台的 `of_clk_set_defaults` 调用链。仍缺 CTRL_0、VCO rate 的现场观测。
- 1.118498 秒面板报 DCS 初始化 -22；0.691191 秒及 2.505286 秒 GPU 报请求的 zap 固件不存在。不能把所有错误合并成一个已证实根因。

上游邮件线程既包含 10nm 的改善报告，也包含 2026-10-01 作者报告的 SM8350 HDK 回归。它不足以证明两行改动可安全广泛移植，更不等于 MIX 2S LCD 已修复。

原始邮件及完整讨论：

- https://lore.kernel.org/all/20260924-dsi-7nm-pll-digtop-v1-1-c2b24c8e218d@oss.qualcomm.com/
- 可读取的原始邮件镜像：https://lore.landau.one/lkml/hqdsikuu7tgbkchteduzgno3pvzvhxahdrv52qy2v35qj3w7ms@qhsy2cot4uuy/T/
- LLVM 构建文档：https://docs.kernel.org/kbuild/llvm.html

## test01 的选择

`0002-10nm-pll-diagnostics.patch` 只增加日志：PLL bias 前后 CTRL_0、VCO 频率、lock 返回码、正常 PHY enable 入口。不修改寄存器写入、延迟或错误返回。

全量构建完成后进一步审计发现面板独立问题：nt35596s_panel_prepare 发送 DSI 命令，但驱动未设置 prepare_prev_first，默认 bridge 顺序先调用面板，MSM dsi_host_transfer 在 power_on=false 时直接返回 -EINVAL。这可以解释 DCS -22；后来的 clk_summary 报 DSI VCO 有引用，并不能消除该时序错误。

本地 pmaports 完整 Git 历史包含 Icenowy Zheng 的原始 hotfix：`8e1bb335ca403ab1cad09747e371583e09fb78ca`（2024 年，MR4867）。已原样恢复为 `0004-nt35596s-prepare-prev-first.patch`，保留作者与签署，只在 drm_panel_init 后设置一个字段。当前 test01 候选包含此修复和 PLL 诊断，仍不包含 DIGTOP 供电实验。

官方项目历史入口：https://gitlab.com/postmarketOS/pmaports/-/commit/8e1bb335ca403ab1cad09747e371583e09fb78ca

对应的通用时序语义还可对照：https://lore.gitlab.freedesktop.org/drm-ai-reviews/20260323-panel-fix-v1-1-9f12b09161e8%40oss.qualcomm.com/

`0001-experimental-10nm-digtop.patch` 保留交接的两行实验，未加入 test01。以后若测试，需独立编号，并特别覆盖 enable/disable、失败路径及重复 modeset。

诊断会增加日志并略微改变时序，仍需实机验证。只有编译通过不能宣称修复 LCD。
