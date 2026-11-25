"""H09.1: bounded native Concept to free Decision feasibility. No reward."""
import hashlib,json,os,pathlib,re,struct,subprocess,sys,tempfile,time
from collections import Counter
from itertools import combinations
import h08d_d1 as d1
import h08d_d3 as d3
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"inherited"))
from experiments.neurolab.c1_synapse_integrated import C1SynapseState,C1SynapticInput,DECISION_EXCITATORY_GENE,update_c1_synapse
from experiments.neurolab.c1_dendrite_tick import DendriteState
OUT=pathlib.Path("h09-1-result.json")
RESULT={"stage":"H09.1","subject_created":False,"pass":False,"classification":"launcher_not_reached","trig_attempts":0,"reward_pulses":0,"requests":[]}
ARMS=("A","S","B","B","S","A")
CAP=4*1024*1024
C="poi(@$t0+0x6e4)";D="poi(@$t0+0x554)";P="poi(@$t0+0xa4)"
SIZES={"RB":12,"RP":11,"WPRE":3,"WPOST":3,"WP":4,"WQ":4,"INV":4,"INV_END":0,"P":8,"SIG_META":3,"SIG":7,"SPRE":11,"SPOST":11,"SAFTER":11,"CPOST":4,"MARK":6,"TPRE":8,"TPOST":8,"ATT":2,"ALT":1}
def save():OUT.write_text(json.dumps(RESULT,indent=2,sort_keys=True)+"\n",encoding="utf-8")
def pr(tag,v=(),direct=False):
    s=d3.pr(tag," ".join(["%u","%08x"]+["%u"]*len(v)),["@$t2","@$t0",*v]).replace("NL_D3_","NL_H9_")
    return s.replace("\\\\n","\\n") if direct else s
def check(cond,body):
    return ".if ("+cond+") { "+body+" } .else { .echo NL_H9_BAD; qd }"
def valid(ptr,n):return "($vvalid("+ptr+",0x%x)"%n+"==1)"
def byte(p,i):return f"by({p}+0x{i:x})"
def u32(b,i):return struct.unpack_from("<I",b,i)[0]
def chemistry():
    p="poi(@$t1+0x2c1c)"
    return [byte(p,8+2*i) for i in (49,50,51,54,55)]+[byte("@$t0+0x4b8",i) for i in range(0xc3,0xc7)]+[byte("@$t0+0x648",i) for i in range(0xc3,0xc5)]
def wta(tag,celltag,direct=False):
    m=pr(tag,["poi(@$t0+0x55c)","by(@$t0+0x4da)","poi(@$t0+0x568)"],direct)
    cell="("+D+"+@$t12*0x10)"
    row=pr(celltag,["@$t12",byte(cell,2),byte(cell,3),byte(cell,14)],direct)
    return m+"; .for (r @$t12=0; @$t12<0x10; r @$t12=@$t12+1) { "+row+" }"
def dump_script():
    lines=[check("(poi(@$t0+0x6ec)==0n640)&(poi(@$t0+0x55c)==0n16)&"+valid(C,10240)+"&"+valid(D,256),pr("INV",[C,D,"poi(@$t0+0x6ec)","poi(@$t0+0x55c)"],True)),
           ".writemem h9c.bin "+C+" L0x2800",".writemem h9d.bin "+D+" L0x100"]
    for i in range(16):
        for typ in range(2):
            owner=f"({D}+0x{i*16:x})";ptr=f"poi({owner}+0x{4+4*typ:x})"
            lines.append(check(f"(by({owner}+0x{12+typ:x})==0x80)&"+valid(ptr,1536),f".writemem h9s{i}_{typ}.bin {ptr} L0x600"))
    lines += [pr("INV_END",[],True),"r @$t9=1"]
    return "\n".join(lines)+"\n"
def cue(sel):
    return [byte(f"({C}+0x{i*16:x})",j) for i in sel["concept"] for j in (2,3)]
def contact_script(sel,tag):
    lines=[]
    for role,dest,slot in sel["slots"]:
        owner=f"({D}+0x{dest*16:x})";ptr=f"(poi({owner}+4)+0x{slot*12:x})";src=f"poi({ptr})"
        vals=[str(role),f"0n{dest}",f"0n{slot}",f"(({src}-{C})/0x10)",byte(src,2)]+[byte(ptr,k) for k in range(6,10)]+[byte(owner,2),byte(owner,3)]
        body=pr(tag,vals,True)
        other=pr(tag,[f"0n{role}",f"0n{dest}",f"0n{slot}","0n999","0"]+[byte(ptr,k) for k in range(6,10)]+[byte(owner,2),byte(owner,3)],True)
        srcok=f"(({src}>={C})&({src}<{C}+0x2800)&((({src}-{C})&0xf)==0))"
        lines.append(check(f"(by({owner}+0xc)==0x80)&"+valid(ptr,12),f".if ({srcok}) {{ {body} }} .else {{ {other} }}"))
    return "\n".join(lines)+"\n"
