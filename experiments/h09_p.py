"""H09.P conditional population bounds; not a native experiment or prediction of a closed brain."""
import sys,json,zipfile,hashlib,collections,statistics,struct
from pathlib import Path
START=501; CHEM=31; KS=(1,3,6,9); H=(6,128,512); W=(128,512)

def run(rows,states,frames):
    margins=[]
    for f in frames[:24]:
        p=sorted((x for x in f['wpre'] if x[1]>0 and x[3]==0),key=lambda x:(-x[1],x[0]))
        assert [x[1] for x in f['wpost']]==[x[1] if p and x[0]==p[0][0] else 0 for x in f['wpre']]
        if p:
            assert p[0][0]==1 and p[1][0]==2
            margins.append(p[0][1]-p[1][1])
    assert len(margins)==23
    pool=collections.defaultdict(list)
    for d,t,k,src,sus,w,l,s in rows:
        if d==1 and t==1 and src<640 and states[src]==[0,0]:pool[src].append((sus,w,l,s))
    pool={src:cs for src,cs in sorted(pool.items()) if any(c[3]>0 for c in cs)}
    assert len(pool)==44 and all(w==l==0 for cs in pool.values() for sus,w,l,s in cs)
    def contribution(contacts):return sum((32*w)>>8 for w,l in contacts)
    def step(delta,contrib):
        u=(min(255,contrib)+1)//2 # ceil, favorable
        y=min(255,delta+u)
        return y,(y*0xaabb+65535)//65536,u
    def bound_weights(cs,t):
        lt=sum(x%128==0 for x in range(START,t+1))
        return [(min(255,lt+(max(sus,35)*CHEM>>8)),lt) for sus,w,l,s in cs]
    def no_reward(weights,t):
        out=[]
        for w,l in weights:
            if t&7==7:w=l+((w-l)*0xf999>>16)
            if t%128==0 and w>l:l+=1
            assert w>=l
            out.append((w,l))
        return out
    def rec(peak,direct):return {'max_output_difference':peak,'max_direct':direct,'margins_strictly_exceeded':sum(m<peak for m in margins)}
    result={}
    for typ in ('positive','all'):
        groups={src:[c for c in cs if typ=='all' or c[3]>0] for src,cs in pool.items()}
        result[typ]={}
        for k in KS:
            d=peak=direct=0; train={}
            for n in range(1,513):
                t=START+n-1
                vals=sorted((contribution(bound_weights(cs,t)) for cs in groups.values()),reverse=True)
                y,d,u=step(d,sum(vals[:k]));peak=max(peak,y);direct=max(direct,u)
                if n in H:train[str(n)]=rec(peak,direct)
            retention={}
            for wash in W:
                weights={src:bound_weights(cs,START+511) for src,cs in groups.items()}
                for t in range(START+512,START+512+wash):
                    weights={src:no_reward(ws,t) for src,ws in weights.items()}
                max_stw=max(w for ws in weights.values() for w,l in ws);max_ltw=max(l for ws in weights.values() for w,l in ws)
                d=peak=direct=0
                for t in range(START+512+wash,START+512+wash+9):
                    vals=sorted((contribution(ws) for ws in weights.values()),reverse=True)
                    y,d,u=step(d,sum(vals[:k]));peak=max(peak,y);direct=max(direct,u)
                    weights={src:no_reward(ws,t) for src,ws in weights.items()}
                retention[str(wash)]={**rec(peak,direct),'max_stw_at_probe':max_stw,'max_ltw_at_probe':max_ltw}
            result[typ][str(k)]={'train':train,'retention':retention}
    # Exact source-specific weight caps at the final training and wash boundary.
    return {'stage':'H09.P','start_tick':START,'chem_local':CHEM,'cue_output':32,'source_count':len(pool),'margins':margins,'margin_min':min(margins),'margin_median':statistics.median(margins),'margin_max':max(margins),'active_snapshot_count':sum(s[0]>0 for s in states),'results':result,'conditional':True}

if __name__=='__main__':
    p=Path(sys.argv[1]);b=p.read_bytes();assert hashlib.sha256(b).hexdigest()=='15c0e4e618940eeb6a1b67c9d1164e79c142387e3c15623dcafcb7e506cf36b9'
    with zipfile.ZipFile(p) as z:
        assert z.testzip() is None
        data=z.read('h09-1-result.json');assert hashlib.sha256(data).hexdigest()=='ef96424fb651e3f0d878ebac0cc3cfb0a8aa71b8703e67952e937b4ba725e044'
    t=json.loads(data)['trace'];inv=t['inventory'];assert inv['tick']==START
    rows,states,frames=inv['rows'],inv['states'],t['frames']
    assert len(rows)==4096 and len(states)==640 and len(frames)==25
    assert hashlib.sha256(b''.join(struct.pack('<HBBBB',*r[3:]) for r in rows)).hexdigest()=='f16845a03ef9c685d7fa92a908e3489b055260388ce47d447729cc64ae7a15ef'
    assert hashlib.sha256(bytes(v for s in states for v in s)).hexdigest()=='43800950bfa54551d5eb12957d3a5e3f732ebf6505566fbaf1e78362b491e019'
    print(json.dumps(run(rows,states,frames),indent=2,sort_keys=True))
