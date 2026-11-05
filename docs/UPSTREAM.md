# 上游来源与贡献路线

- 内核基底：sdm845-mainline/linux，tag与源码哈希见kernel/sources.lock.json。
- 显示与ath10k兼容补丁来自Icenowy Zheng，保留原From/Signed-off-by；pmaports历史提交8e1bb335ca403ab1cad09747e371583e09fb78ca。
- SMB2参考：Sam Day项目qcom-pmic-typec-smb2，固定4164801fa70216a8687cdfdc57026df740926a14。参考项目当时声明只做静态/构建验证，本机实测另行记录，不把本机结论反向包装成原作者保证。
- 原厂OTG寄存器与1-in-8顺序：MiCode/Xiaomi_Kernel_OpenSource polaris-o-oss的smb-lib.c/smb-reg.h；见公开的历史审计。
- 用户提供的nixalpha/android_device_xiaomi_mi845-mainline已参考；没有把Android分区布局或boot header设置盲目导入。

建议候选拆分：FG符号修复→默认电流回调→PMI8998专用regulator身份/状态→SMB2后端与绑定→板级DTS。先消除只针对本机实验的策略、补足schema和其他设备回归，再按对应上游规范提案。

公开仓库不等于上游接受；目前没有替用户提交上游PR、邮件或与维护者联系。成熟后再以明确的贡献范围进行沟通。
