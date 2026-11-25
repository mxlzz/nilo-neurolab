"""D5.1: topologically preselected singleton Concept witnesses; extends D4."""
import json,pathlib,re,sys
from collections import Counter
import h08d_d4 as d4
import h08d_d3 as d3
OUT=pathlib.Path("h08d-d5-result.json")
RESULT={"stage":"H08d.D5.1","subject_created":False,"pass":False,"classification":"launcher_not_reached","trig_attempts":0,"reward_pulses":0,"arms":[]}
BASE_COMMANDS=d4.commands;BASE_PARSE=d4.parse;BASE_ANALYZE=d4.analyze
def save():OUT.write_text(json.dumps(RESULT,indent=2,sort_keys=True)+"\n",encoding="utf-8")
def pr(tag,args):
    fmt=" ".join(["%08x" if i==1 and tag in ("META_PRE","META_POST","C_PRE","C_POST","SELECT","CONTACT_BAD") else "%u" for i in range(len(args))])
    return d3.pr(tag,fmt,args).replace("NL_D3_","NL_D5_")
def cbase():return "poi(@$t0+0x6e4)"
def pbase():return "poi(@$t0+0xa4)"
def valid_source():
    return "((@$t18>=@$t17)&(@$t18<(@$t17+0x700))&(((@$t18-@$t17)&0xf)==0))"
def candidate_scan():
    # All 640 cell counts recorded; weights read only for valid singletons.
    count0="by(@$t15+0xc)";count1="by(@$t15+0xd)"
    bad=pr("SCAN",["@$t10",count0,count1,"0n999","0","0"])
    good=pr("SCAN",["@$t10",count0,count1,"@$t19","by(@$t16+7)","by(@$t16+9)"])
    choose=".if ((by(@$t16+7)>=0n24)&(by(@$t16+9)>0)) { .if (@$t19==0n40) { .if (@$t11==0n640) { r @$t11=@$t10 } } .else { .if (@$t19==0n41) { .if (@$t12==0n640) { r @$t12=@$t10 } } .else { .if (@$t13==0n640) { r @$t13=@$t10 } } } }"
    source=f"r @$t18=poi(@$t16); .if {valid_source()} {{ r @$t19=(@$t18-@$t17)/0x10; {good}; {choose} }} .else {{ {bad} }}"
    body=f"r @$t15={cbase()}+@$t10*0x10; .if (({count0}==1)&({count1}==0)) {{ r @$t16=poi(@$t15+4); .if (@$t16!=0) {{ {source} }} .else {{ {bad} }} }} .else {{ {bad} }}"
    select=pr("SELECT",["@$t1","@$t0","@$t11","@$t12","@$t13"])
    return f"r @$t17={pbase()}; .for (r @$t10=0; @$t10<0n640; r @$t10=@$t10+1) {{ {body} }}; {select}; r @$t14=1; .if ((@$t11==0n640)|(@$t12==0n640)|(@$t13==0n640)) {{ .echo NL_D5_NO_OPPORTUNITY; qd }}"
def concept_frame(phase):
    l="(@$t0+0x648)"
    args=["@$t1","@$t0",f"poi({l}+0xa4)"]+[f"by({l}+0x{x:x})" for x in (0x14,0x15,0x16,0x17,0x22,*range(0x18,0x20),0xc3,0xc4)]
    meta=pr("META_"+phase,args)
    idx=f"((@$t15-{cbase()})/0x10)"
    counts=["by(@$t15+0xc)","by(@$t15+0xd)"]
    bad=pr("CONTACT_BAD",["@$t1","@$t0","@$t10",idx,*counts])
    row=pr("C_"+phase,["@$t1","@$t0","@$t10",idx,*counts,"((@$t18-@$t17)/0x10)","by(@$t18+2)","by(@$t16+7)","by(@$t16+8)","by(@$t16+9)","by(@$t15+2)","by(@$t15+3)"])
    valid=f"r @$t18=poi(@$t16); .if {valid_source()} {{ {row} }} .else {{ {bad}; qd }}"
    read=f".if (({counts[0]}==1)&({counts[1]}==0)) {{ r @$t16=poi(@$t15+4); .if (@$t16!=0) {{ {valid} }} .else {{ {bad}; qd }} }} .else {{ {bad}; qd }}"
    choose=f".if (@$t10==0) {{ r @$t15={cbase()}+@$t11*0x10 }} .else {{ .if (@$t10==1) {{ r @$t15={cbase()}+@$t12*0x10 }} .else {{ r @$t15={cbase()}+@$t13*0x10 }} }}"
    return f"{meta}; r @$t17={pbase()}; .for (r @$t10=0; @$t10<3; r @$t10=@$t10+1) {{ {choose}; {read} }}"
