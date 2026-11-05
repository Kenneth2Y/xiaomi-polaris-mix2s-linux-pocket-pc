#!/usr/bin/env python3
"""离线渲染候选版本的rootfs配置，绝不写手机。"""
import argparse,re,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--release',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
if not re.fullmatch(r'[A-Za-z0-9._-]+',a.release):p.error('无效release')
if a.output.exists():p.error('输出目录已存在')
shutil.copytree(ROOT/'configs/rootfs',a.output)
for f in a.output.rglob('*'):
 if f.is_file():
  s=f.read_text()
  s=s.replace('7.1.0-rc1-sdm845-polaris-test05',a.release).replace('7.1.0-rc1-sdm845-polaris-test06',a.release)
  f.write_text(s)
print('已渲染离线配置。相同替换可能保留重复OR条件，无语义影响；部署前须审核差异并验证unit。')
