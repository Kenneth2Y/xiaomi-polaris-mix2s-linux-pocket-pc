#!/bin/sh
# 在具备锁定工具链的 Linux 环境运行；不安装 APK、不接触手机。
set -eu
set +x
umask 077
work=${1:?用法：build.sh 准备好的工作目录 [并行数]}
jobs=${2:-4}
work=$(realpath "$work")
test -f "$work/prepare.json"
source=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["source_dir"])' "$work/prepare.json")
source="$work/$source"
stage="$work/stage"
test ! -e "$stage"
for tool in clang ld.lld make openssl pahole bison flex perl python3; do command -v "$tool" >/dev/null; done
export ARCH=arm64 LLVM=1
export SOURCE_DATE_EPOCH=1793750400 KBUILD_BUILD_USER=polaris KBUILD_BUILD_HOST=rebuild
# 禁止 shell 调试泄露口令。口令仅留在进程环境，私钥始终加密。
export KBUILD_SIGN_PIN=$(openssl rand -hex 32)
trap 'unset KBUILD_SIGN_PIN' EXIT
openssl req -new -x509 -newkey rsa:4096 -sha512 -days 365 \
    -passout env:KBUILD_SIGN_PIN -subj '/CN=Polaris local rebuild module signing/' \
    -keyout "$source/certs/polaris-test-signing-key.pem" \
    -out "$source/certs/polaris-test-signing-key.pem"
chmod 600 "$source/certs/polaris-test-signing-key.pem"
make -C "$source" olddefconfig
grep -qx 'CONFIG_LOCK_DOWN_KERNEL_FORCE_INTEGRITY=y' "$source/.config"
grep -qx 'CONFIG_MODULE_SIG=y' "$source/.config"
make -C "$source" -j"$jobs" Image.gz modules qcom/sdm845-xiaomi-polaris.dtb
make -C "$source" modules_install INSTALL_MOD_PATH="$stage/usr" INSTALL_MOD_STRIP=1
# Only these two installation links are disposable; never follow them into sources.
for f in "$stage"/usr/lib/modules/*/build "$stage"/usr/lib/modules/*/source; do
    test ! -L "$f" || rm "$f"
done
mkdir -p "$stage/boot/dtbs/qcom"
cp "$source/arch/arm64/boot/Image.gz" "$stage/boot/vmlinuz"
cp "$source/arch/arm64/boot/dts/qcom/sdm845-xiaomi-polaris.dtb" "$stage/boot/dtbs/qcom/"
cp "$source/include/config/kernel.release" "$work/kernel.release"
unset KBUILD_SIGN_PIN
printf '编译完成：%s\n仍未生成/刷写 Android boot，不会调用 mkinitfs 或 boot-deploy。\n' "$stage"