def signature_script(sel):
    lines=[]
    for role,i in enumerate(sel["concept"]):
        owner=f"({C}+0x{i*16:x})"
        lines.append(pr("SIG_META",[f"0n{role}",byte(owner,12),byte(owner,13)],True))
        for typ in range(2):
            count=byte(owner,12+typ);arr=f"poi({owner}+0x{4+typ*4:x})";ptr=f"({arr}+@$t12*0xc)";src=f"poi({ptr})"
            row=pr("SIG",[f"0n{role}",f"0n{typ}","@$t12",f"(({src}-{P})/0x10)",byte(ptr,7),byte(ptr,8),byte(ptr,9)],True)
            bad=pr("SIG",[f"0n{role}",f"0n{typ}","@$t12","0n999",byte(ptr,7),byte(ptr,8),byte(ptr,9)],True)
            ok=f"(({src}>={P})&({src}<{P}+0x700)&((({src}-{P})&0xf)==0))"
            inner=f".if ({ok}) {{ {row} }} .else {{ {bad} }}"
            loop=f".for (r @$t12=0; @$t12<{count}; r @$t12=@$t12+1) {{ {inner} }}"
            lines.append(f".if ({count}!=0) {{ "+check(f"({count}<=0x80)&($vvalid({arr},{count}*0xc)==1)",loop)+" }")
    return "\n".join(lines)+"\n"
def scripts(sel):
    v=cue(sel);local=[byte("@$t0+0x4b8",i) for i in range(0xc3,0xc7)]
    return {
        "h9pre.txt":pr("P",v+local,True)+"\n"+signature_script(sel)+contact_script(sel,"SPRE"),
        "h9post.txt":contact_script(sel,"SPOST"),
        "h9after.txt":contact_script(sel,"SAFTER"),
        "h9concept.txt":pr("CPOST",v,True)+"\n",
        "h9mark.txt":pr("MARK",["@eax","@$t3"]+v,True)+"\n",
        "h9tpre.txt":pr("TPRE",["@$t6","@$t7","@$t8","@$t3"]+v,True)+"\n",
        "h9tpost.txt":pr("TPOST",["@$t6","@$t7","@$t8","@$t3"]+v,True)+"\n",
    }
def commands():
    rb=".if (@$t0==0) { r @$t0=@ecx; r @$t1=@esi }; "+check("(@ecx==@$t0)&(@esi==@$t1)&(@$t3==0)&(poi(@$t0+0x6ec)==0n640)&(poi(@$t0+0x55c)==0n16)",
        "r @$t2=poi(@esi+0x2c20); r @$t3=1; .if ((@$t9==1)&(@$t5==0)) { $$>a<h9arm.txt }; "+pr("RB",["@$t5"]+chemistry())+"; gc")
    dp=".if ((@$t3==1)&(@ecx==@$t0+0x4b8)) { .if ((@$t4>=0n24)&(@$t9==0)) { $$>a<h9inv.txt }; .if (@$t5==1) { $$>a<h9pre.txt }; gc } .else { gc }"
    wp=".if ((@$t3==1)&(@ebx==@$t0+0x4b8)) { "+wta("WPRE","WP")+"; .if (@$t5==1) { $$>a<h9post.txt }; gc } .else { gc }"
    wq=".if ((@$t3==1)&(@ebx==@$t0+0x4b8)) { "+wta("WPOST","WQ")+"; gc } .else { gc }"
    after=".if ((@$t3==1)&(@$t5==1)&(@esi==@$t0)) { .if (@edi==6) { $$>a<h9after.txt }; .if (@edi==8) { $$>a<h9concept.txt }; gc } .else { gc }"
    rp=".if (@$t3==1) { "+check("(@esi==@$t1)&(poi(@esi+0x2c18)==@$t0)&(poi(@esi+0x2c20)==@$t2)",pr("RP",chemistry())+"; r @$t3=0; r @$t4=@$t4+1; .if (@$t4>=0n512) { .echo NL_H9_CAP; qd } .else { gc }")+" } .else { gc }"
    trigpre=".if ((@$t5==1)&(@ecx==@$t0)) { r @$t2=poi(@$t1+0x2c20); r @$t6=poi(@esp); r @$t7=poi(@esp+4); r @$t8=poi(@esp+8); $$>a<h9tpre.txt; gc } .else { gc }"
    trigpost=".if ((@$t5==1)&(poi(@esi+0xa4)==@$t1)) { $$>a<h9tpost.txt; gc } .else { gc }"
    mrk=".if ((@eax==0n31999)&(@$t0!=0)) { .if (poi(@ebx+0xa4)==@$t1) { .echo NL_H9_END; qd } .else { gc } } .else { .if ((@$t5==1)&((@eax==0n30999)|((@eax>=0n31000)&(@eax<=0n31055))|((@eax>=0n32000)&(@eax<=0n32005)))) { "+check("poi(@ebx+0xa4)==@$t1","r @$t2=poi(@$t1+0x2c20); $$>a<h9mark.txt; gc")+" } .else { gc } }"
    ap=".if ((@$t0!=0)&(@esi==@$t1)) { r @$t14=poi(@esp); r @$t15=@ebx; gc } .else { gc }"
    aq=".if ((@$t0!=0)&(@esi==@$t1)) { r @$t2=poi(@$t1+0x2c20); "+pr("ATT",["@$t15","(poi(@esi+0x7f0)==@$t14)"])+"; gc } .else { gc }"
    alt=".if ((@$t0!=0)&(@ecx==@$t0)&(poi(@esp)==Creatures+0x5db4)) { r @$t2=poi(@$t1+0x2c20); "+pr("ALT",["1"])+"; gc } .else { gc }"
    lines=[".echo NL_H9_READY"]+[f"r @$t{i}=0" for i in range(16)]+[d3.bp(off,s) for off,s in [(0x7583,rb),(0x3e00,dp),(0x48a0,wp),(0x4911,wq),(0x3caa,after),(0x759a,rp),(0x16b39,trigpre),(0x16b3e,trigpost),(0x156df,mrk),(0x9cf8,ap),(0x9cfd,aq),(0x3bb0,alt)]]+["g"]
    if any(len(s)>4096 for s in lines):raise RuntimeError("command_too_long")
    return "\n".join(lines)+"\n"