def commands():
    base=BASE_COMMANDS().splitlines()
    init=[f"r @$t{i}={('0n640' if i in (11,12,13) else '0')}" for i in range(10,20)]
    scan=candidate_scan()
    pre=f".if (@$t14==0) {{ .if (@$t2==0x407588) {{ {scan} }} .else {{ .echo NL_D5_ROUTE_BAD; qd }} }}; "+concept_frame("PRE")+"; gc"
    # Explicit identity and bounds before reading cell arrays.
    def guard(body):
        return ".if (@edi==8) { .if ((@$t3==1)&(@esi==@$t0)&(@ebp==@$t0+0x648)&(poi(@$t0+0x6ec)==0n640)&(poi(@$t0+0xac)==0n112)) { "+body+" } .else { .echo NL_D5_LAYOUT_BAD; qd } } .else { gc }"
    # EBP is the lobe pointer both before and after the callee (callee saves EBP).
    bps=[d3.bp(0x3ca1,guard(pre)),d3.bp(0x3caa,guard(concept_frame("POST")+"; gc"))]
    return "\n".join(base[:-1]+init+bps+["g"])+"\n"
def parse(raw,final=True):
    ev,ct,err=BASE_PARSE(raw,final)
    # Map private runtime addresses to the same aliases assigned by D4 parser.
    aliases={};ordered=[];extra=[];i=0;counts=Counter()
    def brain(x):
        if not re.fullmatch("[0-9a-fA-F]{8}",x) or int(x,16)==0:raise ValueError()
        return aliases.setdefault(x.lower(),"B"+str(len(aliases)+1))
    def nums(a):
        if not all(x.isdigit() for x in a):raise ValueError()
        return list(map(int,a))
    for line in raw.splitlines():
        s=line.strip()
        if s.startswith("NL_D4_"):
            a=s.split();tag=a[0][6:]
            try:
                if tag in d4.ORDER or tag in ("PULSE_PRE","PULSE_POST"):
                    brain(a[1] if tag.startswith("PULSE_") else a[2])
                if i<len(ev) and ev[i]["tag"]==tag:
                    ordered.append(("D4",ev[i]));i+=1
            except (ValueError,IndexError):err["D5_alias"]=1
        elif s.startswith("NL_D5_"):
            a=s.split();tag=a[0][6:];counts[tag]+=1
            try:
                if tag=="SCAN" and len(a)==7:r={"tag":tag,"v":nums(a[1:])}
                elif tag in ("NO_OPPORTUNITY","LAYOUT_BAD","ROUTE_BAD") and len(a)==1:r={"tag":tag}
                elif tag in ("META_PRE","META_POST","C_PRE","C_POST","SELECT","CONTACT_BAD"):
                    n={"META_PRE":19,"META_POST":19,"C_PRE":11,"C_POST":11,"SELECT":3,"CONTACT_BAD":4}[tag]
                    # meta: count, 5 parameters, 8 rule bytes, 2 CHEM =16 values
                    if tag.startswith("META_"):n=16
                    # candidate: role,index,count0,count1,source,sourceout,STW,LTW,strength,output,state =11
                    if len(a)!=3+n:raise ValueError()
                    r={"tag":tag,"tick":nums(a[1:2])[0],"brain":brain(a[2]),"v":nums(a[3:])}
                else:raise ValueError()
                extra.append(r);ordered.append(("D5",r))
            except (ValueError,IndexError):err["D5_malformed_marker"]=err.get("D5_malformed_marker",0)+1
    if i!=len(ev):err["D5_order_mapping"]=1
    return {"d4":ev,"d5":extra,"ordered":ordered},ct,err
