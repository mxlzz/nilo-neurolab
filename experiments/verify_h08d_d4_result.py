"""Recompute D4 recorded results without the acquisition analyzer."""
import json,pathlib
r=json.loads((pathlib.Path(__file__).resolve().parents[1]/"evidence"/"H08d_D4.1_result.json").read_text())
a=r["trace"]["analysis"];seg=a["segments"]
assert r["pass"] and r["trig_attempts"]==2 and r["reward_pulses"]==0
assert [len(s) for s in seg]==[8,17,9]
assert [c["tick"] for s in seg for c in s]==list(range(478,512))
assert all(c["layout"]==[9,112,16,40,16,40,32,16,40,640,0,2,0,2,0,1,0,1,0] for s in seg for c in s)
assert all(c[k]==[0]*8 for s in (seg[0],seg[1][9:]) for c in s for k in ("pre","post","copy","perception"))
for n,arm in enumerate(a["arms"]):
    assert arm["cell"]==8+n and len(arm["observed"])==9
    i=2*n;j=4+i;state=32;prev=[0]*8;prev[i:i+2]=[32,32]
    for c in arm["observed"]:
        new=prev.copy();new[i]=state;new[i+1]=(state*43707)>>16
        cp=new.copy();cp[j+1]=max(prev[j+1],state)
        pe=cp.copy();pe[j]=max(cp[j+1]-10,0);pe[j+1]=0
        assert (c["pre"],c["post"],c["copy"],c["perception"])==(prev,new,cp,pe)
        state=new[i+1];prev=pe
print("PASS: 18/18 synchronized predictions; 16/16 zero basals; 34/34 layouts")