def parse(raw):
    events=[];errors=[];brains={};counts=Counter()
    for n,line in enumerate(raw.splitlines(),1):
        s=line.strip()
        if not s.startswith("NL_H9_"):continue
        a=s.split();tag=a[0][6:];counts[tag]+=1
        if tag in ("READY","END","CAP","BAD") and len(a)==1:
            if tag=="BAD":errors.append({"line":n,"tag":"BAD","category":"guard"})
            events.append({"tag":tag});continue
        try:
            if tag not in SIZES or len(a)!=3+SIZES[tag] or not a[1].isdigit() or not re.fullmatch("[0-9a-fA-F]{8}",a[2]) or int(a[2],16)==0 or not all(x.isdigit() for x in a[3:]):raise ValueError()
            tick=int(a[1]);v=list(map(int,a[3:]))
            if tick>0xffffffff or any(x>0xffffffff for x in v):raise ValueError()
            brain=brains.setdefault(a[2].lower(),"B"+str(len(brains)+1))
            events.append({"tag":tag,"tick":tick,"brain":brain,"v":v,"pos":len(events)})
        except ValueError:
            errors.append({"line":n,"tag":tag if tag in SIZES else "unknown","expected":SIZES.get(tag),"actual":len(a)-3,"sha256":hashlib.sha256(s.encode()).hexdigest(),"category":"malformed"})
    for name,pat in (("syntax",r"Syntax error|Extra character|Illegal"),("access",r"Unable to read|Memory access error|access violation"),("bp",r"Unable to resolve|Couldn't resolve|Unable to insert breakpoint"),("operand",r"Operand error|Bad register|Invalid register"),("script",r"Unable to open|Could not open|Unable to write|Couldn't open")):
        if re.search(pat,raw,re.I):errors.append({"category":name})
    return events,dict(counts),errors
def read_inv(root,events,baseline):
    iv=[x for x in events if x["tag"]=="INV"];ends=[x for x in events if x["tag"]=="INV_END"]
    if len(iv)!=1 or len(ends)!=1 or iv[0]["tick"]!=ends[0]["tick"] or iv[0]["brain"]!=ends[0]["brain"]:raise RuntimeError("inventory_markers")
    cb,db,nc,nd=iv[0]["v"]
    if (nc,nd)!=(640,16) or not cb or not db:raise RuntimeError("inventory_layout")
    def exact(name,n):
        b=(root/name).read_bytes()
        if len(b)!=n:raise RuntimeError("inventory_length")
        return b
    c=exact("h9c.bin",10240);d=exact("h9d.bin",256)
    states=[[c[i*16+2],c[i*16+3]] for i in range(640)];rows=[]
    for i in range(16):
        for typ in range(2):
            if d[i*16+12+typ]!=128:raise RuntimeError("inventory_counts")
            b=exact(f"h9s{i}_{typ}.bin",1536)
            for k in range(128):
                src=u32(b,k*12);vals=list(b[k*12+6:k*12+10])
                if src==0 and vals[-1]==0:index=999
                elif cb<=src<cb+10240 and (src-cb)%16==0:index=(src-cb)//16
                else:raise RuntimeError("inventory_source")
                rows.append([i,typ,k,index,*vals])
    rank=Counter(f["winner"] for f in baseline if f["winner"] is not None)
    eligible=sorted([i for i,n in rank.items() if n>=2],key=lambda i:(-rank[i],i))
    srcs={i:{r[3] for r in rows if r[0]==i and r[1]==0 and r[-1]>0 and r[3]<640 and states[r[3]]==[0,0]} for i in eligible}
    pairs=[]
    for x,y in combinations(eligible,2):
        common=sorted(srcs[x]&srcs[y]);pairs.append([x,y,len(common)])
    inv={"tick":iv[0]["tick"],"states":states,"rows":rows,"winner_counts":sorted(rank.items()),"eligible_destinations":eligible,"pair_counts":pairs,"selected":None}
    p=next((p for p in pairs if p[2]>=2),None)
    if p:
        x,y=p[:2];cs=sorted(srcs[x]&srcs[y])[:2]
        slots=[[role,dest,next(r[2] for r in rows if r[0]==dest and r[1]==0 and r[3]==src and r[-1]>0)] for role,src in enumerate(cs) for dest in (x,y)]
        inv["selected"]={"concept":cs,"destinations":[x,y],"slots":slots}
    return inv
