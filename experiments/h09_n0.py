"""H09.N0: bounded read-only natural pattern observation."""
import collections,hashlib,json,os,pathlib,re,struct,subprocess,sys,tempfile,time
import h09_1 as h
import h08d_d1 as d1
import h08d_d3 as d3
OUT=pathlib.Path("h09-n0-result.json")
RESULT={"stage":"H09.N0","subject_created":False,"pass":False,"classification":"launcher_not_reached","trig_attempts":0,"reward_pulses":0,"stim_attempts":0}
CAP=4*1024*1024
N=256
C,D,P=h.C,h.D,h.P
h.SIZES.update({"POP":12,"POP_END":1,"EP":5,"EP_END":1,"CHANGE":3,"SIG":8})
def save():OUT.write_text(json.dumps(RESULT,indent=2,sort_keys=True)+"\n",encoding="utf-8")
def pr(tag,v=(),direct=False):return h.pr(tag,v,direct)
def check(cond,body):return h.check(cond,body)
def signature():
    cell=f"({C}+@$t10*0x10)"
    count=f"by({cell}+0xc+@$t11)"
    arr=f"poi({cell}+4+@$t11*4)"
    ptr=f"({arr}+@$t12*0xc)"
    src=f"poi({ptr})"
    ok=f"(({src}>={P})&({src}<{P}+0x700)&((({src}-{P})&0xf)==0))"
    row=pr("SIG",["@$t10","@$t11","@$t12",f"(({src}-{P})/0x10)",h.byte(ptr,6),h.byte(ptr,7),h.byte(ptr,8),h.byte(ptr,9)],True)
    bad=pr("SIG",["@$t10","@$t11","@$t12","0n999",h.byte(ptr,6),h.byte(ptr,7),h.byte(ptr,8),h.byte(ptr,9)],True)
    # Susceptibility of incoming Concept contacts is read separately only if needed;
    # Concept rule is nonplastic; retain index, weights and strength.
    meta=pr("SIG_META",["@$t10",h.byte(cell,12),h.byte(cell,13)],True)
    inner=f".if ({count}!=0) {{ "+check(f"({count}<=0x80)&($vvalid({arr},{count}*0xc)==1)",f".for (r @$t12=0; @$t12<{count}; r @$t12=@$t12+1) {{ .if ({ok}) {{ {row} }} .else {{ {bad} }} }}")+" }"
    return ".for (r @$t10=0; @$t10<0n640; r @$t10=@$t10+1) { "+meta+"; .for (r @$t11=0; @$t11<2; r @$t11=@$t11+1) { "+inner+" } }\n"
def endpoint_script(i):
    lines=[check("(poi(@$t0+0x6ec)==0n640)&(poi(@$t0+0x55c)==0n16)&(poi(@$t0+0xac)==0n112)&"+h.valid(D,256),pr("EP",[f"0n{i}",C,D,"poi(@$t0+0x6ec)","poi(@$t0+0x55c)"],True)),
           f".writemem n0d{i}.bin {D} L0x100"]
    for d in range(16):
        for typ in range(2):
            owner=f"({D}+0x{d*16:x})";ptr=f"poi({owner}+0x{4+typ*4:x})"
            lines.append(check(f"(by({owner}+0x{12+typ:x})==0x80)&"+h.valid(ptr,1536),f".writemem n0s{i}_{d}_{typ}.bin {ptr} L0x600"))
    lines += ["$$>a<n0sig.txt",pr("EP_END",[f"0n{i}"],True)]
    return "\n".join(lines)+"\n"
def scripts(root):
    def write(name,s):(root/name).write_text(s,encoding="ascii")
    write("n0sig.txt",signature())
    for i in (0,255):write(f"n0ep{i}.txt",endpoint_script(i))
    for g in range(16):
        lines=[]
        for i in range(g*16,g*16+16):
            body=f".writemem n0c{i:03d}.bin {C} L0x2800"
            if i in (0,255):body+=f"; $$>a<n0ep{i}.txt"
            lines.append(f".if (@$t4==0n{i}) {{ {body} }}")
        write(f"n0group{g}.txt","\n".join(lines)+"\n")
    lines=[check("(poi(@$t0+0x6ec)==0n640)&"+h.valid(C,10240),pr("POP",["@$t4"]+h.chemistry(),True))]
    lines += [f".if ((@$t4>=0n{g*16})&(@$t4<0n{g*16+16})) {{ $$>a<n0group{g}.txt }}" for g in range(16)]
    lines += [pr("POP_END",["@$t4"],True)]
    write("n0pop.txt","\n".join(lines)+"\n")
