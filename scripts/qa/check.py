#!/usr/bin/env python3
"""公开仓库静态检查：凭据、路径、补丁清单、配方校验和、脚本语法。"""
from __future__ import annotations
import argparse,ast,hashlib,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SECRET_PATTERNS=[
 ('私钥',re.compile(r'-----BEGIN (?:ENCRYPTED |RSA |EC |OPENSSH )?PRIVATE KEY-----')),
 ('GitHub令牌',re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})\b')),
 ('常见云访问密钥',re.compile(r'\bAKIA[A-Z0-9]{16}\b')),
 ('带认证URL',re.compile(r'https?://[^\s/:]+:[^\s/@]+@')),
 ('明文赋值',re.compile(r'(?i)\b(?:password|passwd|psk|access_token|auth_token)\s*[:=]\s*[\x22\x27][^\x22\x27\s]{4,}[\x22\x27]')),
]
FORBIDDEN_NAMES={'credential.secret','known_hosts','id_rsa','id_ed25519','.env','local.env'}

def scan_text(text):
 return [(i,kind) for i,line in enumerate(text.splitlines(),1) for kind,pat in SECRET_PATTERNS if pat.search(line)]

def files():
 # Git may not have its first commit yet. Explicit source roots only, never downloads/dist.
 for p in ROOT.rglob('*'):
  rel=p.relative_to(ROOT)
  if any(x in ('.git','.local','.private','build','work','downloads','dist','__pycache__') for x in rel.parts):continue
  if p.is_file():yield p

def check():
 errors=[];count=0
 for p in files():
  rel=p.relative_to(ROOT);count+=1
  if p.name in FORBIDDEN_NAMES or p.suffix in ('.img','.ko','.key','.pfx','.p12'):
   errors.append(f'{rel}: 禁止纳入源码库的文件类型')
  if p.is_symlink() and not p.resolve().is_relative_to(ROOT):errors.append(f'{rel}: 外部符号链接')
  try:text=p.read_text()
  except UnicodeDecodeError:
   errors.append(f'{rel}: 未登记的二进制文件');continue
  for line,kind in scan_text(text):errors.append(f'{rel}:{line}: {kind}')
  if p.suffix=='.py':
   try:ast.parse(text)
   except SyntaxError as e:errors.append(f'{rel}: Python语法错误: {e.msg}')
  if p.suffix=='.sh':
   r=subprocess.run(['bash','-n',str(p)],capture_output=True,text=True)
   if r.returncode:errors.append(f'{rel}: shell语法错误')
 # Every APKBUILD source must retain the original checksum. Config is an immutable test06 snapshot.
 recipe=ROOT/'kernel/apkbuild';body=(recipe/'APKBUILD').read_text()
 sums=body.split('sha512sums="',1)[1].rsplit('"',1)[0]
 for line in sums.splitlines():
  if not line.strip():continue
  digest,name=line.split()
  if name.startswith('linux-sdm845-'):continue
  p=recipe/name
  if not p.is_file():errors.append(f'APKBUILD缺少输入: {name}')
  elif hashlib.sha512(p.read_bytes()).hexdigest()!=digest:errors.append(f'APKBUILD输入校验失败: {name}')
 # Keep experimental DIGTOP, firmware packaging and fixed-host diagnostics outside the applied series.
 series=(ROOT/'kernel/patches/series').read_text()
 for name in ('0001-','0003-','0006-'):
  if any(x.startswith(name) for x in series.splitlines()):errors.append(f'实验补丁误入当前series: {name}')
 required=['README.md','AGENTS.md','NOTICE.md','backlog/BUGS.md','backlog/ROADMAP.md','docs/REPRODUCE.md','docs/RECOVERY.md']
 for n in required:
  if not (ROOT/n).is_file():errors.append('缺少维护文档: '+n)
 for e in errors:print(e,file=sys.stderr)
 print(json.dumps({'checked_files':count,'errors':len(errors),'secret_values_printed':False},ensure_ascii=False))
 return bool(errors)
if __name__=='__main__':raise SystemExit(check())
