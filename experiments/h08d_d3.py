"""D3.1: one native pulse and measured GeneralSense updates; no reset/reward."""
import json, os, pathlib, re, shutil, subprocess, sys, time
from collections import Counter
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"inherited"/"experiments"/"neurolab"))
from c1_decay_math import relax
OUT=pathlib.Path("h08d-d3-result.json")
CAP=2*1024*1024
RESULT={"stage":"H08d.D3.1","subject_created":False,"pass":False,"classification":"launcher_not_reached","trig_attempts":0,"reward_pulses":0}
def save():OUT.write_text(json.dumps(RESULT,indent=2,sort_keys=True)+"\n",encoding="utf-8")
def bp(off,cmd):return 'bp Creatures+0x%x "%s"'%(off,cmd.replace('"','\\"'))
def pr(tag,fmt,args):return '.printf "NL_D3_'+tag+' '+fmt+('\\'*2)+'n", '+', '.join(args)
def sense(brain):
    l="("+brain+"+0x3f0)"
    return [f"poi({l}+0xa4)",*[f"by({l}+0x{x:x})" for x in (0x14,0x15,0x16,0x22)],
            *[f"by(poi({l}+0x9c)+0x{x:x})" for x in (0x82,0x83,0x92,0x93)]]
def safe_read(brain,body):
    return ".if (poi("+brain+"+0xc88)>5) { .if (poi("+brain+"+0x494)==0x20) { "+body+" } .else { .echo NL_D3_LAYOUT_BAD; qd } } .else { .echo NL_D3_LAYOUT_BAD; qd }"
def commands():
    fmt=" ".join(["%u","%08x","%08x"]+["%u"]*9)
    def frame(tag):
        return pr(tag,fmt,["@$t1","@$t0","@$t2"]+sense("@$t0"))
    entry="r @$t0=@ecx; r @$t1=poi(@esp+4); r @$t2=poi(@esp); r @$t3=1; "+safe_read("@$t0",frame("PRE")+"; gc")
    post=".if (@$t3==1) { .if (@edi==@$t0+0x3f0) { .if (@esi==@$t0) { "+frame("POST")+"; gc } .else { .echo NL_D3_ID_BAD; qd } } .else { gc } } .else { gc }"
    finish=".if (@$t3==1) { "+pr("ENDC","%u %08x",["@$t1","@esi"])+"; r @$t3=0; r @$t8=@$t8+1; .if (@$t5==1) { r @$t4=@$t4+1 }; .if (@$t4>=9) { .echo NL_D3_END; qd } .else { .if (@$t8>=0n512) { .echo NL_D3_CAP; qd } .else { gc } } } .else { .echo NL_D3_ORPHAN; qd }"
    trigpre="r @$t7=@ecx; r @$t6=poi(@esi+0xa4); "+safe_read("@$t7",pr("PULSE_PRE","%08x %u %u %u %u "+" ".join(["%u"]*9),["@ $t7".replace(" ",""),"poi(@esp)","poi(@esp+4)","poi(@esp+8)","@$t3"]+sense("@$t7"))+"; gc")
    trigpost=".if (poi(poi(@esi+0xa4)+0x2c18)==@$t7) { .if (poi(@esi+0xa4)==@$t6) { "+pr("PULSE_POST","%08x "+" ".join(["%u"]*9),["@$t7"]+sense("@$t7"))+"; r @$t5=1; gc } .else { .echo NL_D3_ID_BAD; qd } } .else { .echo NL_D3_ID_BAD; qd }"
    return "\n".join([".echo NL_D3_READY",*[f"r @$t{i}=0" for i in range(9)],
         bp(0x3bb0,entry),bp(0x3bd1,post),bp(0x3cbb,finish),bp(0x16b39,trigpre),bp(0x16b3e,trigpost),"g"])+"\n"
def metadata(v):
    return len(v)==9 and v[:4]==[32,0,24,0] and 0<=v[4]<=255 and not(v[4]&1) and all(0<=x<=255 for x in v[5:])