def cmds():
    rb=".if (@$t0==0) { r @$t0=@ecx; r @$t1=@esi }; "+check("(@ecx==@$t0)&(@esi==@$t1)&(@$t3==0)&(poi(@$t0+0x6ec)==0n640)&(poi(@$t0+0x55c)==0n16)","r @$t2=poi(@esi+0x2c20); r @$t3=1; "+pr("RB",["0"]+h.chemistry())+"; gc")
    dp=".if ((@$t3==1)&(@ecx==@$t0+0x4b8)) { $$>a<n0pop.txt; gc } .else { gc }"
    wp=".if ((@$t3==1)&(@ebx==@$t0+0x4b8)) { "+h.wta("WPRE","WP")+"; gc } .else { gc }"
    wq=".if ((@$t3==1)&(@ebx==@$t0+0x4b8)) { "+h.wta("WPOST","WQ")+"; gc } .else { gc }"
    rp=".if (@$t3==1) { "+check("(@esi==@$t1)&(poi(@esi+0x2c18)==@$t0)&(poi(@esi+0x2c20)==@$t2)",pr("RP",h.chemistry())+"; r @$t3=0; r @$t4=@$t4+1; .if (@$t4==0n256) { .echo NL_H9_END; qd } .else { gc }")+" } .else { gc }"
    # Keep the current regular tick register unchanged by alternative-route/attention observations.
    def external(tag,values,brain="@$t0"):
        return d3.pr(tag," ".join(["%u","%08x"]+["%u"]*len(values)),["poi(@$t1+0x2c20)",brain,*values]).replace("NL_D3_","NL_H9_")
    ap=".if ((@$t0!=0)&(@esi==@$t1)) { r @$t14=poi(@esp); r @$t15=@ebx; r @$t13=poi(@esi+0x7f0); gc } .else { gc }"
    aq=".if ((@$t0!=0)&(@esi==@$t1)) { "+external("CHANGE",["@$t15","(@$t13!=@$t14)","(poi(@esi+0x7f0)==@$t14)"])+"; gc } .else { gc }"
    alt=".if ((@$t0!=0)&(@ecx==@$t0)&(poi(@esp)==Creatures+0x5db4)) { "+external("ALT",["1"])+"; gc } .else { gc }"
    stop=".if ((@eax==0n31999)&(@$t0!=0)) { .if (poi(@ebx+0xa4)==@$t1) { .echo NL_H9_CAP; qd } .else { gc } } .else { gc }"
    bps=[(0x7583,rb),(0x3e00,dp),(0x48a0,wp),(0x4911,wq),(0x759a,rp),(0x9cf8,ap),(0x9cfd,aq),(0x3bb0,alt),(0x156df,stop)]
    lines=[".echo NL_H9_READY"]+[f"r @$t{i}=0" for i in range(16)]+[d3.bp(off,s) for off,s in bps]+["g"]
    if max(map(len,lines))>4096:raise RuntimeError("command_too_long")
    return "\n".join(lines)+"\n"
def exact(root,name,n):
    b=(root/name).read_bytes()
    if len(b)!=n:raise RuntimeError("block_length")
    return b
def vector(root,i):
    b=exact(root,f"n0c{i:03d}.bin",10240)
    return [[b[j*16+2],b[j*16+3]] for j in range(640)]
