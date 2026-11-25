"""H09.S: conditional bounds, no original execution, no new neuronal model.
Run on H09.1 compact observations JSON and original GEN if available; use only
public derived indices and known GEN parameters. No raw pointers.
"""
import json,sys,base64,zlib,hashlib,struct,math,collections,statistics
from pathlib import Path

def unpack(r,k):
    b=zlib.decompress(base64.b64decode(r[k+'_zlib_b64']))
    assert len(b)==r[k+'_bytes'] and hashlib.sha256(b).hexdigest()==r[k+'_sha256']
    return b

def calculate(rows,states,frames,first=501):
    assert len(rows)==4096 and len(states)==640 and len(frames)==25
    margin=[]
    for f in frames[:24]:
        p=f['wpre'];q=f['wpost'];eligible=sorted([v for v in p if v[1]>0 and v[3]==0],key=lambda v:(-v[1],v[0]))
        win=eligible[0][0] if eligible else None
        assert [x[1] for x in q]==[x[1] if x[0]==win else 0 for x in p]
        if win==1:
            assert eligible[1][0]==2
            margin.append(eligible[0][1]-eligible[1][1])
    assert len(margin)==23
    pool=collections.defaultdict(list);exc2=set()
    for d,t,k,src,sus,w,l,s in rows:
        if src>=640 or states[src]!=[0,0]:continue
        if d==1 and t==1:pool[src].append((sus,w,l,s))
        if d==2 and t==0 and s>0:exc2.add(src)
    pool={src:cs for src,cs in sorted(pool.items()) if any(c[3]>0 for c in cs)}
    assert all(w==l==0 for cs in pool.values() for sus,w,l,s in cs)
    # Favorable fixed source output32; any owner activity allowed. Sus cannot
    # exceed max(initial,35) when goal <=32. LTW <= # clock boundaries.
    # Give *all* matching contacts (even initial zero strength) this allowance.
    # Ignore STW relaxation and strength loss in weights, but include owner
    # state relaxation, with integer ceiling to upper-bound the difference.
    out=[]
    for src,cs in pool.items():
        rec={'source':src,'positive_contacts':sum(s>0 for sus,w,l,s in cs),'all_contacts':len(cs),'also_excites_2':src in exc2,'max_initial_sus':max(sus for sus,w,l,s in cs),'bounds':{}}
        for chem in (31,255):
            for typ,contacts in [('positive',[c for c in cs if c[3]>0]),('all',cs)]:
                delta=0;peak=0;direct_peak=0;n_ltw=0;hs={}
                for n in range(1,513):
                    tick=first+n-1
                    # weights visible at NEXT update after transition; upper
                    # allowance includes current tick consolidation as extra slack.
                    n_ltw+=int(tick%128==0)
                    wmax=[min(255,n_ltw+(max(sus,35)*chem>>8)) for sus,w,l,s in contacts]
                    direct=min(128,(sum((32*w)>>8 for w in wmax)+1)//2)
                    y=min(255,delta+direct);peak=max(peak,y);direct_peak=max(direct_peak,direct)
                    delta=(y*0xaabb+65535)//65536
                    if n in (6,128,512):hs[str(n)]={'weight_max':max(wmax),'direct_max':direct_peak,'output_difference_bound':peak,'margins_reachable':sum(m<=peak for m in margin)}
                rec['bounds'][str(chem)+'_'+typ]=hs
        rec["saturated_weight_direct_bound"]=min(127,(sum(31 for _ in cs)+1)//2)
        out.append(rec)
    summary={}
    for chem in (31,255):
        for typ in ('positive','all'):
            key=str(chem)+'_'+typ
            summary[key]={}
            for n in ('6','128','512'):
                vals=[r['bounds'][key][n] for r in out];mx=max(v['output_difference_bound'] for v in vals)
                summary[key][n]={'max_direct':max(v['direct_max'] for v in vals),'max_difference':mx,'max_weight':max(v['weight_max'] for v in vals),'sources_reaching_min_margin':sum(v['output_difference_bound']>=min(margin) for v in vals),'max_margins_reachable':max(v['margins_reachable'] for v in vals)}
    return {'margins':margin,'margin_min':min(margin),'margin_median':statistics.median(margin),'margin_max':max(margin),'sources':len(out),'overlap_exc2':sum(r['also_excites_2'] for r in out),'start_tick':first,'cue_output':32,'ltw_updates_512':sum(t%128==0 for t in range(first,first+512)),'summary':summary,'per_source':out}

def compact(r):
    states=[list(x) for x in struct.iter_unpack('BB',unpack(r,'states'))]
    rows=[[i//256,(i//128)%2,i%128,*v] for i,v in enumerate(struct.iter_unpack('<HBBBB',unpack(r,'inventory')))]
    raw=unpack(r,'frames');frames=[]
    for i in range(25):
        v=list(raw[i*124:(i+1)*124]);frames.append({'wpre':[[j,*v[28+3*j:31+3*j]] for j in range(16)],'wpost':[[j,*v[76+3*j:79+3*j]] for j in range(16)]})
    return rows,states,frames

if __name__=='__main__':
    r=json.loads(Path(sys.argv[1]).read_text());out=calculate(*compact(r));print(json.dumps(out,indent=2,sort_keys=True))
