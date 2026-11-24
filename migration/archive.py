#!/usr/bin/env python3
"""Archive public derived evidence only; never copy original game inputs or secrets."""
import concurrent.futures as cf, hashlib, json, os, pathlib, re, threading, urllib.request, urllib.error, zipfile
ROOT=pathlib.Path.cwd();M=json.loads((ROOT/"MIGRATION_MANIFEST.json").read_text())
SOURCE=M["source"];BRANCH=M["branch"];API="https://api.github.com/repos/"+SOURCE;TOKEN=os.environ["GH_TOKEN"]
LOCK=threading.Lock();TOTAL=0;BUDGET=350*1024*1024;LIMIT=90*1024*1024
CRITICAL={44852299967,44920963462,44969153930,44970236994,44970705424,44986258314,44987034290,44987744410,45028224155,45028560329,45049703202,45059347950,45492676512,45491763278,45490298944,45489733914}
def get(url):
    req=urllib.request.Request(url,headers={"Authorization":"Bearer "+TOKEN,"Accept":"application/vnd.github+json","User-Agent":"NeuroLab-evidence"})
    with urllib.request.urlopen(req,timeout=60) as f:return json.load(f)
def pages(url,key):
    out=[]
    for n in range(1,101):
        rows=get(url+("&" if "?" in url else "?")+"per_page=100&page="+str(n))[key];out+=rows
        if len(rows)<100:return out
    raise RuntimeError("pagination cap")
class Redirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        r=super().redirect_request(req,fp,code,msg,headers,newurl)
        if r:r.remove_header("Authorization")
        return r
def download(url,dest,digest=None,kind="artifact"):
    global TOTAL
    dest.parent.mkdir(parents=True,exist_ok=True);tmp=dest.with_suffix(".part")
    try:
        req=urllib.request.Request(url,headers={"Authorization":"Bearer "+TOKEN,"Accept":"application/vnd.github+json","User-Agent":"NeuroLab-evidence"})
        with urllib.request.build_opener(Redirect).open(req,timeout=90) as resp,tmp.open("wb") as f:
            h=hashlib.sha256();n=0
            while True:
                b=resp.read(1024*1024)
                if not b:break
                n+=len(b)
                if n>LIMIT:raise ValueError("individual size cap")
                f.write(b);h.update(b)
        sha=h.hexdigest()
        if digest and digest.removeprefix("sha256:")!=sha:raise ValueError("digest mismatch")
        with zipfile.ZipFile(tmp) as z:
            names=[x for x in z.infolist() if not x.is_dir()]
            if not names or sum(x.file_size for x in names)>700*1024*1024:raise ValueError("empty or oversized ZIP contents")
            allowed={".json",".jsonl",".csv",".tsv",".txt",".log",".md",".sha256",".sha",".xml"}
            for x in names:
                p=pathlib.PurePosixPath(x.filename)
                if p.is_absolute() or ".." in p.parts or p.suffix.lower() not in allowed:raise ValueError("non-allowlisted entry: "+p.suffix)
                # Do not republish private drive identifiers, unmasked tokens or credentials.
                with z.open(x) as f:
                    prev=b""
                    while True:
                        b=f.read(1024*1024)
                        if not b:break
                        w=prev+b
                        if re.search(rb'(?:https?://(?:drive\.google\.com/(?:file/d/|drive/folders/)|docs\.google\.com/[^\s]+/d/)|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AIza[0-9A-Za-z_-]{35})',w):raise ValueError("potential private link or token: archive withheld")
                        prev=w[-512:]
            if z.testzip() is not None:raise ValueError("CRC failure")
        with LOCK:
            if TOTAL+n>BUDGET:raise ValueError("global archival budget exceeded")
            TOTAL+=n;tmp.replace(dest)
        return {"status":"archived_verified_digest" if digest else "archived_local_sha256","path":dest.relative_to(ROOT).as_posix(),"sha256":sha,"bytes":n}
    except Exception as e:
        tmp.unlink(missing_ok=True);return {"status":"not_archived","error":str(e)}
def record(run):
    rid=run["id"];r={k:run.get(k) for k in ("id","name","head_sha","status","conclusion","html_url","path","created_at")}
    r["artifacts"]=[]
    try:
        for a in pages(API+"/actions/runs/"+str(rid)+"/artifacts","artifacts"):
            d={k:a.get(k) for k in ("id","name","size_in_bytes","expired","expires_at","digest")}
            if a.get("expired"):d["archive"]={"status":"expired"}
            elif not a.get("size_in_bytes") or a["size_in_bytes"]>LIMIT:d["archive"]={"status":"not_archived","error":"size or unknown"}
            else:d["archive"]=download(API+"/actions/artifacts/"+str(a["id"])+"/zip",ROOT/"evidence"/"archives"/str(rid)/(str(a["id"])+".zip"),a.get("digest"))
            r["artifacts"].append(d)
    except Exception as e:r["artifact_listing_error"]=str(e)
    # Historical logs can contain private input locations and are not bulk-republished.
    # Versioned derived evidence is the canonical H readback; retain public run provenance.
    if any(s in (r.get("path") or "") for s in ("original","mounted","full-cd","win32","startup","pulse","dendrite","eligibility-survey","consolidation-observation","discriminating-observation","vm-capability","h08a")):
        r["log"]={"status":"historical_log_not_republished","reason":"private original-media transfer and debug traces; derived versioned evidence preserved"}
    else:r["log"]=download(API+"/actions/runs/"+str(rid)+"/logs",ROOT/"evidence"/"logs"/(str(rid)+".zip"),kind="log")
    return r
runs=pages(API+"/actions/runs?branch=docs%2Fneurolab-protocolo-20261120","workflow_runs")
runs=[r for r in runs if ("neurolab-" in (r.get("path") or "") or (r.get("name") or "").lower().startswith("neurolab"))]
runs.sort(key=lambda x:(x["id"] not in CRITICAL,"isolated brain" in (x.get("name") or "").lower(),-x["id"]))
with cf.ThreadPoolExecutor(max_workers=6) as pool:records=list(pool.map(record,runs))
out={"source":SOURCE,"source_commit":M["source_commit"],"scope":"NeuroLab runs on source branch; public derived artifacts and safe non-historical logs only","run_count":len(records),"records":records,"archive_bytes":TOTAL,"budget_bytes":BUDGET}
(ROOT/"evidence"/"ARCHIVE_MANIFEST.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("NEUROLAB_ARCHIVE",json.dumps({"runs":len(records),"artifacts":sum(len(r["artifacts"]) for r in records),"archived_artifacts":sum(a["archive"]["status"].startswith("archived") for r in records for a in r["artifacts"]),"logs":sum(r["log"]["status"].startswith("archived") for r in records),"bytes":TOTAL}))
