#!/usr/bin/env python3
"""从固定输入准备独立源码；不编译、不接触设备。"""
from __future__ import annotations
import argparse, hashlib, json, os, re, subprocess, tarfile, urllib.request
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive', type=Path, help='已有上游源码包；省略则下载并校验')
    p.add_argument('--work-dir', type=Path, required=True)
    p.add_argument('--localversion', required=True, help='新构建独立后缀，必须以 - 开头')
    a = p.parse_args()
    if not re.fullmatch(r'-[A-Za-z0-9._-]+', a.localversion):
        p.error('LOCALVERSION 只能包含字母、数字、点、下划线和连字符')
    work = a.work_dir.resolve()
    if work.exists():
        p.error('拒绝覆盖已有工作目录；为每个候选使用新目录')
    lock = json.loads((ROOT/'kernel/sources.lock.json').read_text())
    up = lock['upstream']
    archive = a.archive.resolve() if a.archive else ROOT/'downloads'/up['archive']
    if not archive.exists():
        archive.parent.mkdir(parents=True, exist_ok=True)
        temp = archive.with_suffix(archive.suffix+'.partial')
        try:
            with urllib.request.urlopen(up['url'], timeout=120) as r, temp.open('xb') as f:
                while chunk := r.read(1024*1024):
                    f.write(chunk)
            temp.replace(archive)
        finally:
            temp.unlink(missing_ok=True)
    h = hashlib.sha512()
    with archive.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''): h.update(chunk)
    if h.hexdigest() != up['sha512']:
        raise SystemExit('上游源码 SHA-512 不匹配，未解包')
    work.mkdir(parents=True)
    with tarfile.open(archive) as t:
        t.extractall(work, filter='data')
    dirs = [x for x in work.iterdir() if x.is_dir()]
    if len(dirs) != 1: raise SystemExit('源码包顶层目录异常')
    source = dirs[0]
    series = ROOT/lock['patch_series']
    applied = []
    for line in series.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#'): continue
        patch = (series.parent/line).resolve()
        if not patch.is_relative_to(ROOT/'kernel'): raise SystemExit('补丁越过 kernel 目录')
        subprocess.run(['patch','-p1','--batch','--forward','-i',str(patch)],cwd=source,check=True)
        applied.append({'path':str(patch.relative_to(ROOT)), 'sha256':hashlib.sha256(patch.read_bytes()).hexdigest()})
    config = (ROOT/lock['config']).read_text()
    config, count = re.subn(r'^CONFIG_LOCALVERSION=".*"$', f'CONFIG_LOCALVERSION="{a.localversion}"',config,flags=re.M)
    assert count == 1
    (source/'.config').write_text(config)
    assert (source/'kernel/time/timeconst.bc').is_file(), '源码不完整；禁止经忽略规则裁剪 tar 包'
    manifest={'upstream_sha512':up['sha512'],'source_dir':source.name,'localversion':a.localversion,'patches':applied,'config_sha256':hashlib.sha256(config.encode()).hexdigest(),'phase':'prepared-not-built'}
    (work/'prepare.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(f'准备完成：{source}\n未编译、未部署，新的 LOCALVERSION={a.localversion}')

if __name__ == '__main__': main()