def parse(raw,final=True):
    events=[]; errors=Counter(); counts=Counter(); aliases={}
    def alias(x):
        if not re.fullmatch("[0-9a-fA-F]{8}",x) or int(x,16)==0:raise ValueError()
        return aliases.setdefault(x.lower(),"B"+str(len(aliases)+1))
    def num(x):
        if not x.isdigit():raise ValueError()
        return int(x)
    for line in raw.splitlines():
        s=line.strip()
        if not s.startswith("NL_D3_"):continue
        a=s.split();tag=a[0][6:];counts[tag]+=1
        try:
            if tag in ("READY","END","CAP","LAYOUT_BAD","ID_BAD","ORPHAN"):
                if len(a)!=1:raise ValueError()
                events.append({"tag":tag})
            elif tag in ("PRE","POST"):
                if len(a)!=13:raise ValueError()
                ret=int(a[3],16)
                events.append({"tag":tag,"tick":num(a[1]),"brain":alias(a[2]),"route":{0x407588:"regular",0x405db4:"alternate"}.get(ret,"other"),"v":[num(x) for x in a[4:]]})
            elif tag=="ENDC":
                if len(a)!=3:raise ValueError()
                events.append({"tag":tag,"tick":num(a[1]),"brain":alias(a[2])})
            elif tag=="PULSE_PRE":
                if len(a)!=15:raise ValueError()
                events.append({"tag":tag,"brain":alias(a[1]),"args":[num(x) for x in a[2:5]],"in_cycle":num(a[5]),"v":[num(x) for x in a[6:]]})
            elif tag=="PULSE_POST":
                if len(a)!=11:raise ValueError()
                events.append({"tag":tag,"brain":alias(a[1]),"v":[num(x) for x in a[2:]]})
            else:raise ValueError()
        except (ValueError,IndexError):errors["malformed_marker"]+=1
    if final:
        for k,p in (("syntax",r"Syntax error|Extra character|Illegal"),("access",r"Memory access error|Unable to read|access violation"),("breakpoint",r"Unable to resolve|Couldn't resolve|Unable to insert breakpoint|Couldn't set breakpoint"),("operand",r"Operand error|Bad register|Invalid register"),("quote",r"unterminated|quote.*error")):
            if re.search(p,raw,re.I):errors[k]+=1
    return events,dict(counts),dict(errors)
def cycles(events):
    # Preserve order, reject interruptions and incomplete triplets.
    if len(events)%3:return None
    out=[]
    for i in range(0,len(events),3):
        a,b,c=events[i:i+3]
        if [x["tag"] for x in (a,b,c)]!=["PRE","POST","ENDC"]:return None
        if len({x["brain"] for x in (a,b,c)})!=1 or len({x["tick"] for x in (a,b,c)})!=1 or a["route"]!=b["route"]:return None
        if not metadata(a["v"]) or not metadata(b["v"]) or a["v"][:5]!=b["v"][:5]:return None
        out.append({"brain":a["brain"],"tick":a["tick"],"route":a["route"],"pre":a["v"][5:],"post":b["v"][5:]})
    return out
def valid_sequence(c,n,zero=False):
    return c is not None and len(c)==n and all(x["route"]=="regular" for x in c) and len({x["brain"] for x in c})==1 and all(b["tick"]==a["tick"]+1 for a,b in zip(c,c[1:])) and (not zero or all(x["pre"]==x["post"]==[0]*4 for x in c))
def basal_live(raw):
    # Do not require current partial cycle to be complete; final analysis does.
    ev,ct,err=parse(raw,False)
    if err or ct.get("READY")!=1 or any(x["tag"] not in ("READY","PRE","POST","ENDC") for x in ev):return False
    end=max((i for i,x in enumerate(ev) if x["tag"]=="ENDC"),default=-1)
    if end<24:return False
    return valid_sequence(cycles(ev[end-23:end+1]),8,True)
