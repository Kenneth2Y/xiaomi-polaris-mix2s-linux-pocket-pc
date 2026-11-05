#!/usr/bin/env python3
"""离线检查启动镜像布局、组件哈希与隐私相关路径，不读取设备。"""
import argparse, hashlib, json
from pathlib import Path
from compression import zstd
from bootimg import BootImage, read_cpio, self_check

def inspect(path):
    raw=path.read_bytes(); image=BootImage.parse(raw)
    kernel,dtb=image.kernel_and_dtb(); entries=read_cpio(zstd.decompress(image.ramdisk))
    private=[]
    for e in entries:
        n=e.name.lower()
        if any(x in n for x in ('shadow','ssh_host_','id_rsa','id_ed25519','credstore','credential.secret','system-connections','random-seed')):
            private.append(e.name)
        if b'PRIVATE KEY-----' in e.data: private.append(e.name+':private-key-marker')
    return {'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'kernel_sha256':hashlib.sha256(kernel).hexdigest(),'dtb_sha256':hashlib.sha256(dtb).hexdigest(),'initramfs_sha256':hashlib.sha256(image.ramdisk).hexdigest(),'entries':len(entries),'sensitive_path_findings':private,'roundtrip':self_check(path)}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('image',type=Path);a=p.parse_args()
    r=inspect(a.image);print(json.dumps(r,ensure_ascii=False,indent=2))
    raise SystemExit(bool(r['sensitive_path_findings']))