def endpoint(root,ev,i):
    a=[e for e in ev if e["tag"]=="EP" and e["v"][0]==i]
    z=[e for e in ev if e["tag"]=="EP_END" and e["v"][0]==i]
    if len(a)!=1 or len(z)!=1:raise RuntimeError("endpoint_marker")
    a,z=a[0],z[0]
    if a["tick"]!=z["tick"] or a["brain"]!=z["brain"] or a["pos"]>=z["pos"]:raise RuntimeError("endpoint_identity")
    _,cb,db,nc,nd=a["v"]
    if (nc,nd)!=(640,16) or not cb or not db:raise RuntimeError("endpoint_layout")
    d=exact(root,f"n0d{i}.bin",256);rows=[]
    for dest in range(16):
        for typ in (0,1):
            if d[dest*16+12+typ]!=128:raise RuntimeError("endpoint_count")
            b=exact(root,f"n0s{i}_{dest}_{typ}.bin",1536)
            for slot in range(128):
                src=h.u32(b,slot*12);v=list(b[slot*12+6:slot*12+10])
                if src==0 and v[-1]==0:ix=999
                elif cb<=src<cb+10240 and (src-cb)%16==0:ix=(src-cb)//16
                else:raise RuntimeError("endpoint_source")
                rows.append([dest,typ,slot,ix,*v])
    sigs=[e for e in ev if a["pos"]<e.get("pos",-1)<z["pos"] and e["tag"] in ("SIG_META","SIG")]
    if any(e["tick"]!=a["tick"] or e["brain"]!=a["brain"] for e in sigs):raise RuntimeError("signature_identity")
    meta=[e["v"] for e in sigs if e["tag"]=="SIG_META"];sig=[e["v"] for e in sigs if e["tag"]=="SIG"]
    if [m[0] for m in meta]!=list(range(640)) or any(any(not 0<=v<=128 for v in m[1:]) for m in meta):raise RuntimeError("signature_meta")
    exp=[(j,t,k) for j,n0,n1 in meta for t,n in enumerate((n0,n1)) for k in range(n)]
    if [tuple(v[:3]) for v in sig]!=exp or any(not(0<=v[3]<112 or v[3]==999) or any(not 0<=n<=255 for n in v[4:]) for v in sig):raise RuntimeError("signature_rows")
    return {"index":i,"tick":a["tick"],"rows":rows,"signature_meta":meta,"signature":sig,"states":vector(root,i)}
def collect(root,ev):
    base=[e for e in ev if e["tag"] in ("RB","WPRE","WP","WPOST","WQ","RP","ATT","ALT","READY","END","CAP","BAD")]
    frames,bad=h.collect(base)
    # h.collect's end position is in filtered list; use true event positions.
    rb=[e for e in ev if e["tag"]=="RB"];rp=[e for e in ev if e["tag"]=="RP"]
    ps=[e for e in ev if e["tag"]=="POP"];pe=[e for e in ev if e["tag"]=="POP_END"]
    if not(len(frames)==len(rb)==len(rp)==len(ps)==len(pe)):bad.append("phase_count")
    out=[]
    for i,(f,a,b,p,q) in enumerate(zip(frames,rb,rp,ps,pe)):
        if not(a["pos"]<p["pos"]<q["pos"]<b["pos"]) or not all(e["tick"]==f["tick"] and e["brain"]==f["brain"] for e in (a,b,p,q)):bad.append("population_order");break
        if p["v"][0]!=i or q["v"]!=[i] or any(not 0<=x<=255 for x in p["v"][1:]):bad.append("population_index");break
        w=[e for e in ev if e["tag"]=="WPRE" and a["pos"]<e.get("pos",-1)<b["pos"]]
        if len(w)!=1 or q["pos"]>=w[0]["pos"]:bad.append("population_before_WTA");break
        try:v=vector(root,i)
        except (OSError,RuntimeError):bad.append("population_block");break
        f.update({"index":i,"start":a["pos"],"end":b["pos"],"concept":v,"chem_decision":p["v"][1:]})
        out.append(f)
    return out,bad
def jac(a,b):return len(a&b)/len(a|b) if a|b else 1.0
def recurrence(frames):
    active=[{i for i,v in enumerate(f["concept"]) if v[0]>0} for f in frames]
    a=b=None;ai=bi=None
    for i,s in enumerate(active[:64]):
        if a is None:
            if len(s)>=3:a=s;ai=i
        elif len(s)>=3 and abs(len(s)-len(a))<=1 and jac(s,a)<=.2:
            b=s;bi=i;break
    def label(s):
        if a is None or b is None:return None
        if jac(s,a)>=.8 and jac(s,b)<=.2:return "A"
        if jac(s,b)>=.8 and jac(s,a)<=.2:return "B"
        return None
    labels=[label(s) for s in active]
    episodes={"A":[],"B":[]}
    for i in range(64,len(labels)):
        lab=labels[i]
        if lab is None or i<8 or lab in labels[i-8:i]:continue
        j=i+1
        while j<len(labels) and labels[j]==lab:j+=1
        episodes[lab].append({"index":i,"tick":frames[i]["tick"],"length":j-i,"winners":[f["winner"] for f in frames[i:j]]})
    counts={k:sum(x==k for x in labels[64:]) for k in ("A","B",None)}
    ok=all(len(episodes[k])>=4 and sum(e["length"]>=4 for e in episodes[k])>=2 for k in ("A","B"))
    return {"A":sorted(a) if a is not None else None,"B":sorted(b) if b is not None else None,"A_index":ai,"B_index":bi,"labels":labels,"episodes":episodes,"validation_counts":{str(k):v for k,v in counts.items()},"recurrence":ok}
