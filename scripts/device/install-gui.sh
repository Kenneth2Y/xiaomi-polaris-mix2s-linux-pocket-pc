#!/bin/sh
# 仅在用户明确授权的 polaris / Nura systemd 手机上执行。
# 默认只输出计划；--execute 执行已审阅操作，不另存任何凭据。
set -eu
set +x
if test "${1:-}" != --execute; then
 echo '计划：先关闭 deviceinfo 自动刷写，验证后以 KERNEL_INSTALL_BYPASS=1 安装 Phosh/Phoc/Stevia/Foot。'
 echo '不会升级系统内核；请先核对 docs/DEVICE_OPERATIONS.md 和回退方法。'
 exit 0
fi
test "$(id -u)" = 0
grep -zq 'xiaomi,polaris' /sys/firmware/devicetree/base/compatible
command -v systemctl apk >/dev/null
backup=/var/lib/polaris-lab/gui-config-before
install -d -m 700 "$backup"
if test -f /etc/deviceinfo; then
 test -f "$backup/deviceinfo" || cp -p /etc/deviceinfo "$backup/deviceinfo"
fi
if ! grep -qx 'deviceinfo_flash_kernel_on_update="false"' /etc/deviceinfo 2>/dev/null; then
 printf '\ndeviceinfo_flash_kernel_on_update="false"\n' >> /etc/deviceinfo
fi
. /usr/share/misc/source_deviceinfo
test "$deviceinfo_flash_kernel_on_update" = false
export KERNEL_INSTALL_BYPASS=1
apk --preserve-env --no-interactive add --simulate phosh phosh-osk-stub stevia-schemas foot greetd-phrog mesa-utils
# 禁止隐式启动显示服务，保留已运行会话；首装后按操作文档配置tty7。
apk --preserve-env --no-interactive add phosh phosh-osk-stub stevia-schemas foot greetd-phrog mesa-utils
printf '软件已装；未自动重启。继续按 docs/DEVICE_OPERATIONS.md 核验服务、GPU与回退。\n'