def collect(events,sel=None):
    frames=[];cur=None;bad=[]
    for pos,e in enumerate(events):
        tag=e["tag"]
        if tag=="RB":
            if cur is not None:bad.append("nested_RB")
            cur={"tick":e["tick"],"brain":e["brain"],"start":pos,"records":[e]}
        elif tag=="RP":
            if cur is None:continue
            cur["records"].append(e);cur["end"]=pos
            r=cur["records"];cur=None
            try:
                if any(x["tick"]!=r[0]["tick"] or x["brain"]!=r[0]["brain"] for x in r):raise ValueError("identity")
                groups={k:[x["v"] for x in r if x["tag"]==k] for k in SIZES}
                active=r[0]["v"][0]
                wpre,wpost=groups["WPRE"],groups["WPOST"];wp,wq=groups["WP"],groups["WQ"]
                if active not in (0,1) or len(wpre)!=1 or len(wpost)!=1 or wpre[0][0]!=16 or wpost[0][0]!=16 or [v[0] for v in wp]!=list(range(16)) or [v[0] for v in wq]!=list(range(16)):raise ValueError("WTA_shape")
                if any(any(not 0<=n<=255 for n in v[1:]) for v in wp+wq):raise ValueError("WTA_byte")
                if not(wpre[0][1]&1 and wpost[0][1]&1):raise ValueError("WTA_flag")
                match=d1.predict([v[1] for v in wp],[v[3] for v in wp],wpre[0][1],wpre[0][2])==[v[1] for v in wq]
                wins=[v[0] for v in wq if v[1]>0];winner=wins[0] if len(wins)==1 and wpre[0][2] else None
                f={"tick":r[0]["tick"],"brain":r[0]["brain"],"start":next(x["pos"] for x in r if x["tag"]=="RB"),"end":pos,"selected":bool(active),"winner":winner,"wta_match":match,"wpre":wp,"wpost":wq,"wta_meta":[wpre[0],wpost[0]],"chem_pre":r[0]["v"][1:],"chem_post":e["v"]}
                if any(not 0<=v<=255 for v in f["chem_pre"]+f["chem_post"]):raise ValueError("chemical_byte")
                expected=["RB"]+["WPRE"]+["WP"]*16+["WPOST"]+["WQ"]*16+["RP"]
                actual=[x["tag"] for x in r if x["tag"] not in ("INV","INV_END","ATT","ALT")]
                if active:
                    if sel is None:raise ValueError("selection_missing")
                    p=groups["P"];cp=groups["CPOST"];meta=groups["SIG_META"];sig=groups["SIG"]
                    if len(p)!=1 or len(cp)!=1 or [v[0] for v in meta]!=[0,1]:raise ValueError("cue_shape")
                    if any(not 0<=n<=255 for n in p[0]+cp[0]):raise ValueError("cue_byte")
                    if any(not 0<=n<=128 for v in meta for n in v[1:]):raise ValueError("signature_count")
                    exp=[(role,typ,k) for role,n0,n1 in meta for typ,n in enumerate((n0,n1)) for k in range(n)]
                    if [tuple(v[:3]) for v in sig]!=exp:raise ValueError("signature_shape")
                    if any(not(0<=v[3]<112 or v[3]==999) or any(not 0<=n<=255 for n in v[4:]) for v in sig):raise ValueError("signature_byte")
                    phases=[groups[x] for x in ("SPRE","SPOST","SAFTER")]
                    if any([v[:3] for v in group]!=sel["slots"] for group in phases):raise ValueError("slot_shape")
                    if any(not(0<=v[3]<640 or v[3]==999) or any(not 0<=n<=255 for n in v[4:]) for group in phases for v in group):raise ValueError("slot_byte")
                    stable=all(v[3]==sel["concept"][v[0]] and v[8]>0 for group in phases for v in group)
                    f.update({"cue_pre":p[0][:4],"local":p[0][4:],"cue_post":cp[0],"signature_meta":meta,"signature":sig,"slots":phases,"stable_slots":stable})
                    expected=["RB","P"]+[k for v in meta for k in ["SIG_META"]+["SIG"]*(v[1]+v[2])]+["SPRE"]*4+["WPRE"]+["WP"]*16+["SPOST"]*4+["WPOST"]+["WQ"]*16+["SAFTER"]*4+["CPOST","RP"]
                if actual!=expected:raise ValueError("phase_order")
                frames.append(f)
            except (ValueError,IndexError,KeyError) as exc:bad.append(str(exc) if type(exc) is ValueError else "frame_shape")
        elif cur is not None and tag in SIZES:cur["records"].append(e)
    if len({f["brain"] for f in frames})>1 or any(b["tick"]!=a["tick"]+1 for a,b in zip(frames,frames[1:])):bad.append("regular_continuity")
    return frames,bad
def sigkey(f):
    return (f["signature_meta"],[x[:6] for x in f["signature"]])
