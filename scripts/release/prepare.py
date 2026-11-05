#!/usr/bin/env python3
"""离线整理首个历史基线的公开资产；不读取设备或复制整份实验目录。"""
from __future__ import annotations
import argparse, hashlib, io, json, shutil, subprocess, sys, tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'scripts/image'))
sys.path.insert(0, str(ROOT/'scripts/qa'))
from bootimg import BootImage, read_cpio
from check import scan_text
from compression import zstd

def digest(path, algorithm='sha256'):
    h = hashlib.new(algorithm)
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''): h.update(block)
    return h.hexdigest()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    for n in ('boot','artifacts','upstream','output'):
        p.add_argument('--'+n, type=Path, required=True)
    p.add_argument('--source-commit', required=True)
    a = p.parse_args()
    commit = subprocess.check_output(['git','rev-parse',a.source_commit+'^{commit}'],cwd=ROOT,text=True).strip()
    lock = json.loads((ROOT/'kernel/sources.lock.json').read_text())
    if digest(a.upstream,'sha512') != lock['upstream']['sha512']:
        raise SystemExit('上游包校验失败')
    expected = 'e9c7591b9a044f63d3fc4036cee778217ce7fe31a9a31c3cc5205b4977c9adce'
    if digest(a.boot) != expected: raise SystemExit('只接受已验证的历史test06镜像')
    boot = BootImage.parse(a.boot.read_bytes())
    entries = read_cpio(zstd.decompress(boot.ramdisk))
    forbidden = ('shadow','ssh_host_','id_rsa','id_ed25519','credstore','credential.secret','system-connections','known_hosts','random-seed')
    for e in entries:
        if any(x in e.name.lower() for x in forbidden) or b'PRIVATE KEY-----' in e.data:
            raise SystemExit('initramfs含不应公开的路径或私钥标记；未输出内容')
        if not e.name.endswith(('.zst','.fw','.bin','.mdt','.b00','.b01','.b02')):
            try: text = e.data.decode('utf-8')
            except UnicodeDecodeError: continue
            if scan_text(text): raise SystemExit('initramfs文本凭据扫描失败；未输出内容')
    release = lock['historical_kernel_release']
    module_archive = a.artifacts/'test06-modules.tar'
    if digest(module_archive) != 'eac4ccbf674c6ffe88aac49d403d2492cc3fb32740dd19d17f4cae580bbdbeae':
        raise SystemExit('历史匹配模块包校验失败')
    modules = 0
    with tarfile.open(module_archive) as t:
        for m in t:
            n = Path(m.name)
            if n.is_absolute() or '..' in n.parts or not m.name.startswith('usr/lib/modules/'+release):
                raise SystemExit('模块归档越过允许的版本目录')
            if m.issym() or m.islnk(): raise SystemExit('模块归档不允许链接')
            if m.isfile():
                if not (m.name.endswith('.ko.zst') or n.name.startswith('modules.')):
                    raise SystemExit('模块归档含非模块/元数据文件')
                modules += m.name.endswith('.ko.zst')
    if modules != 1156: raise SystemExit('模块数量不符')
    a.output.mkdir(parents=True,exist_ok=False)
    copies = {
        'boot-polaris-test06.img':a.boot,
        'vmlinuz-polaris-test06.gz':a.artifacts/'vmlinuz',
        'sdm845-xiaomi-polaris-test06.dtb':a.artifacts/'sdm845-xiaomi-polaris.dtb',
        'modules-polaris-test06.tar':module_archive,
        lock['upstream']['archive']:a.upstream,
    }
    kernel,dtb = boot.kernel_and_dtb()
    if kernel != copies['vmlinuz-polaris-test06.gz'].read_bytes() or dtb != copies['sdm845-xiaomi-polaris-test06.dtb'].read_bytes():
        raise SystemExit('镜像与独立组件不一致')
    for name,source in copies.items(): shutil.copyfile(source,a.output/name)
    (a.output/'initramfs-polaris-test06.cpio.zst').write_bytes(boot.ramdisk)
    source_name = 'polaris-source-v0.1.0-alpha.1.tar.gz'
    subprocess.run(['git','archive','--format=tar.gz','--prefix=polaris-source/','--output='+str((a.output/source_name).resolve()),commit],cwd=ROOT,check=True)
    # 元数据来自已提交的公开源码快照，而非可能混有秘密的历史目录。
    with tarfile.open(a.output/source_name) as src, tarfile.open(a.output/'polaris-test06-build-metadata.tar.gz','w:gz') as target:
        for member in src:
            rel=Path(member.name).parts[1:]
            if rel and rel[0] in ('kernel','configs','reports','docs','licenses','LICENSE','NOTICE.md'):
                target.addfile(member,src.extractfile(member) if member.isfile() else None)
        for name in ('Module.symvers','module-signing-cert.der','module-signing-cert.pem'):
            data=(a.artifacts/name).read_bytes()
            if b'PRIVATE KEY-----' in data: raise SystemExit('公开证书中出现私钥')
            info=tarfile.TarInfo('polaris-source/public-build/'+name)
            info.size=len(data); info.mode=0o644; info.mtime=lock['source_date_epoch']
            target.addfile(info,io.BytesIO(data))
    assets=[{'name':f.name,'bytes':f.stat().st_size,'sha256':digest(f)} for f in sorted(a.output.iterdir())]
    manifest={
        'schema':1,'repository':'Kenneth2Y/xiaomi-polaris-mix2s-linux-pocket-pc',
        'tag':'v0.1.0-alpha.1','historical_test':'test06','kernel_release':release,
        'historical_build_git_commit':None,'imported_source_commit':commit,
        'provenance_note':'历史二进制早于建仓；源码导入提交标识对应方案，不冒充当时构建提交。',
        'upstream':lock['upstream'],'modules':modules,'assets':assets,
        'validation':{'historical_device_tests':'reports/test06/','fresh_source_and_dtb':'reports/test06/public-reproduction-check.json','full_kernel_rebuild_on_import':False,'boot_privacy_scan':'passed'},
        'scope':'boot及匹配模块；不含完整rootfs、设备私有备份或私钥',
    }
    (a.output/'release-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    checks=''.join(digest(f)+'  '+f.name+'\n' for f in sorted(a.output.iterdir()))
    (a.output/'SHA256SUMS').write_text(checks)
    print(json.dumps({'assets':len(assets)+2,'modules':modules,'imported_source_commit':commit,'phase':'prepared-not-published'},ensure_ascii=False))

if __name__=='__main__': main()
