"""D4.1: synchronized L5->L0 propagation, two isolated native pulses."""
import json, os, pathlib, re, subprocess, sys, time
from collections import Counter
import h08d_d3 as d3
from c1_decay_math import relax
OUT=pathlib.Path("h08d-d4-result.json")
CAP=2*1024*1024
RESULT={"stage":"H08d.D4.1","subject_created":False,"pass":False,"classification":"launcher_not_reached","trig_attempts":0,"reward_pulses":0,"arms":[]}
COUNTS=[112,16,40,16,40,32,16,40,640]
FLAGS=[0,1,0,1,0,1,0,1,0]
ORDER=["LAYOUT","PRE","POST","COPY","PERCEPTION","ENDC"]
def save():OUT.write_text(json.dumps(RESULT,indent=2,sort_keys=True)+"\n",encoding="utf-8")
def pr(tag,fmt,args):return d3.pr(tag,fmt,args).replace("NL_D3_","NL_D4_")
def bp(off,cmd):return d3.bp(off,cmd)
def lobe(brain,i):return "("+brain+"+0x%x)"%(8+200*i)
def meta(brain,i):
    l=lobe(brain,i)
    return [f"poi({l}+0xa4)"]+[f"by({l}+0x{x:x})" for x in (0x14,0x15,0x16,0x22)]
def cells(brain,i,indices):
    l=lobe(brain,i)
    return [f"by(poi({l}+0x9c)+0x{16*j+k:x})" for j in indices for k in (2,3)]
def values(brain):return meta(brain,5)+meta(brain,0)+cells(brain,5,(8,9))+cells(brain,0,(40,41))
def layout(brain):
    return ["poi("+brain+"+0xc88)"]+[f"poi({lobe(brain,i)}+0xa4)" for i in range(9)]+[f"poi({lobe(brain,i)}+0xb4)" for i in range(9)]
def safe(brain,body):
    return ".if (poi("+brain+"+0xc88)==9) { .if (poi("+brain+"+0x494)==0x20) { .if (poi("+brain+"+0xac)==0x70) { "+body+" } .else { .echo NL_D4_LAYOUT_BAD; qd } } .else { .echo NL_D4_LAYOUT_BAD; qd } } .else { .echo NL_D4_LAYOUT_BAD; qd }"
def commands():
    def frame(tag):
        return pr(tag,"%u %08x %08x "+" ".join(["%u"]*18),["@$t1","@$t0","@$t2"]+values("@$t0"))
    lay=pr("LAYOUT","%u %08x %08x "+" ".join(["%u"]*19),["@$t1","@$t0","@$t2"]+layout("@$t0"))
    entry="r @$t0=@ecx; r @$t1=poi(@esp+4); r @$t2=poi(@esp); r @$t3=1; "+safe("@$t0",lay+"; "+frame("PRE")+"; gc")
    def middle(tag):
        return ".if (@$t3==1) { .if (@esi==@$t0) { "+frame(tag)+"; gc } .else { .echo NL_D4_ID_BAD; qd } } .else { .echo NL_D4_ORPHAN; qd }"
    post=".if (@$t3==1) { .if (@edi==@$t0+0x3f0) { "+middle("POST")+" } .else { gc } } .else { gc }"
    finish=".if (@$t3==1) { "+pr("ENDC","%u %08x",["@$t1","@esi"])+"; r @$t3=0; r @$t8=@$t8+1; .if (@$t9==2) { r @$t4=@$t4+1 }; .if (@$t4>=9) { .echo NL_D4_END; qd } .else { .if (@$t8>=0n512) { .echo NL_D4_CAP; qd } .else { gc } } } .else { .echo NL_D4_ORPHAN; qd }"
    pre="r @$t7=@ecx; r @$t6=poi(@esi+0xa4); "+safe("@$t7",pr("PULSE_PRE","%08x %u %u %u %u "+" ".join(["%u"]*18),["@$t7","poi(@esp)","poi(@esp+4)","poi(@esp+8)","@$t3"]+values("@$t7"))+"; gc")
    after=".if (poi(poi(@esi+0xa4)+0x2c18)==@$t7) { .if (poi(@esi+0xa4)==@$t6) { "+pr("PULSE_POST","%08x "+" ".join(["%u"]*18),["@$t7"]+values("@$t7"))+"; r @$t9=@$t9+1; gc } .else { .echo NL_D4_ID_BAD; qd } } .else { .echo NL_D4_ID_BAD; qd }"
    return "\n".join([".echo NL_D4_READY",*[f"r @$t{i}=0" for i in range(10)],bp(0x3bb0,entry),bp(0x3bd1,post),bp(0x3c82,middle("COPY")),bp(0x3c8c,middle("PERCEPTION")),bp(0x3cbb,finish),bp(0x16b39,pre),bp(0x16b3e,after),"g"])+"\n"