def analyze(frames,ends):
    r=recurrence(frames)
    wash=[];run=0
    for f in frames:
        zero=all(v==0 for key in ("chem_pre","chem_decision","chem_post") for v in f[key])
        run=run+1 if zero else 0
        if run>=8:wash.append(f["tick"])
    labeled=[f for f,l in zip(frames,r["labels"]) if f["index"]>=64 and l is not None]
    wins=sorted({f["winner"] for f in labeled if f["winner"] is not None})
    margins=[]
    for f in labeled:
        p=sorted([v for v in f["wpre"] if v[1]>0 and v[3]==0],key=lambda v:(-v[1],v[0]))
        if len(p)>=2:margins.append([f["tick"],p[0][0],p[1][0],p[0][1]-p[1][1]])
    changes=None;patterns={}
    if len(ends)==2:
        a,b=ends;changes=sum(x[3]!=y[3] for x,y in zip(a["rows"],b["rows"]))
        for label in ("A","B"):
            s=r[label]
            if s is None:continue
            s=set(s);sa=[v[:4]+v[5:7] for v in a["signature"] if v[0] in s];sb=[v[:4]+v[5:7] for v in b["signature"] if v[0] in s]
            patterns[label]={"signature_equal_endpoints":sa==sb,"counts_equal_endpoints":[m for m in a["signature_meta"] if m[0] in s]==[m for m in b["signature_meta"] if m[0] in s],"contacts_initial_positive":sum(v[3] in s and v[-1]>0 for v in a["rows"]),"contacts_final_positive":sum(v[3] in s and v[-1]>0 for v in b["rows"])}
    # Endpoints cannot establish per-cycle weight stability or credit timing.
    # Compute a deliberately optimistic conditional inhibitory sensitivity using
    # actual pattern output maxima during validation, fixed endpoint topology,
    # and maximum nominal CHEM1=31. No claim of actual opportunities.
    bounds={}
    if len(ends)==2 and labeled:
        for lab in ("A","B"):
            target=r[lab];lf=[f for f,l in zip(frames,r["labels"]) if f["index"]>=64 and l==lab]
            if not target or not lf:continue
            amp={s:max(f["concept"][s][0] for f in lf) for s in target}
            for dest in range(16):
                contacts=[v for v in ends[0]["rows"] if v[0]==dest and v[1]==1 and v[3] in amp and v[-1]>0]
                # Bound incremental weight relative to same initial LTW, all
                # susceptibility/relax/clock terms favorable; 512 ticks <=4 LTW steps.
                term=sum(max(0,(amp[v[3]]*min(255,max(v[5],v[6]+4+(max(v[4],min(255,amp[v[3]]+3))*31>>8)))>>8)-(amp[v[3]]*v[5]>>8)) for v in contacts)
                u=(min(255,term)+1)//2;d=peak=0
                for _ in range(512):
                    y=min(255,d+u);peak=max(peak,y);d=(y*0xaabb+65535)//65536
                bounds[f"{lab}:{dest}"]={"contacts":len(contacts),"optimistic_output_difference":peak}
    # Structural feasibility requires stable indexed incoming signatures at both
    # endpoints and a common pair of stable positive contacts for both cues.
    # This is not verification of credit timing; a later causal protocol needs it.
    common=[]
    if len(ends)==2 and set(patterns)=={"A","B"}:
        e0,e1=ends
        for dest in range(16):
            ok=True
            for lab in ("A","B"):
                src=set(r[lab])
                ok=ok and any(x[:4]==y[:4] and x[0]==dest and x[3] in src and x[-1]>0 and y[-1]>0 for x,y in zip(e0["rows"],e1["rows"]))
            if ok:common.append(dest)
    stable=bool(set(patterns)=={"A","B"} and all(p["signature_equal_endpoints"] and p["counts_equal_endpoints"] for p in patterns.values()))
    pair=stable and len(set(common)&set(wins))>=2
    # Single-dominant option can only support feasibility with a synchronized
    # credit measurement; this passive endpoint instrument cannot certify it.
    return {**r,"wash_end_ticks":wash,"Q":bool(wash),"labeled_winners":wins,"labeled_margins":margins,"two_alternatives":len(wins)>=2,"endpoint_source_changes":changes,"pattern_endpoint":patterns,"conditional_margin_bounds":bounds,"common_endpoint_destinations":common,"endpoint_signature_stable":stable,"credit_window_verified":False,"feasible":bool(pair),"reason":"two_free_alternatives_and_endpoint_connectivity" if pair else "no_interpretable_alternative_and_connectivity_or_credit_window"}
