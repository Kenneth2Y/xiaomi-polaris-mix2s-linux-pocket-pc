#!/bin/sh
# 主机、用户由未纳入Git的环境变量提供，不接受密码参数。
set -eu
host=${POLARIS_SSH_HOST:?请先设置 POLARIS_SSH_HOST}
user=${POLARIS_SSH_USER:-user}
exec ssh -o StrictHostKeyChecking=yes -o ConnectTimeout=8 "$user@$host" '
set -eu
uname -a
printf "\n设备树身份：\n"; tr "\0" "\n" < /sys/firmware/devicetree/base/compatible
printf "\nUSB角色：\n"; cat /sys/class/usb_role/*/role
printf "\n供电：\n"
for d in /sys/class/power_supply/*; do
 printf "%s\n" "${d##*/}"
 for f in usb_type online status capacity voltage_now current_now current_max temp; do
  test ! -r "$d/$f" || { printf "%s=" "$f"; cat "$d/$f"; }
 done
done
printf "\n关键服务：\n"
systemctl is-active greetd.service polaris-usb-role-test06.service polaris-charger-test05.service || true
'
