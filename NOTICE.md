# 来源与许可证说明

内核及衍生补丁按原GPL-2.0-only等声明保留，完整条款在licenses。0004/0005保留Icenowy Zheng原作者和Signed-off-by；SMB2参考代码保留Sam Day项目及其所含原作者版权声明。公开仓库新增内容不覆盖这些许可证。

USB输入统计C程序原声明MIT，适用licenses/MIT.txt。

公开Release中的内核对应源码由同版本工程方案加固定上游源码包组成。历史原始构建早于建仓，不伪造Git构建来源；输入/配置/补丁哈希及验证范围都单独记录。

启动模板包含发行版initramfs用户空间和Qualcomm/Xiaomi GPU固件。固件上游包firmware-xiaomi-polaris在pmaports标为proprietary，来源MollySophia/firmware-xiaomi-polaris、提交d88ffb2ee182d07567bf280fc4a8493f975ae977；本项目不把它改授为GPL。各发行版组件保留自己的许可证与对应源码来源，不能因复制进boot就视为项目自有代码。

相关入口：

- https://gitlab.com/sdm845-mainline/linux
- https://gitlab.com/postmarketOS/pmaports
- https://gitlab.alpinelinux.org/alpine/aports
- https://github.com/MollySophia/firmware-xiaomi-polaris
- https://github.com/samcday/qcom-pmic-typec-smb2

不发布任何设备密码、Wi-Fi PSK、访问令牌、私钥、设备加密凭据或整份rootfs。若发现历史证据不完整或授权/来源标注不清，先登记并纠正，不隐去问题。