def self_test():
    # Construct frozen A/B discovery, then four separated episodes each, plus
    # unlabeled intervals; decisions not used for selection.
    def frame(i,s,w=1):
        v=[[0,0] for _ in range(640)]
        for j in s:v[j]=[32,5]
        return {"index":i,"tick":i,"concept":v,"winner":w,"wpre":[],"chem_pre":[0]*11,"chem_decision":[0]*11,"chem_post":[0]*11}
    fs=[frame(i,{0,1,2} if i==0 else {3,4,5} if i==1 else set()) for i in range(64)]
    for k in range(8):
        for _ in range(4):fs.append(frame(len(fs),{0,1,2} if k%2==0 else {3,4,5},k%2))
        for _ in range(8):fs.append(frame(len(fs),set()))
    a=recurrence(fs)
    assert a["A"]==[0,1,2] and a["B"]==[3,4,5] and a["recurrence"] and len(a["episodes"]["A"])==4
    assert not recurrence(fs[:65])["recurrence"]
    assert analyze(fs,[])["Q"] and analyze(fs,[])["two_alternatives"]
    for f in fs:f["chem_decision"][0]=1
    assert not analyze(fs,[])["Q"]
    assert h.parse("NL_H9_POP 0 00010000 1\n")[2]
    assert "NL_H9_END" in cmds()
    print("PASS: H09.N0 frozen patterns, recurrence episodes, chemistry and parser",flush=True)
def fixture(exe):
    exe=pathlib.Path(exe).resolve()
    with tempfile.TemporaryDirectory(prefix="nl-n0-fixture-") as td:
        root=pathlib.Path(td);scripts(root);cmd=root/"commands.txt";log=root/"trace.txt"
        body="r @$t0=poi(@esp+4); r @$t1=poi(@esp+8); r @$t2=0n11; r @$t4=0; "+pr("RB",["0"]+h.chemistry())+"; $$>a<n0pop.txt; "+h.wta("WPRE","WP")+"; "+h.wta("WPOST","WQ")+"; "+pr("RP",h.chemistry())+"; r @$t2=0n12; r @$t4=0n255; $$>a<n0pop.txt; .echo NL_H9_END; qd"
        cmd.write_text(".echo NL_H9_READY\n"+d1.bp(0,body).replace("Creatures+0x0","fixture!nl_tick")+"\ng\n",encoding="ascii")
        r={"pass":False}
        try:
            with log.open("wb") as f:p=subprocess.run([str(h.cdb_path()),"-G","-pd","-cf",str(cmd),str(exe)],cwd=root,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,timeout=45)
            ev,ct,err=h.parse(log.read_text(encoding="utf-8",errors="replace"))
            ends=[endpoint(root,ev,i) for i in (0,255)]
            base=[e for e in ev if e["tag"] in ("RB","WPRE","WP","WPOST","WQ","RP","READY","END")]
            fs,bad=h.collect(base)
            ok=p.returncode==0 and not err and not bad and len(fs)==1 and fs[0]["wta_match"] and ct.get("POP")==ct.get("POP_END")==2 and vector(root,0)==vector(root,255) and all(len(e["rows"])==4096 and len(e["signature"])==640 for e in ends)
            r={"pass":ok,"returncode":p.returncode,"counts":ct,"diagnostics":err,"frame_errors":bad,"endpoint_rows":[len(e["rows"]) for e in ends],"signature_rows":[len(e["signature"]) for e in ends]}
        except Exception as ex:r["error"]=str(ex) if type(ex) is RuntimeError and re.fullmatch("[a-z_]+",str(ex)) else type(ex).__name__
    pathlib.Path("h09-n0-fixture-result.json").write_text(json.dumps(r,indent=2),encoding="utf-8")
    print("NL_N0_FIXTURE "+json.dumps(r),flush=True);return r["pass"]