def select(scan):
    if len(scan)!=640 or [x[0] for x in scan]!=list(range(640)):return None
    for _,c0,c1,src,w,strength in scan:
        if not(0<=c0<=255 and 0<=c1<=255 and 0<=w<=255 and 0<=strength<=255):return None
        if src!=999 and not(c0==1 and c1==0 and 0<=src<112):return None
        if src==999 and (w or strength):return None
    eligible=[r for r in scan if r[1:3]==[1,0] and r[3]<112 and r[4]>=24 and r[5]>0]
    return [next((r[0] for r in eligible if p(r[3])),640) for p in (lambda x:x==40,lambda x:x==41,lambda x:x not in (40,41))]
def meta_ok(v):
    return len(v)==16 and v[:5]==[640,0,8,0,255] and 0<=v[5]<=255 and not(v[5]&1) and v[6:14]==[14,0,0,0,0,0,0,0] and all(0<=x<=255 for x in v[14:])
def expected(row):
    x,w=row[5:7];out=((x*w)>>8)*255>>8
    return [out,(out*12965)>>16]
def concept_analysis(packet,base,final):
    extra=packet["d5"];ordered=packet["ordered"]
    scan=[x["v"] for x in extra if x["tag"]=="SCAN"]
    chosen=select(scan);marks=[x for x in extra if x["tag"]=="SELECT"]
    r={"scan":scan,"selected":chosen,"selection_verified":False,"frames":[],"arms":[],"basal_ready":False,"complete":False,"classification":"instrumental_incomplete_or_no_opportunity"}
    if any(x["tag"]=="NO_OPPORTUNITY" for x in extra):
        if chosen is not None and 640 in chosen and len(marks)==1 and marks[0]["v"]==chosen:r["classification"]="no_opportunity"
        return r
    if chosen is None or 640 in chosen or len(marks)!=1 or marks[0]["v"]!=chosen:return r
    if any(x["tag"] in ("CONTACT_BAD","LAYOUT_BAD","ROUTE_BAD") for x in extra):
        r["classification"]="structural_or_layout_incomplete";return r
    # Inventory/selection must precede any pulse; at first regular Concept PRE.
    selpos=next((i for i,(k,x) in enumerate(ordered) if k=="D5" and x["tag"]=="SELECT"),-1)
    firstpulse=next((i for i,(k,x) in enumerate(ordered) if k=="D4" and x["tag"]=="PULSE_PRE"),len(ordered))
    if selpos<640 or selpos>=firstpulse or any(k!="D5" or x["tag"]!="SCAN" for k,x in ordered[selpos-640:selpos]):return r
    r["selection_verified"]=True
    allc=[c for s in base.get("segments",[]) for c in s]
    if not allc:return r
    if marks[0]["tick"]!=allc[0]["tick"] or marks[0]["brain"]!=allc[0]["brain"]:return r
    sources=[scan[i][3] for i in chosen]
    # Index mixed stream once, require exact phase placement in each complete cycle.
    blocks={};active=None;bad=False
    for k,x in ordered:
        if k=="D4" and x["tag"]=="PERCEPTION":
            if active is not None:bad=True
            active=(x["tick"],x["brain"]);blocks[active]=[]
        elif k=="D4" and x["tag"]=="ENDC":
            if active!=(x["tick"],x["brain"]):bad=True
            active=None
        elif k=="D5" and x["tag"] in ("META_PRE","C_PRE","META_POST","C_POST"):
            if active!=(x["tick"],x["brain"]):bad=True
            else:blocks[active].append(x)
    if bad or (final and active is not None):return r
    structural=False;divergence=False
    for c in allc:
        rows=blocks.get((c["tick"],c["brain"]),[])
        if [x["tag"] for x in rows]!=["META_PRE","C_PRE","C_PRE","C_PRE","META_POST","C_POST","C_POST","C_POST"]:return r
        if not meta_ok(rows[0]["v"]) or not meta_ok(rows[4]["v"]):return r
        pre=[x["v"] for x in rows[1:4]];post=[x["v"] for x in rows[5:8]]
        pairs=[]
        for role,(a,b) in enumerate(zip(pre,post)):
            identity=all(x[:5]==[role,chosen[role],1,0,sources[role]] for x in (a,b))
            bytevalid=all(len(x)==11 and all(0<=v<=255 for v in x[5:]) for x in (a,b))
            stable=identity and bytevalid and a[8]>0 and b[8]>0 and a[5]==b[5]
            if role<2:stable=stable and a[5]==c["perception"][4+2*role]
            exp=expected(a)
            match=stable and b[9:11]==exp
            pairs.append({"role":role,"pre":a,"post":b,"expected":exp,"stable":stable,"match":match})
            structural|=not stable
        r["frames"].append({"tick":c["tick"],"brain":c["brain"],"chem_pre":rows[0]["v"][14:],"chem_post":rows[4]["v"][14:],"pairs":pairs})
    if structural:r["classification"]="structural_or_layout_incomplete";return r
    frames={f["tick"]:f for f in r["frames"]}
    def zero(cycles):
        return all(all(p["pre"][9:]==p["post"][9:]==[0,0] for p in frames[c["tick"]]["pairs"][:2]) for c in cycles)
    seg=base["segments"]
    if len(seg[0])>=8 and not zero(seg[0][-8:]):return r
    for i,arm in enumerate(base.get("arms",[])):
        if arm.get("cycles",0)<9:return r
        cs=[frames[c["tick"]] for c in arm["observed"]]
        matches=[sum(f["pairs"][j]["match"] for f in cs) for j in range(3)]
        positives=[sum(f["pairs"][j]["post"][9]>0 for f in cs) for j in range(3)]
        passed=matches==[9,9,9] and positives[i]>=1 and positives[1-i]==0
        r["arms"].append({"cell":8+i,"matched":matches,"positive":positives,"pass":passed})
        if not passed:
            r["classification"]="observed_conditional_divergence" if matches!=[9,9,9] or positives[1-i] else "no_opportunity"
            return r
    if len(seg)>1 and len(seg[1])>=17 and not zero(seg[1][-8:]):return r
    r["basal_ready"]=bool(base.get("basal_ready") and ((len(seg)==1 and len(seg[0])>=8 and zero(seg[0][-8:])) or (len(seg)==2 and len(r["arms"])==1 and len(seg[1])>=17 and zero(seg[1][-8:]))))
    r["complete"]=bool(base.get("complete") and len(r["arms"])==2 and all(x["pass"] for x in r["arms"]) and len(seg[1])>=17 and zero(seg[1][9:]))
    if r["complete"]:r["classification"]="PASS_local_concept_representation"
    return r
