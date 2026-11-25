"""Exact baseline-only selective revision diagnostic, NSR00. No random seeds."""
import json
from collections import defaultdict
from itertools import product

class Packed:
    def __init__(self, shared=False): self.bits=0; self.shared=shared
    def key(self,c,x): return x if self.shared else 4*c+x
    def act(self,c,x): return (self.bits>>self.key(c,x))&1
    def feedback(self,c,x,a,r):
        k=self.key(c,x); v=a if r==1 else 1-a
        self.bits=(self.bits&~(1<<k))|(v<<k)

class LRU:
    def __init__(self): self.rows=[]
    def act(self,c,x):
        key=4*c+x
        for j,(k,v) in enumerate(self.rows):
            if k==key:
                self.rows.append(self.rows.pop(j)); return v
        return 0
    def feedback(self,c,x,a,r):
        k=4*c+x; v=a if r==1 else 1-a
        self.rows=[p for p in self.rows if p[0]!=k]+[(k,v)];self.rows=self.rows[-4:]

class Factor:
    def __init__(self): self.base=0; self.z=0
    def act(self,c,x):return ((self.base>>x)&1)^(self.z*c)
    def feedback(self,c,x,a,r):
        v=a if r==1 else 1-a
        if c==0:self.base=(self.base&~(1<<x))|(v<<x)
        else:self.z=v^((self.base>>x)&1)

PAIRS=list(product(range(2),range(4)))

def run_one(agent,initial,mask,stats):
    def step(c,x,m,key,train=False):
        a=agent.act(c,x);y=(m>>(4*c+x))&1; correct=int(a==y)
        stats[key][0]+=correct;stats[key][1]+=1
        if train:agent.feedback(c,x,a,1 if correct else -1)
        return correct
    for c,x in PAIRS:step(c,x,initial,'first_acquisition',True)
    for c,x in PAIRS:step(c,x,initial,'acquisition')
    revised=initial^(mask<<4)
    for x in range(4):step(1,x,revised,'first_changed' if mask>>x&1 else 'first_unchanged',True)
    for c,x in PAIRS:
        step(c,x,revised,'post_return' if c==0 else 'post_changed' if mask>>x&1 else 'post_unchanged')
    for x in range(4):step(1,x,initial,'restore_first_changed' if mask>>x&1 else 'restore_first_unchanged',True)
    for c,x in PAIRS:step(c,x,initial,'reversal')

def summarize(stats):return {k:{'correct':v[0],'count':v[1],'accuracy':v[0]/v[1]} for k,v in sorted(stats.items())}

def main():
    result={'stage':'NSR00','families':{},'state_bits':{'packed':8,'shared':4,'lru_ordered':19,'factor':5},'ci_jobs':0,'neuronal_runs':0,'historical_seeds_used':0}
    for name,masks in [('partial',range(1,15)),('no_change',[0]),('global_context1',[15])]:
        arms={}
        for label,cls in [('packed',Packed),('shared',lambda:Packed(True)),('lru',LRU)]:
            stats=defaultdict(lambda:[0,0])
            for m,mask in product(range(256),masks):run_one(cls(),m,mask,stats)
            arms[label]=summarize(stats)
        result['families'][name]={'sequences':256*len(masks),'arms':arms}
    arms={}
    for label,cls in [('packed',Packed),('factor',Factor),('shared',lambda:Packed(True)),('lru',LRU)]:
        stats=defaultdict(lambda:[0,0])
        for b,z in product(range(16),range(2)):
            m=b|((b^(15*z))<<4);run_one(cls(),m,0,stats)
        arms[label]=summarize(stats)
    result['families']['factorized_no_change']={'sequences':32,'arms':arms}
    for fam in ('partial','no_change','global_context1'):
        a=result['families'][fam]['arms']['packed']
        for k in ('acquisition','post_return','post_changed','post_unchanged','reversal'):
            if k in a: assert a[k]['accuracy']==1
        if 'first_changed' in a: assert a['first_changed']['accuracy']==0
    assert all(result['families']['factorized_no_change']['arms']['factor'][k]['accuracy']==1 for k in ('acquisition','post_return','post_unchanged','reversal'))
    print(json.dumps(result,indent=2,sort_keys=True))
if __name__=='__main__':main()