def evaluate(ev,ct,err,ret,timeout,ack,ident_before,ident_after):
    result={"event_counts":ct,"diagnostics":err,"returncode":ret,"timeout":timeout,"gate_checks":{},"pass":False}
    checks=result["gate_checks"]
    checks["transport"]=ret==0 and not timeout and not err and ct.get("READY")==ct.get("END")==ct.get("PULSE_PRE")==ct.get("PULSE_POST")==1 and ev and ev[0]["tag"]=="READY" and ev[-1]["tag"]=="END"
    checks["identity"]=ident_before and ident_after
    checks["ack"]=ack.get("ok") is True and len(ack.get("value",[]))==7 and ack["value"][:2]==[32,32]
    preidx=next((i for i,x in enumerate(ev) if x["tag"]=="PULSE_PRE"),-1)
    postidx=next((i for i,x in enumerate(ev) if x["tag"]=="PULSE_POST"),-1)
    if preidx<1 or postidx!=preidx+1:
        result["classification"]="instrumental_incomplete_or_no_opportunity";return result
    a,b=ev[preidx],ev[postidx]
    checks["pulse"]=a["args"]==[5,8,32] and a["in_cycle"]==0 and a["brain"]==b["brain"] and metadata(a["v"]) and metadata(b["v"]) and a["v"][:5]==b["v"][:5] and a["v"][5:]==[0]*4 and b["v"][5:]==[32,32,0,0]
    base=cycles(ev[1:preidx]);after=cycles(ev[postidx+1:-1])
    result["basal_cycles"]=base;result["post_cycles"]=after
    tail=base[-8:] if base else None
    checks["basal"]=valid_sequence(tail,8,True)
    checks["post_sequence"]=valid_sequence(after,9) and checks["basal"] and after[0]["tick"]==tail[-1]["tick"]+1 and all(x["brain"]==a["brain"] for x in tail+after)
    expected=[];p=[32,32,0,0]
    for i in range(9):
        v=p[1];s=relax(v,24,0,i)
        after_v=[v,s,0,0];expected.append({"pre":p,"post":after_v});p=after_v
    result["expected"]=expected
    checks["prediction"]=bool(checks["post_sequence"] and all(x["pre"]==y["pre"] and x["post"]==y["post"] for x,y in zip(after,expected)))
    result["matched_cycles"]=sum(x["pre"]==y["pre"] and x["post"]==y["post"] for x,y in zip(after or [],expected))
    result["pass"]=all(checks.values())
    result["classification"]="PASS_local_decay" if result["pass"] else ("observed_conditional_divergence" if all(v for k,v in checks.items() if k!="prediction") else "instrumental_incomplete_or_no_opportunity")
    return result
def self_test():
    # Same parser and gate as live experiment, plus explicit controls for wrong route and missing rows.
    def frame(tag,t,v,ret="00407588"):return f"NL_D3_{tag} {t} 00010000 {ret} 32 0 24 0 0 "+" ".join(map(str,v))
    def trip(t,p,q,ret="00407588"):return [frame("PRE",t,p,ret),frame("POST",t,q,ret),f"NL_D3_ENDC {t} 00010000"]
    raw=["NL_D3_READY"]
    for t in range(8):raw+=trip(t,[0]*4,[0]*4)
    assert basal_live("\n".join(raw)+"\n")
    raw+=["NL_D3_PULSE_PRE 00010000 5 8 32 0 32 0 24 0 0 0 0 0 0","NL_D3_PULSE_POST 00010000 32 0 24 0 0 32 32 0 0"]
    p=[32,32,0,0]
    for t in range(8,17):
        q=[p[1],relax(p[1],24,0,t),0,0];raw+=trip(t,p,q);p=q
    raw+=["NL_D3_END"]
    def check(lines):
        ev,ct,err=parse("\n".join(lines))
        return evaluate(ev,ct,err,0,False,{"ok":True,"value":[32,32,0,0,0,0,0]},True,True)
    assert check(raw)["pass"]
    assert not check(raw[:-3]+raw[-2:])["pass"]
    assert not check([x.replace("00407588","00405db4") if x.startswith("NL_D3_PRE 8 ") else x for x in raw])["pass"]
    assert not check([x.replace("32 21 0 0","32 22 0 0") if x.startswith("NL_D3_POST 8 ") else x for x in raw])["pass"]
    assert not parse('0:000> .printf "NL_D3_READY"')[0]
    assert len(commands().splitlines())==16
    print("PASS: D3 synthetic transport, basal, pulse, sequence, conditional prediction",flush=True)