def analyze(packet,final=False):
    base=BASE_ANALYZE(packet["d4"],final);r=concept_analysis(packet,base,final)
    base["concept"]=r
    base["basal_ready"]=bool(base.get("basal_ready") and r["basal_ready"])
    base["complete"]=bool(base.get("complete") and r["complete"])
    if r["classification"]!="instrumental_incomplete_or_no_opportunity":base["classification"]=r["classification"]
    elif not base["complete"] and base["classification"]=="PASS_local_propagation":base["classification"]=r["classification"]
    return base
def self_test():
    d4.self_test()
    scan=[[i,2,0,999,0,0] for i in range(640)]
    scan[3]=[3,1,0,40,128,5];scan[5]=[5,1,0,41,128,5];scan[7]=[7,1,0,12,128,5];scan[9]=[9,1,0,40,128,5]
    assert select(scan)==[3,5,7] and select(scan[:-1]) is None
    assert select([[i,2,0,999,0,0] for i in range(640)])==[640]*3
    assert expected([0,3,1,0,40,22,128,128,5,0,0])==[10,1]
    assert expected([0,3,1,0,40,22,24,128,5,0,0])==[1,0]
    meta=[640,0,8,0,255,0,14,0,0,0,0,0,0,0,0,0]
    assert meta_ok(meta)
    # Full synthetic two-arm mixed-stream fixture, same parser/gates as live.
    raw=["NL_D4_READY"];tick=0;previous=[[0,0]]*3
    dmeta=[32,0,24,0,0,112,10,0,0,0]
    z={k:[0]*8 for k in ("pre","post","copy","perception")}
    def nums(v):return " ".join(map(str,v))
    def trip(v):
        nonlocal tick,previous
        raw.append(f"NL_D4_LAYOUT {tick} 00010000 00407588 "+nums([9]+d4.COUNTS+d4.FLAGS))
        for tag in d4.ORDER[1:5]:raw.append(f"NL_D4_{tag} {tick} 00010000 00407588 "+nums(dmeta+v[tag.lower()]))
        if tick==0:
            raw.extend("NL_D5_SCAN "+nums(s) for s in scan);raw.append("NL_D5_SELECT 0 00010000 3 5 7")
        rows=[]
        for role,idx,src,x in ((0,3,40,v["perception"][4]),(1,5,41,v["perception"][6]),(2,7,12,0)):
            a=[role,idx,1,0,src,x,128,128,5]+previous[role]
            b=a[:9]+expected(a);rows.append((a,b))
        for phase,which in (("PRE",0),("POST",1)):
            raw.append(f"NL_D5_META_{phase} {tick} 00010000 "+nums(meta))
            raw.extend(f"NL_D5_C_{phase} {tick} 00010000 "+nums(row[which]) for row in rows)
        previous=[row[1][9:] for row in rows];raw.append(f"NL_D4_ENDC {tick} 00010000");tick+=1
    def check(lines,final=False):
        e,ct,err=parse("\n".join(lines));assert not err,err
        return analyze(e,final)
    for cell in (8,9):
        for _ in range(8):trip(z)
        assert check(raw)["basal_ready"]
        p=[0]*8;p[2*(cell-8):2*(cell-8)+2]=[32,32]
        raw.extend([f"NL_D4_PULSE_PRE 00010000 5 {cell} 32 0 "+nums(dmeta+[0]*8),"NL_D4_PULSE_POST 00010000 "+nums(dmeta+p)])
        for v in d4.prediction(cell):trip(v)
    raw.append("NL_D4_END")
    assert check(raw,True)["complete"]
    bad=[line[:-1]+"1" if line.startswith("NL_D5_C_POST 8 00010000 1 ") else line for line in raw]
    assert not check(bad,True)["complete"]
    missing=[line for line in raw if not line.startswith("NL_D5_SCAN 5 ")]
    assert not check(missing,True)["complete"]
    noopp=raw[:1]+["NL_D5_SCAN "+nums([i,2,0,999,0,0]) for i in range(640)]+["NL_D5_SELECT 0 00010000 640 640 640","NL_D5_NO_OPPORTUNITY"]
    assert check(noopp)["concept"]["classification"]=="no_opportunity"
    cmd=commands();assert "NL_D5_SCAN" in cmd and "NL_D5_C_POST" in cmd
    print("PASS: D5 synthetic selection, mixed-stream ordering, formula and two-arm gate",flush=True)
def main():
    self_test()
    if "--self-test" in sys.argv:return
    d4.commands=commands;d4.parse=parse;d4.analyze=analyze;d4.RESULT=RESULT;d4.save=save
    d3.OUT=OUT;d3.RESULT=RESULT;d3.trace=d4.trace
    import h08b_mounted_launch as launch
    save();launch.observe_one_norn=d3.observe;launch.main()
    r=RESULT.get("trace",{});c=r.get("analysis",{}).get("concept",{})
    if RESULT.get("pass"):RESULT["classification"]="PASS_local_concept_representation"
    elif c.get("classification") in ("no_opportunity","structural_or_layout_incomplete"):RESULT["classification"]=c["classification"]
    save()
    print("NL_D5_SUMMARY "+json.dumps({"classification":RESULT["classification"],"pass":RESULT["pass"],"subject_created":RESULT["subject_created"],"trig_attempts":RESULT["trig_attempts"],"selected":c.get("selected"),"concept_arms":c.get("arms"),"event_counts":r.get("event_counts"),"diagnostics":r.get("diagnostics"),"observer_error":r.get("observer_error")}),flush=True)
    if not RESULT["pass"]:raise SystemExit(1)
if __name__=="__main__":main()
