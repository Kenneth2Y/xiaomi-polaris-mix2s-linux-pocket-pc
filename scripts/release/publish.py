#!/usr/bin/env python3
"""验证本地资产，使用系统Git凭据发布draft Release；绝不打印/存储令牌。"""
from __future__ import annotations
import argparse,hashlib,json,os,subprocess,time,urllib.error,urllib.parse,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
REPO='Kenneth2Y/xiaomi-polaris-mix2s-linux-pocket-pc'
API='https://api.github.com/repos/'+REPO

def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()

def get_credential():
 token=os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
 if token:return token
 env=os.environ.copy();env.update(GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='never')
 p=subprocess.run(['git','credential','fill'],input='protocol=https\nhost=github.com\npath='+REPO+'.git\n\n',text=True,capture_output=True,cwd=ROOT,env=env,timeout=30)
 values=dict(x.split('=',1) for x in p.stdout.splitlines() if '=' in x)
 if p.returncode or not values.get('password'):raise SystemExit('系统Git安全凭据不可用；请在自己的终端登录，不把令牌发到聊天或文件。')
 return values['password']

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--assets',type=Path,required=True)
 p.add_argument('--manifest',type=Path,required=True)
 p.add_argument('--notes',type=Path,required=True)
 p.add_argument('--commit',required=True)
 p.add_argument('--execute',action='store_true')
 a=p.parse_args();m=json.loads(a.manifest.read_text());tag=m['tag']
 if m['repository']!=REPO:raise SystemExit('目标仓库不匹配')
 wanted={x['name']:x for x in m['assets']}
 for name,x in wanted.items():
  if Path(name).name!=name:raise SystemExit('资产名必须是单个文件名')
  f=a.assets/name
  if f.stat().st_size!=x['bytes'] or sha(f)!=x['sha256']:raise SystemExit('本地资产校验失败：'+name)
 extra=['release-manifest.json','SHA256SUMS']
 for name in extra:
  f=a.assets/name
  wanted[name]={'name':name,'bytes':f.stat().st_size,'sha256':sha(f)}
 subprocess.run(['sha256sum','-c','SHA256SUMS'],cwd=a.assets,check=True)
 print(json.dumps({'target':REPO,'tag':tag,'assets':len(wanted),'phase':'local-verified','execute':a.execute},ensure_ascii=False),flush=True)
 if not a.execute:return
 token=get_credential()
 def request(method,url,data=None):
  headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','User-Agent':'polaris-release-publisher','X-GitHub-Api-Version':'2022-11-28'}
  if isinstance(data,dict):data=json.dumps(data,ensure_ascii=False).encode();headers['Content-Type']='application/json'
  req=urllib.request.Request(url,data=data,headers=headers,method=method)
  with urllib.request.urlopen(req,timeout=60) as r:return json.load(r)
 permissions=request('GET',API).get('permissions',{})
 if not permissions.get('push'):raise SystemExit('凭据无目标仓库发布权限')
 try:release=request('GET',API+'/releases/tags/'+urllib.parse.quote(tag,safe=''))
 except urllib.error.HTTPError as e:
  if e.code!=404:raise
  release=request('POST',API+'/releases',{'tag_name':tag,'target_commitish':a.commit,'name':tag+'：MIX 2S 核心交互基线','body':a.notes.read_text(),'draft':True,'prerelease':True})
 if not release['draft']:
  existing={x['name']:x for x in release['assets']}
  if set(existing)!=set(wanted):raise SystemExit('已发布版本的资产列表不同，拒绝修改')
 else:existing={x['name']:x for x in release['assets']}
 for name,item in wanted.items():
  asset=existing.get(name)
  if asset:
   if asset['size']!=item['bytes'] or asset.get('digest') not in (None,'sha256:'+item['sha256']):
    raise SystemExit('远端同名资产不匹配，拒绝覆盖：'+name)
   print('已存在，校验：'+name,flush=True)
  else:
   if not release['draft']:raise SystemExit('拒绝向已发布版本补写资产')
   url=release['upload_url'].split('{',1)[0]+'?name='+urllib.parse.quote(name)
   print('上传：'+name+' ('+str(item['bytes'])+' bytes)',flush=True)
   # File-like body streams from disk; token is only an HTTPS header in memory.
   with (a.assets/name).open('rb') as body:
    headers={'Authorization':'Bearer '+token,'Content-Type':'application/octet-stream','Content-Length':str(item['bytes']),'User-Agent':'polaris-release-publisher','Accept':'application/vnd.github+json'}
    req=urllib.request.Request(url,data=body,headers=headers,method='POST')
    with urllib.request.urlopen(req,timeout=600) as r:asset=json.load(r)
  digest=asset.get('digest')
  if digest:
   if digest!='sha256:'+item['sha256']:raise SystemExit('GitHub SHA256 digest不匹配：'+name)
  else:
   # Use the public URL without Authorization: never forward credentials to a CDN.
   h=hashlib.sha256()
   with urllib.request.urlopen(asset['browser_download_url'],timeout=300) as r:
    while chunk:=r.read(1024*1024):h.update(chunk)
   if h.hexdigest()!=item['sha256']:raise SystemExit('公开下载回读SHA256不匹配：'+name)
  print('远端SHA256通过：'+name,flush=True)
 if release['draft']:release=request('PATCH',API+'/releases/'+str(release['id']),{'draft':False})
 print(json.dumps({'phase':'published','url':release['html_url'],'tag':tag,'verified_assets':len(wanted)},ensure_ascii=False),flush=True)

if __name__=='__main__':
 try:main()
 except urllib.error.HTTPError as e:
  raise SystemExit(f'GitHub HTTP {e.code}；未输出认证头。保留draft，核对后可按文件重试。')
