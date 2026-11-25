"""D6.1: bounded integrated learning-opportunity pilot, not learning."""
import json, os, pathlib, re, subprocess, sys, tempfile, time
from collections import Counter, defaultdict
import h08d_d1 as d1
import h08d_d3 as d3
import h08d_d4 as d4
import h08d_d5 as d5
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"inherited"))
from experiments.neurolab.c1_synapse_integrated import (C1SynapseState,C1SynapticInput,DECISION_EXCITATORY_GENE,DECISION_INHIBITORY_GENE,update_c1_synapse)
from experiments.neurolab.c1_dendrite_tick import DendriteState
OUT=pathlib.Path("h08d-d6-result.json")
RESULT={"stage":"H08d.D6.1","subject_created":False,"pass":False,"classification":"launcher_not_reached","trig_attempts":0,"reward_pulses":0,"arms":[]}
ARMS=("A","S","B","B","S","A")
CAP=4*1024*1024
BRAIN="@$t0";D="(@$t0+0x4b8)";C="poi(@$t0+0x6e4)"
OWNER="(poi(@$t0+0x554)+@$t10*0x10)"
ARG="$"+"{"+"$arg1"+"}"
def save():OUT.write_text(json.dumps(RESULT,indent=2,sort_keys=True)+"\n",encoding="utf-8")
def pr(tag,args,direct=False):
    s=d3.pr(tag," ".join(["%u","%08x"]+["%u"]*(len(args)-2)),args).replace("NL_D3_","NL_D6_")
    return s.replace("\\\\n","\\n") if direct else s
def mark(tag,v=(),direct=False,tick="@$t1",brain=BRAIN):
    return pr(tag,[tick,brain,*v],direct)
def loop(reg,end,body):
    return f".for (r @$t{reg}=0; @$t{reg}<{end}; r @$t{reg}=@$t{reg}+1) {{ {body} }}"
def source_ok(ptr="@$t19"):
    return f"(({ptr}>={C})&({ptr}<({C}+0x2800))&((({ptr}-{C})&0xf)==0))"
def scan_commands():
    count=f"by({OWNER}+0xc+@$t15)";arr=f"poi({OWNER}+4+@$t15*4)"
    row=mark("DSCAN",["@$t10","@$t15","@$t16",f"((@$t19-{C})/0x10)"]+[f"by(@$t18+{i})" for i in range(6,10)],True)
    bad=mark("DSCAN",["@$t10","@$t15","@$t16","0n999","0","0","0","0"],True)
    each=f"r @$t18={arr}+@$t16*0xc; r @$t19=poi(@$t18); .if {source_ok()} {{ {row} }} .else {{ {bad} }}"
    inner=mark("DCOUNT",["@$t10","@$t15",count],True)+f"; .if (({count}==0)|({arr}!=0)) {{ "+loop(16,count,each)+" } .else { .echo NL_D6_BAD; qd }"
    return loop(10,"0x10",loop(15,"2",inner))+"; "+mark("DSCAN_END",[],True)+"; r @$t14=2\n"