def valid_meta(v):
    return len(v)==18 and v[:4]==[32,0,24,0] and v[5:9]==[112,10,0,0] and not(v[4]&1 or v[9]&1) and all(0<=x<=255 for x in v[10:])
def valid_layout(v):
    return len(v)==19 and v[0]==9 and v[1:10]==COUNTS and [int(x!=0) for x in v[10:]]==FLAGS
def parse(raw,final=True):
    events=[];counts=Counter();err=Counter();aliases={}
    def alias(x):
        if not re.fullmatch("[0-9a-fA-F]{8}",x) or int(x,16)==0:raise ValueError()
        return aliases.setdefault(x.lower(),"B"+str(len(aliases)+1))
    def nums(a):
        if not all(x.isdigit() for x in a):raise ValueError()
        return list(map(int,a))
    for line in raw.splitlines():
        s=line.strip()
        if not s.startswith("NL_D4_"):continue
        a=s.split();tag=a[0][6:];counts[tag]+=1
        try:
            if tag in ("READY","END","CAP","LAYOUT_BAD","ID_BAD","ORPHAN"):
                if len(a)!=1:raise ValueError()
                events.append({"tag":tag})
            elif tag in ORDER[:-1]:
                if len(a)!=(23 if tag=="LAYOUT" else 22):raise ValueError()
                events.append({"tag":tag,"tick":nums(a[1:2])[0],"brain":alias(a[2]),"route":{0x407588:"regular",0x405db4:"alternate"}.get(int(a[3],16),"other"),"v":nums(a[4:])})
            elif tag=="ENDC":
                if len(a)!=3:raise ValueError()
                events.append({"tag":tag,"tick":nums(a[1:2])[0],"brain":alias(a[2])})
            elif tag=="PULSE_PRE":
                if len(a)!=24:raise ValueError()
                events.append({"tag":tag,"brain":alias(a[1]),"args":nums(a[2:5]),"in_cycle":nums(a[5:6])[0],"v":nums(a[6:])})
            elif tag=="PULSE_POST":
                if len(a)!=20:raise ValueError()
                events.append({"tag":tag,"brain":alias(a[1]),"v":nums(a[2:])})
            else:raise ValueError()
        except (ValueError,IndexError):err["malformed_marker"]+=1
    if final:
        for k,p in (("syntax",r"Syntax error|Extra character|Illegal"),("access",r"Memory access error|Unable to read|access violation"),("breakpoint",r"Unable to resolve|Couldn't resolve|Unable to insert breakpoint|Couldn't set breakpoint"),("operand",r"Operand error|Bad register|Invalid register"),("quote",r"unterminated|quote.*error")):
            if re.search(p,raw,re.I):err[k]+=1
    return events,dict(counts),dict(err)