def basal(fs):
    return len(fs)>=8 and all(f["selected"] and f["stable_slots"] and f["wta_match"] and f["cue_pre"]==f["cue_post"]==[0]*4 and all(x[3]<112 for x in f["signature"]) for f in fs[-8:]) and all(sigkey(f)==sigkey(fs[-8]) for f in fs[-8:])
def opportunity(f,sel):
    out=[]
    for a,b,z in zip(*f["slots"]):
        role,dest,slot=a[:3]
        stable=a[3]==b[3]==z[3]==sel["concept"][role] and a[4]==b[4]==z[4] and min(a[8],b[8],z[8])>0
        if not stable:continue
        old=C1SynapseState(DendriteState(*a[5:8]),a[8])
        inp=lambda chem:C1SynapticInput(source_output=a[4],owner_output=a[9],owner_state=a[10],chemicals=tuple(chem))
        real=update_c1_synapse(old,DECISION_EXCITATORY_GENE,inp(f["local"]),tick=f["tick"]).after
        chem=f["local"].copy();chem[0]=min(255,chem[0]+31)
        virt=update_c1_synapse(old,DECISION_EXCITATORY_GENE,inp(chem),tick=f["tick"]).after
        pred=[real.dendrite.susceptibility,real.dendrite.stw,real.dendrite.ltw,real.strength]
        match=b[5:9]==pred
        eligible=(a[5]>0 or real.dendrite.susceptibility>0) and virt.dendrite.stw>real.dendrite.stw
        out.append({"pair":[role,dest],"slot":slot,"tick":f["tick"],"input":a[4],"before":a[5:9],"observed":b[5:9],"predicted":pred,"virtual_stw":virt.dendrite.stw,"match":match,"virtual_discrimination":eligible,"opportunity":bool(eligible and match)})
    return out
def wash(fs):
    req=[0,1,2,5,6,7,8,9,10]
    for i in range(len(fs)-7):
        window=fs[i:i+8]
        if all(f["selected"] and all(f[k][j]==0 for k in ("chem_pre","chem_post") for j in req) and f["local"]==[0]*4 for f in window):
            echoes=all(f[k][j]==0 for f in window for k in ("chem_pre","chem_post") for j in (3,4))
            if echoes:return {"ticks":[f["tick"] for f in window],"echoes_zero":True}
    return None
def analyze(events,frames,sel,requests):
    result={"T":False,"F":False,"O":False,"Q":False,"arms":[],"opportunities":[],"wash":None}
    marks=[e for e in events if e["tag"]=="MARK"];pulses=[e for e in events if e["tag"] in ("TPRE","TPOST")]
    expected=[30999]+[n for i in range(6) for n in [*(31000+10*i+j for j in range(6)),32000+i]]
    if [m["v"][0] for m in marks]!=expected or [r["code"] for r in requests]!=expected or not all(r.get("ack",{}).get("ok") and r["ack"].get("value")==r["code"] for r in requests) or len(pulses)!=48:return result
    if any(m["v"][1]!=0 for m in marks):return result
    if marks[0]["v"][2:]!=[0]*4:return result
    byid={m["v"][0]:m for m in marks}
    idx=0;end=-1;winners=set();roles_with_winner=set();opps=set();functional=True;timing=True
    for i,arm in enumerate(ARMS):
        ms=[byid[31000+10*i+j] for j in range(6)]
        fb=byid[32000+i];role=None if arm=="S" else (0 if arm=="A" else 1)
        consumed=[]
        before=[f for f in frames if end<f["start"] and f["end"]<ms[0]["pos"]]
        if not basal(before):return result
        for j,m in enumerate(ms):
            f=next((f for f in frames if f["start"]>m["pos"]),None)
            if f is None or not f["selected"] or f["tick"] not in (m["tick"],m["tick"]+1):return result
            if any(e["tag"]=="ALT" and m["pos"]<e["pos"]<f["start"] for e in events):return result
            consumed.append(f)
            if j and (m["tick"]-ms[j-1]["tick"] not in (1,2) or f["tick"]-consumed[-2]["tick"] not in (1,2)):return result
            if role is None:
                if m["v"][2:]!=[0]*4 or f["cue_pre"]!=[0]*4:functional=False
            else:
                a,b=pulses[idx:idx+2];idx+=2
                if a["tag"]!="TPRE" or b["tag"]!="TPOST" or not a["pos"]<b["pos"]<m["pos"] or (j and a["pos"]<=ms[j-1]["pos"]) or a["v"][:4]!=[8,sel["concept"][role],32,0] or b["v"][:4]!=a["v"][:4] or a["brain"]!=b["brain"] or b["brain"]!=m["brain"]:return result
                off=2*role;other=2*(1-role);q=b["v"][4:];p=a["v"][4:]
                if q[off:off+2]!=[32,32] or p[other:other+2]!=q[other:other+2] or m["v"][2:]!=q:return result
                if f["cue_pre"][off]==0 or f["cue_pre"][other]!=0:functional=False
        final=consumed[-1];post=[f for f in frames if f["start"]>=final["start"]][:9]
        if len(post)!=9:return result
        end=post[-1]["end"]
        if i<5 and byid[31000+10*(i+1)]["pos"]<=end:return result
        if not(final["end"]<fb["pos"]<=end) or not 0<=fb["tick"]-final["tick"]<=2:timing=False
        full=[f for f in frames if ms[0]["pos"]<f["start"] and f["end"]<=end]
        stable=all(f["stable_slots"] and f["wta_match"] and all(x[3]<112 for x in f["signature"]) and sigkey(f)==sigkey(before[-1]) for f in full)
        functional=functional and stable
        winner=final["winner"]
        if role is not None and winner in sel["destinations"]:
            winners.add(winner);roles_with_winner.add(role)
        afterfb=[f for f in frames if f["start"]>fb["pos"] and f["end"]<=end]
        checks=[ck for f in afterfb[1:3] for ck in opportunity(f,sel)] if role is not None else []
        for ck in checks:
            if ck["pair"][0]==role and ck["opportunity"] and stable:opps.add(tuple(ck["pair"]))
        result["opportunities"]+=checks
        result["arms"].append({"arm":arm,"ticks":[f["tick"] for f in consumed],"primary_winner":winner,"feedback_tick":fb["tick"],"stable":stable,"attention_changes":sum(e["tag"]=="ATT" and ms[0]["pos"]<e["pos"]<=end for e in events),"credit_checks":checks,"cue_pre":[f["cue_pre"] for f in consumed]})
    if idx!=len(pulses):return result
    result["T"]=True
    result["F"]=functional and roles_with_winner=={0,1} and winners==set(sel["destinations"]) and all(f["wta_match"] for f in frames)
    result["O"]=timing and opps=={(role,dest) for role in (0,1) for dest in sel["destinations"]}
    result["opportunity_pairs"]=[list(x) for x in sorted(opps)]
    last=byid[31055]["pos"];result["wash"]=wash([f for f in frames if f["start"]>last])
    result["Q"]=result["wash"] is not None
    return result