def trace(pid,root,game,launch,ident):
    cdb=pathlib.Path(os.environ["ProgramFiles(x86)"])/"Windows Kits"/"10"/"Debuggers"/"x86"/"cdb.exe"
    cmd=root/"d3.txt";cmd.write_text(commands(),encoding="ascii");log=root/"d3.log"
    def n(cmd,kind="cell"):return launch.query_macro("enum 4 1 0,"+cmd+",next",kind=kind)
    def read():
        if log.stat().st_size>CAP:raise RuntimeError("capture_cap")
        with log.open("rb") as f:return f.read(CAP+1).decode("utf-8","replace")
    start=time.monotonic();ack={};error=None;before=False;basal_ok=False;timed=False
    with log.open("wb") as out:
        p=subprocess.Popen([str(cdb),"-G","-pd","-p",str(pid),"-cf",str(cmd)],cwd=game,stdin=subprocess.DEVNULL,stdout=out,stderr=subprocess.STDOUT)
        try:
            while p.poll() is None and time.monotonic()-start<35:
                raw=read()
                # Only complete lines for live arming.
                if basal_live(raw[:raw.rfind("\n")+1]):
                    basal_ok=True;break
                time.sleep(.1)
            if not basal_ok:raise RuntimeError("basal_not_observed")
            before=bool(ident());RESULT["identity_before_pulse"]=before
            if not before:raise RuntimeError("identity_before_pulse")
            basal=[n("dde: cell 5 8 0"),n("dde: cell 5 9 0")]
            RESULT["dde_basal"]=basal
            if not all(x.get("ok") and len(x.get("value",[]))==7 and x["value"][:2]==[0,0] for x in basal):raise RuntimeError("dde_basal_not_zero")
            if p.poll() is not None or time.monotonic()-start>=45:raise RuntimeError("observer_not_available")
            if not basal_live(read().rsplit("\n",1)[0]):raise RuntimeError("basal_lost")
            RESULT["trig_attempts"]=1;save()
            ack=n("trig 5 8 32,dde: cell 5 8 0")
            RESULT["dde_ack"]=ack;save()
            while p.poll() is None and time.monotonic()-start<60:
                if log.stat().st_size>CAP:raise RuntimeError("capture_cap")
                time.sleep(.1)
            timed=p.poll() is None
        except Exception as e:
            error=str(e) if type(e) is RuntimeError and re.fullmatch("[a-z_]+",str(e)) else type(e).__name__
        finally:
            if p.poll() is None:
                p.terminate()
                try:p.wait(timeout=5)
                except subprocess.TimeoutExpired:p.kill();p.wait(timeout=5)
    with log.open("rb") as f:data=f.read(CAP+1)
    raw=data[:CAP].decode("utf-8","replace")
    ev,ct,err=parse(raw)
    if len(data)>CAP or log.stat().st_size>CAP:err["capture_cap"]=1
    after=bool(ident());RESULT["identity_after_pulse"]=after
    r=evaluate(ev,ct,err,p.returncode,timed,ack,before,after)
    r.update({"events":ev,"live_basal_observed":basal_ok,"observer_error":error,"raw_bytes":log.stat().st_size,"elapsed_ms":round((time.monotonic()-start)*1000)})
    if error:r["pass"]=False;r["classification"]="instrumental_incomplete_or_no_opportunity"
    return r
def observe(game,pid,root):
    import h08b_mounted_launch as launch
    q=launch.query_macro;base=launch.base
    def req(x,msg):
        if not x:raise RuntimeError(msg)
    def ident():return q("dde: putv totl 4 1 0",1).get("ok") and q("enum 4 1 0,dde: getb monk,next","31306c6e","moniker").get("ok")
    try:
        req(q("dde: putv totl 4 1 0",0).get("ok"),"world_not_empty")
        dst=game/"Genetics"/"NL01.gen";req(not dst.exists(),"moniker_collision")
        shutil.copyfile(game/"Genetics"/"dad1.gen",dst);req(base.digest(dst)==base.GEN,"genome_mismatch")
        req(q("new: crea tokn nl01 1,mvto 2408 870,dde: putv totl 4 1 0",1).get("ok"),"birth_transport")
        RESULT["subject_created"]=True;save()
        end=time.perf_counter()+85
        while time.perf_counter()<end:
            time.sleep(min(5,max(0,end-time.perf_counter())))
            req(q("dde: putv 123",123).get("ok"),"initialization_dde")
        req(ident(),"initial_identity")
        r=trace(pid,root,game,launch,ident)
        RESULT["trace"]=r;RESULT["pass"]=r["pass"];RESULT["classification"]=r["classification"]
    except Exception as e:
        RESULT["error"]=str(e) if type(e) is RuntimeError and re.fullmatch("[a-z_]+",str(e)) else type(e).__name__
        RESULT["classification"]="instrumental_failure"
    finally:save()
def main():
    self_test()
    if "--self-test" in sys.argv:return
    save()
    import h08b_mounted_launch as launch
    launch.observe_one_norn=observe;launch.main()
    print("NL_D3_RESULT "+json.dumps(RESULT,sort_keys=True),flush=True)
    if not RESULT["pass"]:raise SystemExit(1)
if __name__=="__main__":main()