def decode_cycles(ev):
    if len(ev)%6:return None
    out=[]
    for i in range(0,len(ev),6):
        e=ev[i:i+6]
        if [x["tag"] for x in e]!=ORDER or len({x["brain"] for x in e})!=1 or len({x["tick"] for x in e})!=1 or len({x["route"] for x in e[:-1]})!=1:return None
        lay=e[0]["v"];frames=[x["v"] for x in e[1:5]]
        if not valid_layout(lay) or not all(valid_meta(v) and v[:10]==frames[0][:10] for v in frames):return None
        out.append({"tick":e[0]["tick"],"brain":e[0]["brain"],"route":e[0]["route"],"layout":lay,"meta":frames[0][:10],**{k.lower():v[10:] for k,v in zip(ORDER[1:5],frames)}})
    return out
def sequence(c):
    return bool(c) and all(x["route"]=="regular" for x in c) and len({x["brain"] for x in c})==1 and all(b["tick"]==a["tick"]+1 and b["layout"]==a["layout"] and b["meta"]==a["meta"] for a,b in zip(c,c[1:]))
def zero(c):return all(all(x[k]==[0]*8 for k in ("pre","post","copy","perception")) for x in c)
def prediction(cell):
    p=[0]*8;p[2*(cell-8):2*(cell-8)+2]=[32,32];out=[]
    i=2*(cell-8);j=4+i
    for t in range(9):
        post=p[:];post[i]=p[i+1];post[i+1]=relax(p[i+1],24,0,t)
        copy=post[:];copy[j+1]=max(p[j+1],post[i])
        perc=copy[:];perc[j]=max(copy[j+1]-10,0);perc[j+1]=0
        out.append({"pre":p,"post":post,"copy":copy,"perception":perc})
        p=perc[:]
    return out
def ack_ok(a):return a.get("ok") is True and len(a.get("value",[]))==7 and a["value"][:2]==[32,32]
def analyze(ev,final=False):
    r={"complete":False,"basal_ready":False,"arms":[],"classification":"instrumental_incomplete_or_no_opportunity"}
    if not ev or ev[0]["tag"]!="READY":return r
    body=ev[1:]
    if final:
        if not body or body[-1]["tag"]!="END":return r
        body=body[:-1]
    else:
        # Only complete cycle records through latest ENDC; no live partial marks.
        end=max((i for i,x in enumerate(body) if x["tag"]=="ENDC"),default=-1)
        body=body[:end+1]
    segments=[];pulses=[];start=0;i=0
    while i<len(body):
        if body[i]["tag"]=="PULSE_PRE":
            if i+1>=len(body) or body[i+1]["tag"]!="PULSE_POST":return r
            segments.append(decode_cycles(body[start:i]));pulses.append(body[i:i+2]);i+=2;start=i
        else:i+=1
    segments.append(decode_cycles(body[start:]))
    if any(x is None for x in segments) or len(pulses)>2:return r
    allc=[x for s in segments for x in s]
    r["segments"]=segments
    if not sequence(allc):return r
    for i,(a,b) in enumerate(pulses):
        cell=8+i;before=segments[i];after=segments[i+1];expected=prediction(cell)
        pulse_target=[0]*8;pulse_target[2*i:2*i+2]=[32,32]
        baseline=before if i==0 else before[9:]
        basal=len(baseline)>=8 and zero(baseline[-8:])
        pulse=bool(a["args"]==[5,cell,32] and a["in_cycle"]==0 and a["brain"]==b["brain"]==allc[0]["brain"] and valid_meta(a["v"]) and valid_meta(b["v"]) and a["v"][:10]==b["v"][:10]==allc[0]["meta"] and a["v"][10:]==[0]*8 and b["v"][10:]==pulse_target)
        n=min(len(after),9)
        matched=sum(all(x[k]==y[k] for k in y) for x,y in zip(after[:9],expected))
        arm={"cell":cell,"basal":basal,"pulse":pulse,"cycles":n,"matched":matched,"expected":expected,"observed":after[:9],"pass":bool(basal and pulse and n==9 and matched==9)}
        r["arms"].append(arm)
        if not arm["pass"]:
            if basal and pulse and n==9:r["classification"]="observed_conditional_divergence"
            return r
        if len(after)>9 and not zero(after[9:]):r["classification"]="observed_carryover";return r
    if not pulses:r["basal_ready"]=len(segments[0])>=8 and zero(segments[0][-8:])
    elif len(pulses)==1:r["basal_ready"]=len(segments[1])>=17 and zero(segments[1][-8:])
    r["complete"]=len(pulses)==2 and len(segments[-1])==9 and all(a["pass"] for a in r["arms"])
    if r["complete"]:r["classification"]="PASS_local_propagation"
    return r
