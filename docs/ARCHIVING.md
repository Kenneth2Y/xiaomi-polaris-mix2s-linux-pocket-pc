# 保存与归档规则

## Git层

只跟踪可审查的源码、配方、配置、文档、脱敏证据和校验清单。完整Linux树通过固定来源/哈希取得，不把多GB工作目录塞进仓库。应用中的补丁只有一个规范来源，APKBUILD使用目录内链接并校验输入。

历史日志仅选取有证明力的片段，删除凭据和个人网络/路径信息；完整未脱敏日志只留本地私有备份。archive文本用于追溯，scripts维护入口用于新工作。

## Release层

首个版本归档：实际boot、gzip内核、DTB、压缩initramfs、1156个匹配模块、构建元数据/配置/公开证书、固定上游源码包、公开方案快照与SHA256SUMS。完整对应内核源码由固定上游包加同版本仓库的全部补丁/配置共同构成，不仅留一个易漂移的分支链接。

二进制先在本地校验，再上传draft；按GitHub返回的SHA256 digest或公开下载回读验证，齐全后再发布。上传可断点到“文件级”重试；同名不同内容必须拒绝，不覆盖已验证版本。

发布包禁止私钥（即使加密）、密码/令牌、设备加密凭据、credential.secret、PSK配置、known_hosts、完整rootfs和任意用户数据。公开证书允许。镜像检查要展开initramfs核对路径和内容，不只看后缀。

首个历史基线的整理入口如下，路径由操作者填写，输出目录必须尚不存在。prepare.py校验固定历史boot、上游源码和匹配模块哈希，检查initramfs与模块归档范围；源码快照取自明确Git提交，元数据只从该公开快照与公开证书白名单生成。

```sh
python3 scripts/release/prepare.py \
  --boot /path/to/verified-boot.img \
  --artifacts /path/to/test06-artifacts \
  --upstream /path/to/linux-sdm845-7.1-rc1-r0.tar.gz \
  --source-commit COMMIT_SHA \
  --output .local/release-assets/v0.1.0-alpha.1
```

将输出的release-manifest.json登记到releases/v0.1.0-alpha.1.json，提交并建立tag后，使用最终提交发布。publish.py默认只做本地校验；明确添加--execute才上传，凭据来自系统Git安全凭据管理器或当前进程环境，禁止写入文件。发布器核验目标仓库权限、所有本地校验和与远端资产SHA256后才公开draft。

```sh
python3 scripts/release/publish.py \
  --assets .local/release-assets/v0.1.0-alpha.1 \
  --manifest releases/v0.1.0-alpha.1.json \
  --notes releases/v0.1.0-alpha.1.md \
  --commit FINAL_COMMIT_SHA
# 审核输出后，执行同一命令并添加 --execute。
```

prepare.py专用于首次历史test06导入；后续版本必须更新各自输入、版本和验证记录，不能只改文件名冒充新的已验证基线。

## 本地独立备份

GitHub不是唯一备份。保留只读原始boot与最近工作版本、未脱敏原始记录、设备配置和完整分区备份；秘密类数据只在受保护的本地备份，不与公开Release混放。建议另存外部磁盘并定期对照校验和。

## 验证层级

静态检查→源码准备→编译→签名/镜像离线校验→实际启动→外设实测→重启/拔插→长期稳定性。每条报告写明层级。CI绿色不等于手机测试完成，屏幕图标不等于音频/蓝牙/蜂窝工作。