def atomic(path,content):
    tmp=path.with_suffix(".new");tmp.write_text(content,encoding="ascii")
    os.replace(tmp,path)
def cdb_path():return pathlib.Path(os.environ["ProgramFiles(x86)"])/"Windows Kits"/"10"/"Debuggers"/"x86"/"cdb.exe"
def fixture(exe):
    exe=pathlib.Path(exe).resolve()
    with tempfile.TemporaryDirectory(prefix="nl-h9-fixture-") as tmp:
        root=pathlib.Path(tmp);log=root/"trace.txt";cmd=root/"commands.txt"
        sel={"concept":[0,1],"destinations":[0,1],"slots":[[0,0,0],[0,1,0],[1,0,1],[1,1,1]]}
        (root/"h9inv.txt").write_text(dump_script(),encoding="ascii")
        for name,data in scripts(sel).items():(root/name).write_text(data,encoding="ascii")
        body="r @$t0=poi(@esp+4); r @$t1=poi(@esp+8); r @$t2=0n11; r @$t3=0; r @$t6=8; r @$t7=0; r @$t8=0x20; "+pr("RB",["1"]+chemistry())+"; $$>a<h9inv.txt; $$>a<h9pre.txt; "+wta("WPRE","WP")+"; $$>a<h9post.txt; "+wta("WPOST","WQ")+"; $$>a<h9after.txt; $$>a<h9concept.txt; "+pr("RP",chemistry())+"; $$>a<h9tpre.txt; $$>a<h9tpost.txt; "+pr("MARK",["0n30999","0"]+cue(sel))+"; "+pr("ATT",["2","1"])+"; "+pr("ALT",["1"])+"; .echo NL_H9_END; qd"
        cmd.write_text('.echo NL_H9_READY\n'+d1.bp(0,body).replace("Creatures+0x0","fixture!nl_tick")+"\ng\n",encoding="ascii")
        rc=None;errs=[];counts={};ok=False;invok=False;frameok=False;failure=None
        try:
            with log.open("wb") as f:p=subprocess.run([str(cdb_path()),"-G","-pd","-cf",str(cmd),str(exe)],cwd=root,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,timeout=45)
            rc=p.returncode;ev,counts,errs=parse(log.read_text(encoding="utf-8",errors="replace"))
            inv=read_inv(root,ev,[{"winner":0}]*12+[{"winner":1}]*12);invok=inv["selected"]==sel and len(inv["rows"])==4096
            fs,bad=collect(ev,sel);frameok=len(fs)==1 and not bad and fs[0]["wta_match"] and fs[0]["stable_slots"]
            ok=rc==0 and not errs and invok and frameok and all(counts.get(t)==1 for t in ("READY","END","TPRE","TPOST","MARK","ATT","ALT"))
        except Exception as ex:failure=str(ex) if type(ex) is RuntimeError and re.fullmatch("[a-z_]+",str(ex)) else type(ex).__name__
    r={"pass":bool(ok),"returncode":rc,"inventory_ok":invok,"frame_ok":frameok,"counts":counts,"diagnostics":errs,"failure":failure}
    pathlib.Path("h09-1-fixture-result.json").write_text(json.dumps(r,indent=2),encoding="utf-8");print("NL_H9_FIXTURE "+json.dumps(r),flush=True);return ok
