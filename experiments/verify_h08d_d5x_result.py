"""Independent arithmetic cross-check of derived D5x observations."""
import base64,hashlib,json,pathlib,zlib
r=json.loads((pathlib.Path(__file__).resolve().parents[1]/"evidence"/"H08d_D5x.1_observations.json").read_text())
def unpack(obj,name,stride):
    raw=zlib.decompress(base64.b64decode(obj[name+"_zlib_b64"]))
    assert len(raw)==obj[name+"_bytes"] and hashlib.sha256(raw).hexdigest()==obj[name+"_sha256"]
    return [list(raw[i:i+stride]) for i in range(0,len(raw),stride)]
f=unpack(r,"frames",32); c=unpack(r["reset"],"clear",4)
assert len(f)==34 and all(x==[0]*32 for x in f[:8]+f[17:25])
for k,start in enumerate((8,25)):
    i=2*k;j=4+i;p=[0]*8;p[i:i+2]=[32,32]
    for row in f[start:start+9]:
        post=p.copy();post[i]=p[i+1];post[i+1]=p[i+1]*43707>>16
        cp=post.copy();cp[j+1]=max(p[j+1],post[i])
        pe=cp.copy();pe[j]=max(cp[j+1]-10,0);pe[j+1]=0
        assert row==p+post+cp+pe;p=pe
assert len(c)==32 and all(row[2:]==[0,0] for row in c)
assert [(i,row[:2]) for i,row in enumerate(c) if any(row[:2])]==[(12,[183,175])]
assert r["reset"]["ordered_after"]=="ENDC 487" and r["reset"]["ordered_before"]=="LAYOUT 488"
assert r["pass"] is False and r["classification"]=="no_opportunity"
print("D4 18/18; basal 16/16; 32 clears including native active cell 12; injected witness absent; D5x NO OPPORTUNITY")
