#!/usr/bin/env python3
"""离线用匹配的内核/DTB/签名模块更新已验证模板，不接触设备。"""
from __future__ import annotations
import argparse,hashlib,json,shutil,struct,subprocess,tempfile,zlib
from pathlib import Path
from compression import zstd
from bootimg import BootImage,add_with_parents,module_names,read_cpio,write_cpio,self_check
TEMPLATE_SHA='e9c7591b9a044f63d3fc4036cee778217ce7fe31a9a31c3cc5205b4977c9adce'
MAGIC=b'~Module signature appended~\n'

def verify_signature(data,release,cert,tmp):
    raw=zstd.decompress(data)
    if b'vermagic='+release.encode()+b' ' not in raw or not raw.endswith(MAGIC):
        raise ValueError('模块签名或vermagic不匹配')
    desc=raw[-len(MAGIC)-12:-len(MAGIC)]
    if desc[2]!=2 or desc[3:8]!=b'\0'*5: raise ValueError('不支持的模块签名格式')
    size=struct.unpack_from('>I',desc,8)[0];boundary=len(raw)-len(MAGIC)-12
    if not 0<size<boundary:raise ValueError('模块签名长度错误')
    (tmp/'module').write_bytes(raw[:boundary-size]);(tmp/'signature').write_bytes(raw[boundary-size:boundary])
    subprocess.run(['openssl','cms','-verify','-binary','-inform','DER','-in',str(tmp/'signature'),'-content',str(tmp/'module'),'-certfile',str(cert),'-noverify','-out','/dev/null'],check=True,capture_output=True)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('template','stage','source','output'):p.add_argument('--'+n,required=True,type=Path)
    p.add_argument('--template-sha256',default=TEMPLATE_SHA)
    a=p.parse_args()
    if a.output.exists():p.error('拒绝覆盖已有镜像')
    template=a.template.read_bytes()
    if hashlib.sha256(template).hexdigest()!=a.template_sha256:raise SystemExit('模板哈希不匹配')
    release=(a.source/'include/config/kernel.release').read_text().strip()
    root=a.stage.resolve();modules=root/'usr/lib/modules'/release
    if not modules.is_dir():raise SystemExit('缺少匹配模块目录')
    subprocess.run(['depmod','-b',str(root),'-m','/usr/lib/modules',release],check=True)
    image=BootImage.parse(template);entries=read_cpio(zstd.decompress(image.ramdisk))
    old=module_names(entries);releases={n.split('/modules/',1)[1].split('/',1)[0] for n in old}
    if len(releases)!=1:raise SystemExit('模板含多个模块版本')
    previous=releases.pop();oldprefix='usr/lib/modules/'+previous
    selected={n.split('/modules/',1)[1].split('/',1)[1] for n in old}
    deps={}
    for line in (modules/'modules.dep').read_text().splitlines():
        name,rest=line.split(':',1);deps[name]=rest.split()
    pending=list(selected)
    while pending:
        name=pending.pop()
        if name not in deps:raise SystemExit('缺少模板所需模块：'+name)
        for d in deps[name]:
            if d not in selected:selected.add(d);pending.append(d)
    # Remove old directories too: do not leave a stale release in initramfs.
    entries=[e for e in entries if e.name!=oldprefix and not e.name.startswith(oldprefix+'/')]
    for n in sorted(selected):add_with_parents(entries,'usr/lib/modules/'+release+'/'+n,(modules/n).read_bytes())
    # Generate a minimal depmod tree; never follow build/source links or copy private keys.
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);target=tmp/'usr/lib/modules'/release;target.mkdir(parents=True)
        for n in selected:
            f=target/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((modules/n).read_bytes())
        for n in ('modules.builtin','modules.builtin.modinfo'):
            if (modules/n).exists():shutil.copyfile(modules/n,target/n)
        order=[n for n in (modules/'modules.order').read_text().splitlines() if n in selected or n+'.zst' in selected]
        (target/'modules.order').write_text('\n'.join(order)+'\n')
        subprocess.run(['depmod','-b',str(tmp),'-m','/usr/lib/modules',release],check=True)
        for f in sorted(target.iterdir()):
            if f.is_file():add_with_parents(entries,'usr/lib/modules/'+release+'/'+f.name,f.read_bytes())
        kernel=(root/'boot/vmlinuz').read_bytes();dtb=(root/'boot/dtbs/qcom/sdm845-xiaomi-polaris.dtb').read_bytes()
        uncompressed=zlib.decompress(kernel,16+zlib.MAX_WBITS)
        certder=(a.source/'certs/signing_key.x509').read_bytes()
        if release.encode() not in uncompressed or certder not in uncompressed:raise SystemExit('内核版本或内嵌证书不匹配')
        if dtb[:4]!=b'\xd0\x0d\xfe\xed' or b'xiaomi,polaris\0' not in dtb:raise SystemExit('设备树不是polaris')
        cert=tmp/'cert.pem';subprocess.run(['openssl','x509','-inform','DER','-in',str(a.source/'certs/signing_key.x509'),'-out',str(cert)],check=True)
        critical=['kernel/drivers/usb/typec/polaris-smb2/qcom_pmic_typec_smb2.ko.zst','kernel/drivers/usb/typec/tcpm/tcpm.ko.zst','kernel/drivers/regulator/qcom_usb_vbus-regulator.ko.zst','kernel/drivers/power/supply/qcom_smbx.ko.zst','kernel/drivers/power/supply/pmi8998_fg.ko.zst']
        names=sorted(selected|set(critical))
        for n in names:verify_signature((modules/n).read_bytes(),release,cert,tmp)
    image.kernel=kernel+dtb;image.ramdisk=zstd.compress(write_cpio(entries),level=9)
    result=image.encode()
    if len(result)>67108864:raise SystemExit('镜像超过已验证的64MiB boot分区')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('xb') as f:f.write(result)
    report={'release':release,'template_sha256':a.template_sha256,'image_sha256':hashlib.sha256(result).hexdigest(),'bytes':len(result),'signature_modules_verified':len(names),'roundtrip':self_check(a.output),'device_test':'not-performed'}
    a.output.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