def trace(pid,root,game,launch,ident):
    cmd=root/"n0.txt";log=root/"n0.log";scripts(game);cmd.write_text(cmds(),encoding="ascii");start=time.monotonic()
    error=None;timed=False;rc=None;stop_ack=False
    def size():return log.stat().st_size+sum(f.stat().st_size for f in game.glob("n0*.bin"))
    with log.open("wb") as out:
        p=subprocess.Popen([str(h.cdb_path()),"-G","-pd","-p",str(pid),"-cf",str(cmd)],cwd=game,stdin=subprocess.DEVNULL,stdout=out,stderr=subprocess.STDOUT)
        try:
            while p.poll() is None:
                if size()>CAP-65536:raise RuntimeError("capture_cap_guard")
                if time.monotonic()-start>=175:raise RuntimeError("capture_time_guard")
                time.sleep(.15)
        except Exception as ex:
            error=str(ex) if type(ex) is RuntimeError and re.fullmatch("[a-z_]+",str(ex)) else type(ex).__name__
            if p.poll() is None:
                try:stop_ack=bool(launch.query_macro("enum 4 1 0,dde: putv 31999,next",31999).get("ok"))
                except Exception:pass
        finally:
            if p.poll() is None:
                try:p.wait(timeout=max(.1,min(3,180-(time.monotonic()-start))))
                except subprocess.TimeoutExpired:
                    timed=True;p.terminate()
                    try:p.wait(timeout=3)
                    except subprocess.TimeoutExpired:p.kill();p.wait(timeout=3)
            rc=p.returncode
    elapsed=round((time.monotonic()-start)*1000)
    raw=log.read_bytes()[:CAP].decode("utf-8","replace")
    ev,ct,err=h.parse(raw)
    fs,bad=collect(game,ev);ends=[];endpoint_errors=[]
    for i in (0,255):
        try:ends.append(endpoint(game,ev,i))
        except (OSError,RuntimeError) as ex:endpoint_errors.append({"index":i,"error":str(ex) if type(ex) is RuntimeError and re.fullmatch("[a-z_]+",str(ex)) else type(ex).__name__})
    identity=bool(ident())
    total=size()
    transport=not(err or bad or error or timed or endpoint_errors) and total<=CAP and elapsed<=180000 and rc==0 and identity and ct.get("READY")==ct.get("END")==1 and len(fs)==N and all(f["wta_match"] for f in fs)
    a=analyze(fs,ends)
    # The acquisition gate is intentionally conservative: endpoint snapshots
    # do not establish a credit interval. Never label GO from recurrence alone.
    passed=bool(transport and a["recurrence"] and a["Q"] and a["feasible"])
    classification="PASS_feasibility" if passed else ("no_opportunity" if transport else "instrumental_incomplete")
    changes=[{k:v for k,v in e.items() if k in ("tag","tick","brain","v","pos")} for e in ev if e["tag"] in ("CHANGE","ALT")]
    return {"pass":passed,"classification":classification,"transport":transport,"identity":identity,"analysis":a,"frames":fs,"endpoints":ends,"counts":ct,"diagnostics":err,"frame_errors":bad,"endpoint_errors":endpoint_errors,"observer_error":error,"changes":changes,"timeout":timed,"returncode":rc,"stop_ack":stop_ack,"trace_ms":elapsed,"private_capture_bytes":total,"raw_log_bytes":log.stat().st_size}
def main():
    self_test()
    if "--self-test" in sys.argv:return
    if "--fixture" in sys.argv:raise SystemExit(0 if fixture(sys.argv[sys.argv.index("--fixture")+1]) else 1)
    if not json.loads(pathlib.Path("h09-n0-fixture-result.json").read_text())["pass"]:raise SystemExit("fixture gate failed")
    d3.OUT=OUT;d3.RESULT=RESULT;d3.trace=trace
    import h08b_mounted_launch as launch
    save();launch.observe_one_norn=d3.observe;launch.main()
    t=RESULT.get("trace",{});a=t.get("analysis",{})
    print("NL_N0_SUMMARY "+json.dumps({"classification":RESULT["classification"],"pass":RESULT["pass"],"subject_created":RESULT["subject_created"],"transport":t.get("transport"),"frames":len(t.get("frames",[])),"endpoints":len(t.get("endpoints",[])),"A":a.get("A"),"B":a.get("B"),"recurrence":a.get("recurrence"),"validation_counts":a.get("validation_counts"),"episodes":{k:len(v) for k,v in a.get("episodes",{}).items()},"Q":a.get("Q"),"labeled_winners":a.get("labeled_winners"),"diagnostics":t.get("diagnostics"),"frame_errors":t.get("frame_errors"),"endpoint_errors":t.get("endpoint_errors"),"observer_error":t.get("observer_error"),"trace_ms":t.get("trace_ms"),"private_capture_bytes":t.get("private_capture_bytes")}),flush=True)
    if not RESULT["pass"]:raise SystemExit(1)
if __name__=="__main__":main()