def contact_file(slots):
    packed=[sum(slots.get((dest,j//2,j%2),255)<<(8*j) for j in range(4)) for dest in range(16)]
    setpack="; ".join(f".if (@$t10==0n{i}) {{ r @$t17=0x{p:08x} }}" for i,p in enumerate(packed))
    typ="(@$t15/2)";role="(@$t15&1)"
    count=f"by({OWNER}+0xc+{typ})";arr=f"poi({OWNER}+4+{typ}*4)"
    prefix=["@$t10",typ,role,"@$t16",count]
    args=prefix+[f"((@$t19-{C})/0x10)","by(@$t19+2)"]+[f"by(@$t18+{i})" for i in range(6,10)]+[f"by({OWNER}+2)",f"by({OWNER}+3)"]
    read=mark("SLOT_"+ARG,args,True)
    bad=mark("SLOT_"+ARG,prefix+["0n999"]+["0"]*7,True)
    inner=f"r @$t16=(@$t17>>(@$t15*8))&0xff; .if (@$t16!=0xff) {{ .if ((@$t16<{count})&({arr}!=0)) {{ r @$t18={arr}+@$t16*0xc; r @$t19=poi(@$t18); .if {source_ok()} {{ {read} }} .else {{ {bad} }} }} .else {{ {bad} }} }}"
    result=mark("PHASE_"+ARG,[],True)+"; "+loop(10,"0x10",setpack+"; "+loop(15,"4",inner))+"\n"
    if len(result)>4096:raise RuntimeError("contact_script_too_long")
    return result
def wta(phase):
    meta=mark("W_"+phase,[f"poi({D}+0xa4)",f"by({D}+0x22)",f"poi({D}+0xb0)"])
    row=mark("W_CELL_"+phase,["@$t10",f"by({OWNER}+2)",f"by({OWNER}+3)",f"by({OWNER}+0xe)"])
    return meta+"; "+loop(10,"0x10",row)
def chem(phase):
    n="@esi";brain=f"poi({n}+0x2c18)";tick=f"poi({n}+0x2c20)";p=f"poi({n}+0x2c1c)"
    fields=[f"by({p}+0x{8+2*i:x})" for i in (49,50,51,54,55)]
    fields += [f"by({d4.lobe(brain,6)}+0x{i:x})" for i in range(0xc3,0xc7)]
    fields += [f"by({d4.lobe(brain,8)}+0x{i:x})" for i in range(0xc3,0xc5)]
    return mark("CHEM_"+phase,fields,tick=tick,brain=brain)
def commands():
    base=d4.commands().splitlines()
    finish=d4.bp(0x3cbb,".if (@$t3==1) { "+d4.pr("ENDC","%u %08x",["@$t1","@esi"])+"; r @$t3=0; gc } .else { .echo NL_D4_ORPHAN; qd }")
    base=[finish if x.startswith("bp Creatures+0x3cbb ") else x for x in base[:-1]]
    scan=d5.candidate_scan().replace("|(@$t13==0n640)","")
    def concept(phase):return d5.concept_frame(phase).replace("@$t10<3","@$t10<2")
    def lobe8(body):
        return ".if ((@$t3==1)&(@esi==@$t0)&(@ebp==@$t0+0x648)&(poi(@$t0+0x6ec)==0n640)&(poi(@$t0+0xac)==0n112)) { "+body+" } .else { .echo NL_D6_BAD; qd }"
    pre=".if (@edi==8) { "+lobe8(".if (@$t14==0) { "+scan+" }; "+concept("PRE")+"; gc")+" } .else { gc }"
    post=".if (@edi==8) { "+lobe8(concept("POST")+"; gc")+" } .else { .if ((@edi==6)&(@$t14==2)&(@esi==@$t0)) { $$>a<nl-d6-contacts.txt AFTER; gc } .else { gc } }"
    local=mark("DLOCAL",[f"by({D}+0x{i:x})" for i in range(0xc3,0xc7)])
    dp=".if ((@$t3==1)&(@ecx==@$t0+0x4b8)) { "+local+"; .if (@$t14==1) { $$>a<nl-d6-scan.txt; }; .if (@$t14==2) { $$>a<nl-d6-contacts.txt PRE; }; gc } .else { gc }"
    wp=".if ((@$t3==1)&(@ebx==@$t0+0x4b8)) { "+wta("PRE")+"; .if (@$t14==2) { $$>a<nl-d6-contacts.txt POST; }; gc } .else { gc }"
    wo=".if ((@$t3==1)&(@ebx==@$t0+0x4b8)) { "+wta("POST")+"; gc } .else { gc }"
    rb=chem("PRE")+"; gc"
    rp=".if ((@$t0!=0)&(poi(@esi+0x2c18)==@$t0)) { "+chem("POST")+"; r @$t8=@$t8+1; .if (@$t5==6) { r @$t4=@$t4+1 }; .if (@$t4>=9) { .echo NL_D4_END; qd } .else { .if (@$t8>=0n512) { .echo NL_D4_CAP; qd } .else { gc } } } .else { gc }"
    marker=mark("MARK",["@eax","@$t3"]+d4.values(BRAIN)[10:],tick="poi(poi(@ebx+0xa4)+0x2c20)")
    check=".if ((@$t0!=0)&(poi(@ebx+0xa4)!=0)) { .if (poi(poi(@ebx+0xa4)+0x2c18)==@$t0) { "+marker+"; .if (@eax==0n31999) { .echo NL_D4_END; qd } .else { .if ((@eax>=0n31000)&(@eax<=0n31005)) { r @$t5=@$t5+1 }; gc } } .else { .echo NL_D6_BAD; qd } } .else { .echo NL_D6_BAD; qd }"
    markbp=".if ((@eax==0n30999)|((@eax>=0n31000)&(@eax<=0n31005))|(@eax==0n31999)) { "+check+" } .else { gc }"
    changeguard=".if ((@$t0!=0)&(poi(@esi+0x2c18)==@$t0)) { "
    cp=changeguard+"r @$t18=poi(@esi+0x7f0); r @$t19=poi(@esp); "+mark("CHANGE_PRE",["@ebx","(@$t18!=@$t19)","(@$t18!=0)","(@$t19!=0)"],tick="poi(@esi+0x2c20)")+"; gc } .else { gc }"
    cq=changeguard+mark("CHANGE_POST",["@ebx","(poi(@esi+0x7f0)==@$t19)"],tick="poi(@esi+0x2c20)")+"; gc } .else { gc }"
    rbegin=changeguard+".if (@edi==0) { "+mark("RESET_BEGIN",["poi(@esp)","poi(@esp+4)","poi(@esp+8)"]+d4.cells(BRAIN,5,(8,9)),tick="poi(@esi+0x2c20)")+"; gc } .else { gc } } .else { gc }"
    rend=changeguard+".if (@edi==0x1f) { "+mark("RESET_END",["@edi"]+d4.cells(BRAIN,5,(8,9)),tick="poi(@esi+0x2c20)")+"; gc } .else { gc } } .else { gc }"
    extra=[d3.bp(off,s) for off,s in [(0x3ca1,pre),(0x3caa,post),(0x3e00,dp),(0x48a0,wp),(0x4911,wo),(0x7583,rb),(0x759a,rp),(0x156df,markbp),(0x9cf8,cp),(0x9cfd,cq),(0x9d22,rbegin),(0x9d27,rend)]]
    lines=base+[f"r @$t{i}={'0n640' if i in (11,12,13) else '0'}" for i in range(10,20)]+extra+["g"]
    if any(len(x)>4096 for x in lines):raise RuntimeError("breakpoint_command_too_long")
    return "\n".join(lines)+"\n"

def parse(raw,final=False):
    packet,ct,err=d5.parse(raw,final)
    core=iter(packet["ordered"]);ordered=[];extra=[];aliases={};err=Counter(err)
    lens={"DCOUNT":3,"DSCAN":8,"DSCAN_END":0,"DLOCAL":4,"PHASE_PRE":0,"PHASE_POST":0,"PHASE_AFTER":0,"WAIT":0,"SLOT_PRE":13,"SLOT_POST":13,"SLOT_AFTER":13,"W_PRE":3,"W_POST":3,"W_CELL_PRE":4,"W_CELL_POST":4,"CHEM_PRE":11,"CHEM_POST":11,"MARK":10,"CHANGE_PRE":4,"CHANGE_POST":2,"RESET_BEGIN":7,"RESET_END":5}
    for line in raw.splitlines():
        s=line.strip()
        if s.startswith(("NL_D4_","NL_D5_")):
            try:
                k,x=next(core)
                if s.split()[0][6:]!=x["tag"]:raise ValueError()
                if "brain" in x:
                    a=s.split();ptr=a[1] if x["tag"].startswith("PULSE_") else a[2]
                    alias=aliases.setdefault(ptr.lower(),"B"+str(len(aliases)+1))
                    if alias!=x["brain"]:raise ValueError()
                ordered.append((k,x))
            except (StopIteration,ValueError,IndexError):err["mixed_mapping"]+=1
        elif s.startswith("NL_D6_"):
            a=s.split();tag=a[0][6:]
            try:
                if tag=="BAD" and len(a)==1:err["native_guard"]+=1;continue
                if len(a)!=3+lens[tag] or not a[1].isdigit() or not re.fullmatch("[a-fA-F0-9]{8}",a[2]) or int(a[2],16)==0 or not all(v.isdigit() for v in a[3:]):raise ValueError()
                brain=aliases.setdefault(a[2].lower(),"B"+str(len(aliases)+1))
                x={"tag":tag,"tick":int(a[1]),"brain":brain,"v":list(map(int,a[3:]))}
                extra.append(x);ordered.append(("D6",x))
            except (KeyError,ValueError,IndexError):err["D6_malformed"]+=1
    return {"ordered":ordered,"d5":packet["d5"],"d6":extra,"d4":packet["d4"]},dict(ct),dict(err)

def inventory(packet):
    scan=[x["v"] for x in packet["d5"] if x["tag"]=="SCAN"]
    chosen=d5.select(scan)
    marks=[x for x in packet["d5"] if x["tag"]=="SELECT"]
    if chosen is None or len(marks)!=1 or marks[0]["v"]!=chosen:return None
    if 640 in chosen[:2]:return {"no_opportunity":"concept_candidate_missing","concept":chosen[:2],"concept_scan":scan}
    ends=[x for x in packet["d6"] if x["tag"]=="DSCAN_END"]
    if len(ends)!=1:return None
    counts=[x["v"] for x in packet["d6"] if x["tag"]=="DCOUNT"]
    rows=[x["v"] for x in packet["d6"] if x["tag"]=="DSCAN"]
    if [(x[0],x[1]) for x in counts]!=[(i,j) for i in range(16) for j in range(2)]:return {"invalid":"decision_counts"}
    expected=[(i,j,k) for i,j,n in counts for k in range(n)]
    if [tuple(x[:3]) for x in rows]!=expected or any(not(0<=x[2]<255 and (0<=x[3]<640 or x[3]==999) and all(0<=v<=255 for v in x[4:])) for x in rows):return {"invalid":"decision_scan"}
    if any(n!=128 for _,_,n in counts) or any(x[3]==999 for x in rows):return {"invalid":"decision_layout_or_pointer","rows":rows,"counts":counts}
    slots={}
    for dest,typ,slot,src,sus,stw,ltw,strength in rows:
        if src in chosen[:2] and strength>0:slots.setdefault((dest,typ,chosen[:2].index(src)),slot)
    common=[i for i in range(16) if (i,0,0) in slots and (i,0,1) in slots]
    return {"concept":chosen[:2],"concept_scan":scan,"counts":counts,"rows":rows,"selected":[list(k)+[v] for k,v in sorted(slots.items())],"destinations":common[:2],"all_common":common,**({"no_opportunity":"fewer_than_two_common_destinations"} if len(common)<2 else {})}
def packed_slots(inv):return {tuple(x[:3]):x[3] for x in inv["selected"]}

def collect(packet):
    frames=[];marks=[];pulses=[];changes=[];errors=[];cur=None;pending=None;change=None
    for pos,(k,e) in enumerate(packet["ordered"]):
        tag=e["tag"]
        if k=="D6" and tag=="CHEM_PRE":
            if cur is not None:errors.append("nested_cycle")
            cur={"start":pos,"tick":e["tick"],"brain":e["brain"],"records":defaultdict(list)}
        elif k=="D6" and tag=="CHEM_POST" and cur is None:
            if frames:errors.append("orphan_chem_post")
            continue
        if k=="D4" and tag=="PULSE_PRE":
            if pending is not None or cur is not None:errors.append("pulse_phase")
            pending={"pre":e,"pos":pos}
        elif k=="D4" and tag=="PULSE_POST":
            if pending is None or "post" in pending:errors.append("orphan_pulse")
            else:pending["post"]=e;pulses.append(pending)
        elif k=="D6" and tag=="MARK":
            if cur is not None or e["v"][1]!=0:errors.append("marker_phase")
            marks.append({**e,"pos":pos,"pulse":pending if pending and "post" in pending else None});pending=None
        elif k=="D6" and tag=="CHANGE_PRE":
            if change is not None:errors.append("nested_change")
            change={"pre":e,"pos":pos}
        elif k=="D6" and tag in ("CHANGE_POST","RESET_BEGIN","RESET_END"):
            if change is None or change["pre"]["tick"]!=e["tick"] or change["pre"]["brain"]!=e["brain"]:errors.append("change_pair")
            else:
                expected={"CHANGE_POST":set(["pre","pos"]),"RESET_BEGIN":set(["pre","pos","CHANGE_POST"]),"RESET_END":set(["pre","pos","CHANGE_POST","RESET_BEGIN"])}
                if set(change)!=expected[tag]:errors.append("change_order")
                change[tag]=e
                if tag=="RESET_END":
                    a=change["pre"]["v"];b=change.get("CHANGE_POST",{}).get("v",[]);z=change.get("RESET_BEGIN",{}).get("v",[])
                    if len(b)!=2 or b[0]!=a[0] or a[1]!=1 or b[1]!=1 or z[:3]!=[5,0,0] or e["v"]!=[31,0,0,0,0]:errors.append("reset_bounds")
                    changes.append(change);change=None
        elif cur is not None and tag not in ("READY","END","SCAN","SELECT","DCOUNT","DSCAN","DSCAN_END"):
            if "brain" in e and (e["brain"]!=cur["brain"] or e.get("tick")!=cur["tick"]):errors.append("cycle_identity")
            cur["records"][k+"_"+tag].append(e)
            if k=="D6" and tag=="CHEM_POST":
                cur["end"]=pos;cur["records"]=dict(cur["records"]);frames.append(cur);cur=None
    return frames,marks,pulses,changes,errors
def one(f,k):
    rows=f["records"].get(k,[])
    return rows[0]["v"] if len(rows)==1 else None
def rows(f,k):return [x["v"] for x in f["records"].get(k,[])]
def stable_concept(f,inv):
    p,q=rows(f,"D5_C_PRE"),rows(f,"D5_C_POST")
    if len(p)!=2 or len(q)!=2 or not d5.meta_ok(one(f,"D5_META_PRE") or []) or not d5.meta_ok(one(f,"D5_META_POST") or []):return None
    per=one(f,"D4_PERCEPTION")
    if per is None:return None
    good=True;match=True;positive=[]
    for role,(a,b) in enumerate(zip(p,q)):
        identity=[role,inv["concept"][role],1,0,40+role]
        good=good and a[:5]==b[:5]==identity and a[5]==b[5]==per[14+role*2] and a[8]>0 and b[8]>0 and all(0<=v<=255 for v in a[5:]+b[5:])
        match=match and d5.expected(a)==b[9:11]
        positive.append(b[9])
    return {"stable":bool(good),"match":bool(match),"pre":p,"post":q,"positive":positive}

def frame_check(f,inv,prior=None,opportunity=False):
    r=f["records"]
    order=["D6_CHEM_PRE","D4_LAYOUT","D4_PRE","D4_POST","D4_COPY","D4_PERCEPTION","D6_DLOCAL","D6_PHASE_PRE","D6_SLOT_PRE","D6_W_PRE","D6_W_CELL_PRE","D6_PHASE_POST","D6_SLOT_POST","D6_W_POST","D6_W_CELL_POST","D6_PHASE_AFTER","D6_SLOT_AFTER","D5_META_PRE","D5_C_PRE","D5_META_POST","D5_C_POST","D4_ENDC","D6_CHEM_POST"]
    if list(r)!=order:return None
    d4rows=[r.get("D4_"+k,[]) for k in d4.ORDER]
    if any(len(a)!=1 for a in d4rows):return None
    c=d4.decode_cycles([a[0] for a in d4rows])
    if c is None or c[0]["route"]!="regular":return None
    c=c[0];cp=stable_concept(f,inv)
    if cp is None:return None
    pre=rows(f,"D6_W_CELL_PRE");post=rows(f,"D6_W_CELL_POST")
    pm=one(f,"D6_W_PRE");qm=one(f,"D6_W_POST")
    if pm is None or qm is None or pm[0]!=16 or qm[0]!=16 or len(pre)!=16 or len(post)!=16:return None
    if [a[0] for a in pre]!=list(range(16)) or [a[0] for a in post]!=list(range(16)) or any(not all(0<=v<=255 for v in a[1:]) for a in pre+post):return None
    wmatch=bool(pm[1]&1 and qm[1]&1 and d1.predict([a[1] for a in pre],[a[3] for a in pre],pm[1],pm[2])==[a[1] for a in post])
    winners=[a[0] for a in post if a[1]>0]
    chem0,chem1,local=one(f,"D6_CHEM_PRE"),one(f,"D6_CHEM_POST"),one(f,"D6_DLOCAL")
    if chem0 is None or chem1 is None or local is None or any(not 0<=v<=255 for v in chem0+chem1+local):return None
    slots=packed_slots(inv)
    if any(len(r.get("D6_PHASE_"+k,[]))!=1 for k in ("PRE","POST","AFTER")):return None
    ss=[{tuple(v[:3]):v for v in rows(f,"D6_SLOT_"+k)} for k in ("PRE","POST","AFTER")]
    if any(set(x)!=set(slots) or len(rows(f,"D6_SLOT_"+k))!=len(slots) for x,k in zip(ss,("PRE","POST","AFTER"))):return None
    checks=[];stable=True
    for key,slot in slots.items():
        a,b,z=(x[key] for x in ss);dest,typ,role=key;src=inv["concept"][role]
        ok=all(v[3]==slot and v[4]==128 and v[5]==src and v[10]>0 and all(0<=x<=255 for x in v[6:]) for v in (a,b,z)) and a[6]==b[6]==z[6]
        if prior is not None:ok=ok and a[6]==prior["concept"]["post"][role][9]
        stable=stable and ok
        if not opportunity or not ok or a[6]==0:continue
        gene=(DECISION_EXCITATORY_GENE,DECISION_INHIBITORY_GENE)[typ]
        inp=C1SynapticInput(source_output=a[6],owner_output=a[11],owner_state=a[12],chemicals=tuple(local))
        old=C1SynapseState(DendriteState(*a[7:10]),a[10])
        real=update_c1_synapse(old,gene,inp,tick=f["tick"]).after
        virtualchem=list(local);virtualchem[0]=min(255,virtualchem[0]+32)
        virt=update_c1_synapse(old,gene,C1SynapticInput(source_output=a[6],owner_output=a[11],owner_state=a[12],chemicals=tuple(virtualchem)),tick=f["tick"]).after
        actual=b[7:11];pred=[real.dendrite.susceptibility,real.dendrite.stw,real.dendrite.ltw,real.strength]
        virtual=bool(typ==0 and (old.dendrite.susceptibility>0 or real.dendrite.susceptibility>0) and virt.dendrite.stw>real.dendrite.stw)
        checks.append({"key":list(key),"slot":slot,"input":a[6],"old":a[7:11],"observed":actual,"predicted":pred,"virtual_stw":virt.dendrite.stw,"match":actual==pred,"virtual_opportunity":virtual,"opportunity":virtual and actual==pred})
    return {"tick":f["tick"],"brain":f["brain"],"start":f["start"],"end":f["end"],"sensor":c,"concept":cp,"wta_match":wmatch,"winner":winners[0] if len(winners)==1 else None,"wta_branch":bool(pm[1]&1 and pm[2]),"chem_pre":chem0,"chem_post":chem1,"local":local,"stable":bool(stable),"checks":checks}
def basal(cs):
    return len(cs)>=8 and all(c is not None and c["stable"] and c["concept"]["stable"] and c["concept"]["match"] and c["wta_match"] and d4.zero([c["sensor"]]) and all(v[9:11]==[0,0] for v in c["concept"]["pre"]+c["concept"]["post"]) for c in cs[-8:])
def consistent(cs):
    return bool(cs) and all(c is not None for c in cs) and len({c["brain"] for c in cs})==1 and all(b["tick"]==a["tick"]+1 for a,b in zip(cs,cs[1:]))

def evaluate(packet,inv,final=False):
    fs,marks,pulses,changes,errors=collect(packet)
    checked=[];prior=None
    for f in fs:
        v=frame_check(f,inv,prior,final);checked.append(v);prior=v
    first=next((i for i,c in enumerate(checked) if c is not None),len(checked))
    cs=checked[first:]
    validmarks=[m for m in marks if 31000<=m["v"][0]<=31005]
    r={"classification":"instrumental_incomplete","errors":errors,"selected":inv["selected"],"destinations":inv["destinations"],"complete_cycles":len(fs),"cycles_with_contacts":sum(c is not None for c in cs),"markers":marks,"changes":changes,"arms":[],"ready":False,"pass":False}
    if errors or not cs or not consistent(cs):return r
    if len(validmarks)>6 or [m["v"][0] for m in validmarks]!=list(range(31000,31000+len(validmarks))):return r
    selend=next((i for i,(k,x) in enumerate(packet["ordered"]) if k=="D6" and x["tag"]=="DSCAN_END"),None)
    if selend is None or any(p["pos"]<=selend for p in pulses) or any(m["pos"]<=selend for m in validmarks):return r
    last_end=-1;opp=set();wins=set()
    for i,m in enumerate(validmarks):
        arm=ARMS[i];before=[c for c in cs if last_end<c["start"] and c["end"]<m["pos"]]
        after=[c for c in cs if c["start"]>m["pos"] and (i+1==len(validmarks) or c["end"]<validmarks[i+1]["pos"])]
        role=None if arm=="S" else (0 if arm=="A" else 1)
        expected=[0]*8
        if role is not None:expected[2*role:2*role+2]=[32,32]
        markerok=m["v"][1]==0 and m["v"][2:]==expected and m["brain"]==cs[0]["brain"]
        pulse=m["pulse"]
        if role is None:pulseok=pulse is None
        else:pulseok=bool(pulse and pulse["pre"]["args"]==[5,8+role,32] and pulse["pre"]["in_cycle"]==0 and pulse["pre"]["brain"]==pulse["post"]["brain"]==m["brain"] and pulse["pre"]["v"][10:]==[0]*8 and pulse["post"]["v"][10:]==expected and pulse["pos"]<m["pos"])
        window=after[:9];b=basal(before)
        record={"arm":arm,"marker":m["v"][0],"basal":b,"marker_ok":bool(markerok),"pulse_ok":bool(pulseok),"cycles":len(window),"signature":None,"winners":[],"opportunity":[],"reset_count":None,"pass":False}
        r["arms"].append(record)
        if not(b and markerok and pulseok) or len(window)<9:return r
        last_end=window[-1]["end"]
        record["reset_count"]=sum(m["pos"]<x["pos"]<=last_end for x in changes)
        record["ticks"]=[x["tick"] for x in window]
        record["sensor_passive_matches"]=None if role is None else sum(all(x["sensor"][k]==y[k] for k in y) for x,y in zip(window,d4.prediction(8+role)))
        record["concept_outputs"]=[x["concept"]["positive"] for x in window]
        record["chemistry"]=[{"tick":x["tick"],"pre":x["chem_pre"],"post":x["chem_post"],"decision":x["local"]} for x in window]
        valid=all(x["concept"]["stable"] and x["concept"]["match"] and x["stable"] and x["wta_match"] for x in window)
        if not valid:record["structural_or_prediction_divergence"]=True
        if role is None:signature=all(x["concept"]["positive"]==[0,0] for x in window)
        else:
            signature=any(x["concept"]["positive"][role]>0 for x in window[:4]) and all(x["concept"]["positive"][1-role]==0 for x in window)
            start=next((j for j,x in enumerate(window[:4]) if x["concept"]["positive"][role]>0),None)
            relevant=window[start+1:start+5] if start is not None else []
            for x in relevant:
                if x["winner"] in inv["destinations"] and x["wta_branch"]:wins.add(x["winner"])
                for ck in x["checks"]:
                    dest,typ,cr=ck["key"]
                    if cr==role and dest in inv["destinations"]:
                        if ck["opportunity"]:opp.add((role,dest));record["opportunity"].append({"tick":x["tick"],**ck})
                        if ck["virtual_opportunity"] and not ck["match"]:record["structural_or_prediction_divergence"]=True
        record["signature"]=bool(signature);record["winners"]=[x["winner"] for x in window]
        record["pass"]=bool(valid and signature and not record.get("structural_or_prediction_divergence"))
        if final:record["contact_predictions"]=[{"tick":x["tick"],"checks":x["checks"]} for x in window]
    if len(validmarks)<6:
        tail=[c for c in cs if c["start"]>last_end and (not validmarks or c["start"]>validmarks[-1]["pos"])]
        r["ready"]=basal(tail)
    else:
        required={(role,dest) for role in (0,1) for dest in inv["destinations"]}
        r["opportunity_pairs"]=[list(x) for x in sorted(opp)]
        r["required_pairs"]=[list(x) for x in sorted(required)]
        r["distinct_eligible_winners"]=sorted(wins)
        r["pass"]=bool(all(a["pass"] for a in r["arms"]) and len(r["arms"])==6 and opp>=required and wins==set(inv["destinations"]) and len(pulses)==4)
        r["classification"]="PASS_integrated_opportunity" if r["pass"] else ("observed_divergence" if any(a.get("structural_or_prediction_divergence") for a in r["arms"]) else "no_opportunity")
    if final:r["frames"]=cs
    return r

def atomic(path,content):
    tmp=path.with_suffix(".new");tmp.write_text(content,encoding="ascii")
    for i in range(20):
        try:os.replace(tmp,path);return
        except PermissionError:time.sleep(.025)
    raise RuntimeError("contact_script_replace")
def cdb_path():return pathlib.Path(os.environ["ProgramFiles(x86)"])/"Windows Kits"/"10"/"Debuggers"/"x86"/"cdb.exe"
def fixture(exe):
    exe=pathlib.Path(exe).resolve()
    with tempfile.TemporaryDirectory(prefix="nl-d6-fixture-") as td:
        root=pathlib.Path(td);cmd=root/"commands.txt";log=root/"trace.txt"
        (root/"nl-d6-fixture.txt").write_text('.printf "NL_D6_FIX '+ARG+' %u %u\\n", poi(@esp+4), ((0x12345678>>0x18)&0xff)\n',encoding="ascii")
        body='.if (@$t0<3) { $$>a<nl-d6-fixture.txt PRE; r @$t0=@$t0+1; .if (@$t0==3) { .echo NL_D6_FIX_END; qd } .else { gc } } .else { qd }'
        cmd.write_text('r @$t0=0\nbp fixture!nl_tick "'+body+'"\ng\n',encoding="ascii")
        try:
            with log.open("wb") as f:p=subprocess.run([str(cdb_path()),"-G","-pd","-cf",str(cmd),str(exe)],cwd=root,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,timeout=30)
            lines=[s.strip() for s in log.read_text(encoding="utf-8",errors="replace").splitlines() if s.strip().startswith("NL_D6_FIX")]
            rc=p.returncode
        except subprocess.TimeoutExpired:lines=[];rc=None
    result={"stage":"D6_fixture","returncode":rc,"markers":lines,"pass":rc==0 and lines==["NL_D6_FIX PRE 11 18","NL_D6_FIX PRE 22 18","NL_D6_FIX PRE 33 18","NL_D6_FIX_END"]}
    pathlib.Path("h08d-d6-fixture-result.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print("NL_D6_FIXTURE "+json.dumps(result),flush=True)
    return result["pass"]

def trace(pid,root,game,launch,ident):
    cmd=root/"d6.txt";log=root/"d6.log";contacts=game/"nl-d6-contacts.txt";scan=game/"nl-d6-scan.txt"
    for path in (contacts,scan):
        if path.exists():raise RuntimeError("observer_file_collision")
    contacts.write_text(mark("WAIT",[],True)+"\n",encoding="ascii");scan.write_text(scan_commands(),encoding="ascii")
    cmd.write_text(commands(),encoding="ascii")
    start=time.monotonic();inv=None;error=None;stopped=False;timed=False;preflight=False
    def read(final=False):
        if log.stat().st_size>CAP:raise RuntimeError("capture_cap")
        raw=log.read_bytes().decode("utf-8","replace")
        return parse(raw if final else raw[:raw.rfind("\n")+1],final)
    def q(s,expected=None,kind="number"):return launch.query_macro("enum 4 1 0,"+s+",next",expected,kind)
    def stop():
        nonlocal stopped
        if p.poll() is None:stopped=bool(q("dde: putv 31999",31999).get("ok"))
    with log.open("wb") as f:
        p=subprocess.Popen([str(cdb_path()),"-G","-pd","-p",str(pid),"-cf",str(cmd)],cwd=game,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT)
        try:
            while p.poll() is None and time.monotonic()-start<55:
                packet,ct,err=read()
                if err:raise RuntimeError("capture_invalid")
                inv=inventory(packet)
                if inv is not None:break
                time.sleep(.15)
            if inv is None:
                packet,ct,err=read();inv=inventory(packet)
            if inv is None:raise RuntimeError("inventory_not_observed")
            if inv.get("invalid"):raise RuntimeError("inventory_invalid")
            if inv.get("no_opportunity"):stop()
            else:
                atomic(contacts,contact_file(packed_slots(inv)))
                while p.poll() is None and time.monotonic()-start<80:
                    packet,ct,err=read();a=evaluate(packet,inv)
                    if not err and a["ready"]:break
                    time.sleep(.2)
                else:raise RuntimeError("initial_basal_not_observed")
                if not ident() or not q("dde: putv 30999",30999).get("ok"):raise RuntimeError("marker_preflight_ack")
                while p.poll() is None and time.monotonic()-start<90:
                    packet,ct,err=read()
                    ms=[x for x in packet["d6"] if x["tag"]=="MARK" and x["v"][0]==30999]
                    if not err and len(ms)==1 and ms[0]["v"][1:]==[0]+[0]*8:preflight=True;break
                    time.sleep(.1)
                if not preflight:raise RuntimeError("marker_preflight_missing")
                for i,arm in enumerate(ARMS):
                    while p.poll() is None and time.monotonic()-start<165:
                        packet,ct,err=read();a=evaluate(packet,inv)
                        if err:raise RuntimeError("capture_invalid")
                        if a["ready"] and len(a["arms"])==i:break
                        time.sleep(.2)
                    else:raise RuntimeError("basal_or_window_not_observed")
                    row={"arm":arm,"marker":31000+i,"identity_before":bool(ident())};RESULT["arms"].append(row)
                    if not row["identity_before"]:raise RuntimeError("identity_before")
                    row["dde_basal"]=[q("dde: cell 5 8 0",kind="cell"),q("dde: cell 5 9 0",kind="cell")]
                    if not all(x.get("ok") and len(x.get("value",[]))==7 and x["value"][:2]==[0,0] for x in row["dde_basal"]):raise RuntimeError("dde_basal_not_zero")
                    packet,ct,err=read();a=evaluate(packet,inv)
                    if err or not a["ready"] or len(a["arms"])!=i or p.poll() is not None or time.monotonic()-start>=170:raise RuntimeError("basal_lost")
                    prefix="" if arm=="S" else f"trig 5 {8 if arm=='A' else 9} 32,"
                    if arm!="S":RESULT["trig_attempts"]+=1
                    save();row["ack"]=q(prefix+f"dde: putv {31000+i}",31000+i);save()
                    if not row["ack"].get("ok"):raise RuntimeError("marker_ack")
                    row["identity_after"]=bool(ident());save()
                    if not row["identity_after"]:raise RuntimeError("identity_after")
                while p.poll() is None and time.monotonic()-start<180:
                    if log.stat().st_size>CAP:raise RuntimeError("capture_cap")
                    time.sleep(.15)
                timed=p.poll() is None
        except Exception as e:
            error=str(e) if type(e) is RuntimeError and re.fullmatch("[a-z_]+",str(e)) else type(e).__name__
            try:stop()
            except Exception:pass
        finally:
            if p.poll() is None:
                try:p.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    p.terminate()
                    try:p.wait(timeout=5)
                    except subprocess.TimeoutExpired:p.kill();p.wait(timeout=5)
    raw=log.read_bytes()[:CAP].decode("utf-8","replace")
    packet,ct,err=parse(raw,True)
    if log.stat().st_size>CAP:err["capture_cap"]=1
    inv=inventory(packet) if inv is None else inv
    ids=bool(ident()) and all(x.get("identity_before") and x.get("identity_after") for x in RESULT["arms"])
    a=evaluate(packet,inv,True) if inv and not(inv.get("invalid") or inv.get("no_opportunity")) else {"pass":False,"classification":"no_opportunity" if inv and inv.get("no_opportunity") else "instrumental_incomplete"}
    transport=not err and not timed and p.returncode==0 and ct.get("READY")==ct.get("END")==1
    passed=bool(transport and ids and preflight and len(RESULT["arms"])==6 and all(x.get("ack",{}).get("ok") for x in RESULT["arms"]) and not error and a["pass"])
    classification=a["classification"] if (transport and ids and not error) or (inv and inv.get("no_opportunity") and not err and p.returncode==0 and not RESULT["arms"]) else "instrumental_incomplete"
    return {"pass":passed,"classification":classification,"gate_checks":{"transport":transport,"identity":ids,"preflight":preflight,"complete_opportunity":a["pass"]},"inventory":inv,"analysis":a,"events":packet,"event_counts":ct,"diagnostics":err,"observer_error":error,"timeout":timed,"returncode":p.returncode,"raw_bytes":log.stat().st_size,"elapsed_ms":round((time.monotonic()-start)*1000),"stop_ack":stopped}

def self_test():
    d1.self_test();d4.self_test();d5.self_test()
    scan=[[i,2,0,999,0,0] for i in range(640)]
    scan[3]=[3,1,0,40,128,5];scan[5]=[5,1,0,41,128,5]
    d5e=[{"tag":"SCAN","v":v} for v in scan]+[{"tag":"SELECT","v":[3,5,640]}]
    de=[]
    for i in range(16):
        for j in range(2):
            de.append({"tag":"DCOUNT","v":[i,j,128]})
            for k in range(128):
                src=3 if k in (0,3) and i<2 else 5 if k==1 and i<2 else 100
                de.append({"tag":"DSCAN","v":[i,j,k,src,0,0,0,5]})
    de.append({"tag":"DSCAN_END","v":[]})
    inv=inventory({"d5":d5e,"d6":de})
    assert inv["concept"]==[3,5] and inv["destinations"]==[0,1] and packed_slots(inv)[(0,0,0)]==0 and packed_slots(inv)[(1,1,1)]==1
    assert inventory({"d5":d5e,"d6":de[:-2]+de[-1:]})["invalid"]=="decision_scan"
    assert "NL_D6_SLOT_" in contact_file(packed_slots(inv))
    assert len(scan_commands())<=4096 and "NL_D6_DSCAN_END" in scan_commands()
    assert "NL_D6_MARK" in commands()
    assert not basal([]) and not consistent([])
    packet,ct,err=parse("NL_D6_MARK 4 00010000 30999 0 0 0 0 0 0 0 0 0\n")
    assert not err and packet["d6"][0]["v"][0]==30999
    print("PASS: D6 synthetic inventory, corruption, script size, marker parser and inherited arithmetic",flush=True)
def main():
    self_test()
    if "--self-test" in sys.argv:return
    if "--fixture" in sys.argv:raise SystemExit(0 if fixture(sys.argv[sys.argv.index("--fixture")+1]) else 1)
    if not json.loads(pathlib.Path("h08d-d6-fixture-result.json").read_text(encoding="utf-8")).get("pass"):raise SystemExit("fixture gate not passed")
    d3.OUT=OUT;d3.RESULT=RESULT;d3.trace=trace
    import h08b_mounted_launch as launch
    save();launch.observe_one_norn=d3.observe;launch.main()
    t=RESULT.get("trace",{});a=t.get("analysis",{});inv=t.get("inventory") or {}
    print("NL_D6_SUMMARY "+json.dumps({"classification":RESULT["classification"],"pass":RESULT["pass"],"subject_created":RESULT["subject_created"],"trig_attempts":RESULT["trig_attempts"],"gate_checks":t.get("gate_checks"),"diagnostics":t.get("diagnostics"),"observer_error":t.get("observer_error"),"concept":inv.get("concept"),"destinations":inv.get("destinations"),"no_opportunity":inv.get("no_opportunity"),"arms":[{k:v for k,v in row.items() if k not in ("contact_predictions","chemistry","opportunity")} for row in a.get("arms",[])],"opportunity_pairs":a.get("opportunity_pairs"),"distinct_eligible_winners":a.get("distinct_eligible_winners"),"elapsed_ms":t.get("elapsed_ms")}),flush=True)
    if not RESULT["pass"]:raise SystemExit(1)
if __name__=="__main__":main()
