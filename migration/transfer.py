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
    records=[]; exceptions=[]
    for row in raw.split(b"\0"):
        if not row:continue
        meta,path=row.split(b"\t",1);mode,typ,blob=meta.decode().split();p=path.decode()
        if not p.startswith(("docs/neurolab/","experiments/neurolab/",".github/workflows/neurolab-")):continue
        if typ!="blob" or mode not in ("100644","100755") or pathlib.Path(p).suffix.lower() not in {".md",".py",".json",".yml",".yaml",".txt",".csv",".gitignore",".ps1"}:raise ValueError("unexpected file "+p)
        dest=ROOT/"inherited"/p;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(repo/p,dest)
        assert cmd("git","hash-object","--no-filters",str(dest))==blob,p
        original_size=dest.stat().st_size
        rawbytes=dest.read_bytes()
        # Public source document may mention private folder locations; preserve provenance, not access identifiers.
        clean=re.sub(rb'https?://drive\.google\.com/drive/(?:u/\d+/)?folders/[A-Za-z0-9_-]{15,}',b'[private folder reference withheld]',rawbytes)
        clean=re.sub(rb'(carpeta\s+`)[A-Za-z0-9_-]{20,}(`)',rb'\1[private folder ID withheld]\2',clean,flags=re.I)
        clean=re.sub(rb'(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AIza[0-9A-Za-z_-]{35})',b'[potential credential withheld]',clean)
        if clean!=rawbytes:
            dest.write_bytes(clean);exceptions.append({"path":p,"reason":"private folder identifier or potential credential withheld; source SHA retained"})
        records.append({"source":p,"destination":"inherited/"+p,"git_blob_sha":blob,"destination_git_blob_sha":cmd("git","hash-object","--no-filters",str(dest)),"mode":mode,"source_size":original_size,"size":dest.stat().st_size})
    assert len(records)==514,len(records)
    dump(ROOT/"MIGRATION_MANIFEST.json",{"source":SOURCE,"branch":BRANCH,"source_commit":SHA,"source_tree":cmd("git","rev-parse","HEAD^{tree}",cwd=repo),"count":len(records),"files":records,"status":"snapshot_verified_with_documented_exceptions" if exceptions else "exact_snapshot_verified","exceptions":exceptions,"history":"DAG remains in original; workflows archived inactive; no original game or credentials copied"})
if source_head()!=SHA:raise RuntimeError("source moved during snapshot")
print("NEUROLAB_SNAPSHOT",len(records))
