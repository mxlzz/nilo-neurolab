#!/usr/bin/env python3
"""Authorized NeuroLab snapshot and safe evidence transfer, not research execution."""
import concurrent.futures as cf, hashlib, json, os, pathlib, re, shutil, subprocess, tempfile, threading, urllib.request, urllib.error, zipfile
ROOT=pathlib.Path.cwd()
SOURCE="mxlzz/Nilo_public"
BRANCH="docs/neurolab-protocolo-20261120"
SHA="c0c06c95c176eb9c0e0df71853313d16acda0f27"
API="https://api.github.com/repos/"+SOURCE
TOKEN=os.environ.get("GH_TOKEN","")
def cmd(*a,cwd=None):return subprocess.check_output(a,cwd=cwd).decode().strip()
def dump(p,v):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def get(url):
    req=urllib.request.Request(url,headers={"Authorization":"Bearer "+TOKEN,"Accept":"application/vnd.github+json","User-Agent":"NeuroLab-migration"})
    with urllib.request.urlopen(req,timeout=60) as f:return json.load(f)
def pages(url,key):
    out=[]
    for page in range(1,101):
        rows=get(url+("&" if "?" in url else "?")+"per_page=100&page="+str(page))[key];out.extend(rows)
        if len(rows)<100:return out
    raise RuntimeError("pagination cap reached")
def source_head():return get(API+"/git/refs/heads/"+BRANCH)["object"]["sha"]
if source_head()!=SHA:raise RuntimeError("source moved: reconcile before transfer")
if (ROOT/"inherited").exists():raise RuntimeError("snapshot exists")
with tempfile.TemporaryDirectory() as td:
    repo=pathlib.Path(td);cmd("git","init","-q",cwd=repo);cmd("git","remote","add","origin","https://github.com/"+SOURCE+".git",cwd=repo)
    cmd("git","fetch","--depth=1","origin",SHA,cwd=repo);cmd("git","checkout","-q","--detach","FETCH_HEAD",cwd=repo)
    assert cmd("git","rev-parse","HEAD",cwd=repo)==SHA
    raw=subprocess.check_output(["git","ls-tree","-r","-z",SHA],cwd=repo)
    records=[]
    for row in raw.split(b"\0"):
        if not row:continue
        meta,path=row.split(b"\t",1);mode,typ,blob=meta.decode().split();p=path.decode()
        if not p.startswith(("docs/neurolab/","experiments/neurolab/",".github/workflows/neurolab-")):continue
        if typ!="blob" or mode not in ("100644","100755") or pathlib.Path(p).suffix.lower() not in {".md",".py",".json",".yml",".yaml",".txt",".csv",".gitignore",".ps1"}:raise ValueError("unexpected file "+p)
        dest=ROOT/"inherited"/p;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(repo/p,dest)
        assert cmd("git","hash-object","--no-filters",str(dest))==blob,p
        records.append({"source":p,"destination":"inherited/"+p,"git_blob_sha":blob,"mode":mode,"size":dest.stat().st_size})
    assert len(records)==514,len(records)
    dump(ROOT/"MIGRATION_MANIFEST.json",{"source":SOURCE,"branch":BRANCH,"source_commit":SHA,"source_tree":cmd("git","rev-parse","HEAD^{tree}",cwd=repo),"count":len(records),"files":records,"status":"exact_snapshot_verified","history":"DAG remains in original; workflows archived inactive; no original game or credentials copied"})
if source_head()!=SHA:raise RuntimeError("source moved during snapshot")
print("NEUROLAB_SNAPSHOT",len(records))