def self_test():
    def trip(t,v,brain="00010000",ret="00407588"):
        m=[32,0,24,0,0,112,10,0,0,0]
        return [f"NL_D4_LAYOUT {t} {brain} {ret} "+" ".join(map(str,[9]+COUNTS+FLAGS))]+[f"NL_D4_{tag} {t} {brain} {ret} "+" ".join(map(str,m+v[tag.lower()])) for tag in ORDER[1:5]]+[f"NL_D4_ENDC {t} {brain}"]
    z={k:[0]*8 for k in ("pre","post","copy","perception")};raw=["NL_D4_READY"];t=0
    m=[32,0,24,0,0,112,10,0,0,0]
    for cell in (8,9):
        for _ in range(8):raw+=trip(t,z);t+=1
        a=[0]*8;a[2*(cell-8):2*(cell-8)+2]=[32,32]
        ev,ct,err=parse("\n".join(raw));assert not err and analyze(ev)["basal_ready"]
        raw+=[f"NL_D4_PULSE_PRE 00010000 5 {cell} 32 0 "+" ".join(map(str,m+[0]*8)),"NL_D4_PULSE_POST 00010000 "+" ".join(map(str,m+a))]
        for v in prediction(cell):raw+=trip(t,v);t+=1
    raw+=["NL_D4_END"]
    def check(lines):
        e,c,x=parse("\n".join(lines));return not x and analyze(e,True)["complete"]
    assert check(raw)
    assert not check(raw[:-3]+raw[-2:])
    assert not check([x.replace("00407588","00405db4") if x.startswith("NL_D4_PRE 8 ") else x for x in raw])
    assert not check([x.replace("00010000","00020000") if x.startswith("NL_D4_COPY 8 ") else x for x in raw])
    assert not check([x.replace("112 16 40","111 16 40") if x.startswith("NL_D4_LAYOUT 8 ") else x for x in raw])
    assert not check([x[:-1]+"1" if x.startswith("NL_D4_PERCEPTION 8 ") else x for x in raw])
    assert [x["perception"][4] for x in prediction(8)]==[22,11,4,0,0,0,0,0,0]
    assert [x["perception"][6] for x in prediction(9)]==[22,11,4,0,0,0,0,0,0]
    print("PASS: D4 synthetic sequence, layout, threshold, isolation and corruption controls",flush=True)
