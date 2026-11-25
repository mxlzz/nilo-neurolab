"""Verify H09.N0 compact projection. No original or third-party dependencies."""
import json,base64,zlib,hashlib,collections
from pathlib import Path
r=json.loads((Path(__file__).resolve().parents[1]/"evidence/H09.N0_observations.json").read_text())
def unpack(k):
    v=r[k];b=zlib.decompress(base64.b64decode(v["zlib_b64"]))
    assert len(b)==v["bytes"] and hashlib.sha256(b).hexdigest()==v["sha256"]
    return b
ids=unpack("pattern_ids");w=unpack("wta");c=unpack("chem")
s=[set(r["patterns"][i]) for i in ids]
assert len(s)==256 and len(set(map(frozenset,s)))==28
A=next(x for x in s[:64] if len(x)>=3)
B=next((x for x in s[1:64] if len(x)>=3 and abs(len(x)-len(A))<=1 and 5*len(A&x)<=len(A|x)),None)
assert A==set(r["patterns"][0]) and B is None
assert sum(5*len(A&x)>=4*len(A|x) for x in s[64:])==11
wins=[]
for i in range(256):
    meta=w[i*6:i*6+6]
    assert meta[0]==16 and meta[1]&1 and meta[2]>0
    off=1536+i*96
    p=[w[off+3*j:off+3*j+3] for j in range(16)]
    q=[w[off+48+3*j:off+48+3*j+3] for j in range(16)]
    eligible=[j for j in range(16) if p[j][0]>0 and p[j][2]==0]
    k=max(eligible,key=lambda j:p[j][0]) if eligible else None
    assert [v[0] for v in q]==[p[j][0] if j==k else 0 for j in range(16)]
    wins.append(str(k))
assert dict(collections.Counter(wins))==r["winner_counts"]
assert all(any(c[i*33:(i+1)*33]) for i in range(256))
assert len(r["changed_sources"])==84 and len({x[0] for x in r["changed_sources"]})==84
print("H09.N0: 256 WTA, 28 supports, no B, Q absent, 84 endpoint differences. No training.")
