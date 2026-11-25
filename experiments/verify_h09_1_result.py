"""Verify compact H09.1 observations, without original."""
import base64,hashlib,json,pathlib,struct,zlib,collections,statistics
r=json.loads((pathlib.Path(__file__).resolve().parents[1]/"evidence/H09.1_observations.json").read_text())
def unpack(k):
    b=zlib.decompress(base64.b64decode(r[k+"_zlib_b64"]))
    assert len(b)==r[k+"_bytes"] and hashlib.sha256(b).hexdigest()==r[k+"_sha256"]
    return b
inv=list(struct.iter_unpack("<HBBBB",unpack("inventory")))
states=list(struct.iter_unpack("BB",unpack("states")))
frames=unpack("frames")
assert len(inv)==4096 and len(states)==640 and sum(x[-1]>0 for x in inv)==1485 and sum(x==(0,0) for x in states)==631
assert all(x[0]<640 for x in inv)
wins=[];gaps=[];runner=[]
for i in range(25):
    v=list(frames[124*i:124*(i+1)]);m=v[:3];p=[v[28+3*j:31+3*j] for j in range(16)];q=[v[76+3*j:79+3*j] for j in range(16)]
    eligible=sorted((j for j in range(16) if p[j][0]>0 and p[j][2]==0),key=lambda j:(-p[j][0],j))
    k=eligible[0] if eligible else None
    assert m[0]==16 and m[1]&1 and m[2] and [x[0] for x in q]==[x[0] if j==k else 0 for j,x in enumerate(p)]
    wins.append(k)
    if i<24 and len(eligible)>=2:runner.append(eligible[1]);gaps.append(p[k][0]-p[eligible[1]][0])
assert collections.Counter(wins[:24])=={1:23,None:1} and wins[24]==1
assert runner==[2]*23 and (min(gaps),max(gaps),statistics.median(gaps))==(42,126,102)
def sources(d,t):
    return {x[0] for x in inv[(2*d+t)*128:(2*d+t+1)*128] if x[-1]>0 and states[x[0]]==(0,0)}
assert len(sources(1,0)&sources(2,0))==10
assert len(sources(1,1)&sources(2,0))==15
assert len(sources(1,0)&sources(1,1)&sources(2,0)&sources(2,1))==6
assert r["classification"]=="no_opportunity" and r["trig_attempts"]==0 and r["requests"]==[] and r["selected"] is None
print("H09.1 inventory, 25 WTA cycles and exploratory overlap verified; no intervention")