def trace(pid,root,game,launch,ident):
    cmd=root/"h9.txt";log=root/"h9.log";sel=None;inv=None;error=None;timed=False;rc=None;cleanstop=False;noopp=None
    (game/"h9inv.txt").write_text(dump_script(),encoding="ascii");(game/"h9arm.txt").write_text(".echo h9_wait\n",encoding="ascii")
    cmd.write_text(commands(),encoding="ascii");start=time.monotonic()
    last=([],{},[],[],[])
    def read(final=False):
        nonlocal last
        size=log.stat().st_size+sum(f.stat().st_size for f in game.glob("h9*.bin"))
        if size>CAP:raise RuntimeError("capture_cap")
        raw=log.read_bytes().decode("utf-8","replace")
        ev,ct,err=parse(raw if final else raw[:raw.rfind("\n")+1]);fs,bad=collect(ev,sel)
        last=(ev,ct,err,fs,bad);return last
    def q(s,expected):return launch.query_macro("enum 4 1 0,"+s+",next",expected)
    def send(code,role=None):
        prefix=""
        if role is not None:
            prefix=f"trig 8 {sel['concept'][role]} 32,";RESULT["trig_attempts"]+=1
        row={"code":code,"role":role};RESULT["requests"].append(row);save()
        row["ack"]=q(prefix+f"dde: putv {code}",code);save()
        if not row["ack"].get("ok"):raise RuntimeError("marker_ack")
    with log.open("wb") as output:
        p=subprocess.Popen([str(cdb_path()),"-G","-pd","-p",str(pid),"-cf",str(cmd)],cwd=game,stdin=subprocess.DEVNULL,stdout=output,stderr=subprocess.STDOUT)
        def wait(pred,limit,reason):
            while p.poll() is None and time.monotonic()-start<limit:
                ev,ct,err,fs,bad=read()
                if err or bad:raise RuntimeError("capture_invalid")
                value=pred(ev,fs)
                if value is not None:return value
                time.sleep(.045)
            raise RuntimeError(reason)
        def stop():
            nonlocal cleanstop
            if p.poll() is None:cleanstop=bool(q("dde: putv 31999",31999).get("ok"))
        def getmark(code,limit):
            return wait(lambda ev,fs:next((e for e in ev if e["tag"]=="MARK" and e["v"][0]==code),None),limit,"marker_missing")
        def consume(m,limit):
            return wait(lambda ev,fs:next((f for f in fs if f["start"]>m["pos"]),None),limit,"cycle_missing")
        try:
            ev,fs=wait(lambda ev,fs:(ev,fs) if any(e["tag"]=="INV_END" for e in ev) and len(fs)>=24 else None,55,"inventory_missing")
            base=fs[:24]
            if not all(f["wta_match"] and not f["selected"] for f in base):raise RuntimeError("baseline_invalid")
            inv=read_inv(game,ev,base);sel=inv["selected"]
            if sel is None:noopp="no_common_pair";stop()
            else:
                for name,data in scripts(sel).items():atomic(game/name,data)
                atomic(game/"h9arm.txt","r @$t5=1\n")
                wait(lambda ev,fs:True if basal(fs) else None,75,"initial_basal_missing")
                if not ident():raise RuntimeError("identity_preflight")
                send(30999);pre=getmark(30999,80)
                if pre["v"][1:]!=[0]*5:raise RuntimeError("marker_preflight")
                end=-1
                for i,arm in enumerate(ARMS):
                    wait(lambda ev,fs:True if basal([f for f in fs if f["start"]>end]) else None,165,"arm_basal_missing")
                    if not ident():raise RuntimeError("identity_before")
                    wait(lambda ev,fs:True if basal([f for f in fs if f["start"]>end]) else None,165,"arm_basal_lost")
                    role=None if arm=="S" else (0 if arm=="A" else 1);previous=None
                    for j in range(6):
                        code=31000+10*i+j;send(code,role);m=getmark(code,170)
                        f=consume(m,170)
                        if previous is not None and m["tick"]-previous not in (1,2):raise RuntimeError("slot_cadence")
                        previous=m["tick"]
                    send(32000+i);fb=getmark(32000+i,172)
                    if not 0<=fb["tick"]-f["tick"]<=2:raise RuntimeError("feedback_cadence")
                    post=wait(lambda ev,fs:[x for x in fs if x["start"]>=f["start"]][:9] if len([x for x in fs if x["start"]>=f["start"]])>=9 else None,175,"post_window_missing")
                    end=post[-1]["end"]
                    if not ident():raise RuntimeError("identity_after")
                # No extension beyond approved observation. Observe wash if present.
                try:wait(lambda ev,fs:wash([x for x in fs if x["start"]>m["pos"]]),177,"wash_not_observed")
                except RuntimeError as e:
                    if str(e)!="wash_not_observed":raise
                stop()
        except Exception as e:
            error=str(e) if type(e) is RuntimeError and re.fullmatch("[a-z_]+",str(e)) else type(e).__name__
            try:stop()
            except Exception:pass
        finally:
            if p.poll() is None:
                try:p.wait(timeout=max(.1,min(3,180-(time.monotonic()-start))))
                except subprocess.TimeoutExpired:
                    timed=True;p.terminate()
                    try:p.wait(timeout=3)
                    except subprocess.TimeoutExpired:p.kill();p.wait(timeout=3)
            rc=p.returncode
    try:ev,ct,err,fs,bad=read(True)
    except Exception:ev,ct,err,fs,bad=last;err=err+[{"category":"final_read"}]
    identity=bool(ident())
    a=analyze(ev,fs,sel,RESULT["requests"]) if sel is not None else {"T":False,"F":False,"O":False,"Q":False}
    transport=not(err or bad or timed or error) and rc==0 and ct.get("READY")==ct.get("END")==1 and cleanstop and identity
    passed=bool(transport and all(a.get(k) for k in ("T","F","O","Q")))
    if passed:classification="PASS_feasibility"
    elif transport and noopp:classification="no_opportunity"
    elif transport and a.get("T"):classification="partial_or_no_opportunity"
    elif error in ("initial_basal_missing","arm_basal_missing","arm_basal_lost") and not(err or bad or timed) and cleanstop and identity:classification="no_opportunity_baseline"
    else:classification="instrumental_incomplete"
    # Remove raw pointer values from inventory headers. Do not persist dumps or raw log.
    safe=[{**x,"v":[x["v"][2],x["v"][3]]} if x["tag"]=="INV" else x for x in ev]
    return {"pass":passed,"classification":classification,"analysis":a,"inventory":inv,"events":safe,"frames":fs,"counts":ct,"diagnostics":err,"frame_errors":bad,"observer_error":error,"no_opportunity":noopp,"identity":identity,"transport":transport,"stop_ack":cleanstop,"returncode":rc,"timeout":timed,"trace_ms":round((time.monotonic()-start)*1000),"raw_bytes":log.stat().st_size}
