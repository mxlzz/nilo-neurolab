"""Recheck the D6 compact topology and WTA observation without original."""
import base64,hashlib,json,pathlib,zlib
r=json.loads((pathlib.Path(__file__).resolve().parents[1]/"evidence"/"H08d_D6.1_observations.json").read_text())
x=zlib.decompress(base64.b64decode(r["scan_zlib_b64"]))
assert len(x)==r["scan_bytes"] and hashlib.sha256(x).hexdigest()==r["scan_sha256"]
s=[list(x[i:i+5]) for i in range(0,len(x),5)]
assert len(s)==640 and [sum(v[0]==n for v in s) for n in (1,2,3)]==[150,263,227]
assert all(v[1]==0 for v in s)
eligible=[(i,v) for i,v in enumerate(s) if v[:2]==[1,0] and v[2]<112 and v[3]>=24 and v[4]>0]
assert len(eligible)==142
assert [next((i for i,v in eligible if p(v[2])),640) for p in (lambda y:y==40,lambda y:y==41,lambda y:y not in(40,41))]==r["concept_select"]==[640,236,7]
assert [(i,*v) for i,v in eligible if v[2]==41]==[(236,1,0,41,128,9),(237,1,0,41,128,6)]
p=r["wta_pre"];q=r["wta_post"]
k=max((v for v in p if not v[3] and v[1]>0),key=lambda v:v[1])[0]
assert k==1 and [v[1] for v in q]==[v[1] if v[0]==k else 0 for v in p]
assert r["classification"]=="instrumental_incomplete" and not r["pass"] and r["trig_attempts"]==0 and r["arms"]==[] and not r["decision_scan_executed"]
print("D6: full Concept scan, no singleton A, two B; one local WTA pair. Formal instrument incomplete, no exposures.")
