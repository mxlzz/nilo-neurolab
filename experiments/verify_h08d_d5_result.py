"""Recompute D5 from packed derived observations; no original binary needed."""
import base64,hashlib,json,pathlib,zlib
r=json.loads((pathlib.Path(__file__).resolve().parents[1]/"evidence"/"H08d_D5.1_observations.json").read_text())
def unpack(name,stride):
    x=zlib.decompress(base64.b64decode(r[name+"_zlib_b64"]))
    assert len(x)==r[name+"_bytes"] and hashlib.sha256(x).hexdigest()==r[name+"_sha256"]
    return [list(x[i:i+stride]) for i in range(0,len(x),stride)]
scan=unpack("scan",5);rows=unpack("frames",72)
eligible=[(i,x) for i,x in enumerate(scan) if x[:2]==[1,0] and x[2]<112 and x[3]>=24 and x[4]>0]
assert [next(i for i,x in eligible if p(x[2])) for p in (lambda x:x==40,lambda x:x==41,lambda x:x not in (40,41))]==r["selected"]
assert [sum(x[0]==n for x in scan) for n in (1,2,3)]==[128,292,220]
assert len(rows)==34
for k,start in enumerate((8,25)):
    i=2*k;j=4+i;p=[0]*8;p[i:i+2]=[32,32];m=0;matches=[0]*3;positive=[0]*3
    for x in rows[start:start+9]:
        post=p.copy();post[i]=p[i+1];post[i+1]=(p[i+1]*43707)>>16
        cp=post.copy();cp[j+1]=max(p[j+1],post[i]);perc=cp.copy();perc[j]=max(cp[j+1]-10,0);perc[j+1]=0
        m+=x[:32]==p+post+cp+perc;p=perc
        for role in range(3):
            q=x[36+12*role:48+12*role];src,w=q[:2]
            out=((src*w)>>8)*255>>8
            matches[role]+=q[10:12]==[out,(out*12965)>>16]
            positive[role]+=q[10]>0
    assert m==[9,1][k] and matches==[9,9,9] and positive==[[3,0,0],[0,1,0]][k]
assert all(x[:32]==[0]*32 and all(x[36+12*k+4:36+12*k+6]==x[36+12*k+10:36+12*k+12]==[0,0] for k in (0,1)) for x in rows[:8]+rows[17:25])
assert rows[25][10:12]==[32,21] and rows[26][2:4]==[0,0]
print("D5 formal FAIL; upstream A 9/9 B 1/9; conditional Concept 54/54; selection and basals verified")