def self_test():
    d1.self_test()
    assert "NL_H9_RB" in commands() and "L0x2800" in dump_script()
    ev,ct,er=parse("NL_H9_MARK 8 00010000 30999 0 0 0 0 0\n")
    assert not er and ev[0]["v"]==[30999,0,0,0,0,0]
    assert parse("NL_H9_MARK 8 00010000 30999 0\n")[2][0]["category"]=="malformed"
    assert parse("NL_H9_ALT 4294967296 00010000 1\n")[2]
    assert parse("NL_H9_OTHER 0 00010000 0\n")[2][0]["tag"]=="unknown"
    assert not collect([{"tag":"RB","tick":8,"brain":"B1","v":[0]+[0]*11,"pos":0}])[0]
    assert not basal([]) and wash([]) is None
    # A nonzero eligibility trace can distinguish virtual reward from actual.
    sel={"concept":[0,1],"destinations":[0,1],"slots":[[0,0,0],[0,1,0],[1,0,1],[1,1,1]]}
    f={"tick":513,"local":[0]*4,"slots":[[],[],[]]}
    for role,dest,slot in sel["slots"]:
        a=[role,dest,slot,role,0,40,0,0,5,0,0]
        z=update_c1_synapse(C1SynapseState(DendriteState(40,0,0),5),DECISION_EXCITATORY_GENE,C1SynapticInput(source_output=0,owner_output=0,owner_state=0),tick=513).after
        b=a.copy();b[5:9]=[z.dendrite.susceptibility,z.dendrite.stw,z.dendrite.ltw,z.strength]
        f["slots"][0].append(a);f["slots"][1].append(b);f["slots"][2].append(b.copy())
    assert all(x["opportunity"] for x in opportunity(f,sel))
    f["slots"][1][0][6]=255;assert not opportunity(f,sel)[0]["opportunity"]
    assert not analyze([],[],sel,[])["T"]
    print("PASS: H09 parser, bounded scripts, WTA, arithmetic opportunity and empty/truncated controls",flush=True)
def main():
    self_test()
    if "--self-test" in sys.argv:return
    if "--fixture" in sys.argv:raise SystemExit(0 if fixture(sys.argv[sys.argv.index("--fixture")+1]) else 1)
    if not json.loads(pathlib.Path("h09-1-fixture-result.json").read_text())["pass"]:raise SystemExit("fixture gate not passed")
    d3.OUT=OUT;d3.RESULT=RESULT;d3.trace=trace
    import h08b_mounted_launch as launch
    save();launch.observe_one_norn=d3.observe;launch.main()
    t=RESULT.get("trace",{});a=t.get("analysis",{});inv=t.get("inventory") or {}
    print("NL_H9_SUMMARY "+json.dumps({"classification":RESULT["classification"],"pass":RESULT["pass"],"subject_created":RESULT["subject_created"],"trig_attempts":RESULT["trig_attempts"],"gates":{k:a.get(k) for k in ("T","F","O","Q")},"selected":inv.get("selected"),"eligible_destinations":inv.get("eligible_destinations"),"frames":len(t.get("frames",[])),"counts":t.get("counts"),"diagnostics":t.get("diagnostics"),"frame_errors":t.get("frame_errors"),"observer_error":t.get("observer_error"),"no_opportunity":t.get("no_opportunity"),"trace_ms":t.get("trace_ms")}),flush=True)
    if not RESULT["pass"]:raise SystemExit(1)
if __name__=="__main__":main()
