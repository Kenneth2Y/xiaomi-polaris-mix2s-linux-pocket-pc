# 从新克隆开始复现

目标分开三层：准备相同源码方案、构建匹配内核/模块、验证后生成候选boot。**没有任何步骤自动刷写手机。** 原始已验证二进制应先下载并核对SHA256SUMS，以便独立回退。

## 锁定输入

kernel/config/test06.config是历史配方seed，test06.effective.config是经olddefconfig后的有效配置；工具探测字段不同属预期。

kernel/sources.lock.json记录上游tag、源码包SHA-512、pmbootstrap/pmaports提交、工具版本和配置。kernel/patches/series是唯一应用顺序；0001 DIGTOP、0003固件包实验、0006固定Host诊断不在当前序列。

历史构建使用Alpine native环境中的Clang/LLD23.1.4、Make4.4.1、pmbootstrap3.12.1；宿主Python3.14、OpenSSL与支持zstd的kmod。其他必要依赖包括bison、flex、pahole、ELF/OpenSSL开发库、perl与内核构建基本工具。使用Linux/WSL2与独立工作目录。

仓库锁定了输入和工具版本要求，**还没有发布完全封装、长期固定的工具链容器**。源码准备和镜像工具会在本次导入做独立检查；完整内核构建证据来自test06实测环境。不能把CI静态检查当作在所有新主机上全量编译已通过。工具链容器化是backlog中的明确事项。

## 准备源码

Python3.14满足所有脚本需求。下载Release中的上游源码包，或让prepare.py从锁定URL下载；两种方式都验证SHA-512，不依赖可变分支。

```bash
python3 scripts/build/prepare.py \
  --archive downloads/linux-sdm845-7.1-rc1-r0.tar.gz \
  --work-dir work/candidate-001 \
  --localversion=-sdm845-polaris-candidate-001
```

已有work目录会被拒绝。归档必须保留kernel/time/timeconst.bc：早期pmbootstrap --src/rsync忽略规则曾把它漏掉。不要用不完整源码副本来“修”这个编译错误。

## 构建并保留完整性保护

在具备上述工具链的Linux构建环境内：

```bash
sh scripts/build/build.sh work/candidate-001 4
```

生成内核、DTB和匹配的签名模块至work/candidate-001/stage。脚本生成加密RSA私钥，随机口令仅在进程环境，结束即丢弃；不会产出明文私钥，也不将私钥放入发布包。保留lockdown。

新证书和构建细节意味着**不承诺逐字节复现旧boot哈希**。每次新候选使用独立release和模块目录，记录新的证书与SHA256，不把新模块塞进历史test06目录。

## 离线生成启动镜像

先从已验证Release取得boot-polaris-test06.img作为v0布局和initramfs用户空间模板。它不是读者的新手机rootfs镜像。模板已经过凭据路径检查；新候选仍须独立检查。

```bash
python3 scripts/image/inspect-boot.py downloads/boot-polaris-test06.img
python3 scripts/image/assemble.py \
  --template downloads/boot-polaris-test06.img \
  --stage work/candidate-001/stage \
  --source work/candidate-001/linux-sdm845-7.1-rc1-r0 \
  --output dist/boot-candidate-001.img
```

assemble需要Python3.14 compression.zstd、OpenSSL和宿主kmod/depmod。它校验模板哈希、内核版本/证书、DTB身份、initramfs模块依赖与关键模块CMS签名，做镜像/CPIO往返和64MiB尺寸约束。输出JSON仍标为not-performed，不能自动升级成实机通过。

离线生成rootfs配置：

```bash
python3 scripts/device/render-config.py \
  --release 7.1.0-rc1-sdm845-polaris-candidate-001 \
  --output dist/rootfs-candidate-001
```

先审核差异，再按DEVICE_OPERATIONS和RECOVERY执行有授权的部署。完整系统安装、固件来源和对应许可证仍需单独核对；本项目不是一键重装整机。