def trace(pid,root,game,launch,ident):
    cdb=pathlib.Path(os.environ["ProgramFiles(x86)"])/"Windows Kits"/"10"/"Debuggers"/"x86"/"cdb.exe"
    cmd=root/"d4.txt";cmd.write_text(commands(),encoding="ascii");log=root/"d4.log"
    def n(s):return launch.query_macro("enum 4 1 0,"+s+",next",kind="cell")
    def read():
        if log.stat().st_size>CAP:raise RuntimeError("capture_cap")
        with log.open("rb") as f:return f.read(CAP+1).decode("utf-8","replace")
    def live():
        raw=read();e,c,x=parse(raw[:raw.rfind("\n")+1],False)
        if x:return {}
        return analyze(e)
    start=time.monotonic();error=None;timed=False
    with log.open("wb") as out:
        p=subprocess.Popen([str(cdb),"-G","-pd","-p",str(pid),"-cf",str(cmd)],cwd=game,stdin=subprocess.DEVNULL,stdout=out,stderr=subprocess.STDOUT)
        try:
            for cell in (8,9):
                ready=False
                while p.poll() is None and time.monotonic()-start<70:
                    a=live()
                    if a.get("classification") in ("observed_conditional_divergence","observed_carryover"):raise RuntimeError("observed_A_divergence")
                    if a.get("basal_ready") and len(a.get("arms",[]))==cell-8:
                        ready=True;break
                    time.sleep(.1)
                if not ready:raise RuntimeError("basal_not_observed")
                row={"cell":cell,"identity_before":bool(ident())};RESULT["arms"].append(row)
                if not row["identity_before"]:raise RuntimeError("identity_before")
                row["dde_basal"]=[n("dde: cell 5 8 0"),n("dde: cell 5 9 0")]
                if not all(x.get("ok") and len(x.get("value",[]))==7 and x["value"][:2]==[0,0] for x in row["dde_basal"]):raise RuntimeError("dde_basal_not_zero")
                a=live()
                if not a.get("basal_ready") or len(a.get("arms",[]))!=cell-8 or p.poll() is not None or time.monotonic()-start>=80:raise RuntimeError("basal_lost")
                RESULT["trig_attempts"]+=1;save()
                row["ack"]=n(f"trig 5 {cell} 32,dde: cell 5 {cell} 0");save()
                if not ack_ok(row["ack"]):raise RuntimeError("ack_invalid")
                row["identity_after"]=bool(ident());save()
                if not row["identity_after"]:raise RuntimeError("identity_after")
            while p.poll() is None and time.monotonic()-start<90:
                if log.stat().st_size>CAP:raise RuntimeError("capture_cap")
                time.sleep(.1)
            timed=p.poll() is None
        except Exception as e:
            error=str(e) if type(e) is RuntimeError and re.fullmatch("[A-Za-z_]+",str(e)) else type(e).__name__
        finally:
            if p.poll() is None:
                p.terminate()
                try:p.wait(timeout=5)
                except subprocess.TimeoutExpired:p.kill();p.wait(timeout=5)
    with log.open("rb") as f:data=f.read(CAP+1)
    ev,ct,err=parse(data[:CAP].decode("utf-8","replace"))
    if log.stat().st_size>CAP:err["capture_cap"]=1
    a=analyze(ev,True)
    # Preserve partial and divergent observations even if no END.
    partial=analyze(ev,False) if not a["complete"] else a
    transport=not err and not timed and p.returncode==0 and ct.get("READY")==ct.get("END")==1 and ct.get("PULSE_PRE")==ct.get("PULSE_POST")==2
    ids=bool(ident()) and len(RESULT["arms"])==2 and all(x.get("identity_before") and x.get("identity_after") for x in RESULT["arms"])
    ack=len(RESULT["arms"])==2 and all(ack_ok(x.get("ack",{})) for x in RESULT["arms"])
    passed=bool(transport and ids and ack and a["complete"] and not error)
    classification="PASS_local_propagation" if passed else partial["classification"]
    if not passed and classification=="PASS_local_propagation":classification="instrumental_incomplete_or_no_opportunity"
    return {"pass":passed,"classification":classification,"gate_checks":{"transport":transport,"identity":ids,"ack":ack,"full_prediction":a["complete"]},"events":ev,"analysis":partial,"event_counts":ct,"diagnostics":err,"returncode":p.returncode,"timeout":timed,"observer_error":error,"raw_bytes":log.stat().st_size,"elapsed_ms":round((time.monotonic()-start)*1000)}
def main():
    self_test()
    if "--self-test" in sys.argv:return
    # Reuse the validated D3 launch/identity/initialization and result persistence.
    d3.OUT=OUT;d3.RESULT=RESULT;d3.trace=trace
    import h08b_mounted_launch as launch
    save();launch.observe_one_norn=d3.observe;launch.main()
    print("NL_D4_RESULT "+json.dumps(RESULT,separators=(",",":")),flush=True)
    if not RESULT["pass"]:raise SystemExit(1)
if __name__=="__main__":main()
