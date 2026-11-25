"""H08d.D1: minimal original C1 WTA readout. No pulses, reward, or forcing."""
import json, os, pathlib, re, shutil, subprocess, sys, time
from collections import Counter
LIMIT=20
IDENT="31306c6e"
OUT=pathlib.Path("h08d-d1-result.json")
def predict(pre,excluded,flag,active):
    if not (flag&1 and active):return list(pre)
    eligible=[i for i,v in enumerate(pre) if not excluded[i] and v>0]
    result=[0]*len(pre)
    if eligible:
        k=max(eligible,key=lambda i:pre[i])
        result[k]=pre[k]
    return result
def bp(off,cmd):
    return 'bp Creatures+0x%x "%s"'%(off,cmd.replace('"','\\"'))
def pr(tag,fmt,args):
    return '.printf "NL_D1_'+tag+' '+fmt+('\\'*2)+'n", '+', '.join(args)
def commands():
    rb=("r @$t0=@ecx; r @$t1=@esi; r @$t2=poi(@esi+0x2c20); r @$t3=1; "
        +pr("RB","%u %08x %08x",["@$t2","@$t1","@$t0"])+"; gc")
    def cells(phase):
        body=(pr(phase,"%u %u %u %u",["@$t2","poi(@ebx+0xa4)","by(@ebx+0x22)","poi(@ebx+0xb0)"])
          +"; r @$t5=poi(@ebx+0x9c); "
          +".for (r @$t6=0; @$t6<0x10; r @$t6=@$t6+1) { r @$t7=@$t5+@$t6*0x10; "
          +pr(phase+"_CELL","%u %u %u %u",["@$t2","@$t6","by(@$t7+2)","by(@$t7+0xe)"])+" }; gc")
        return (".if (@$t3==1) { .if (@ebx==@$t0+0x4b8) { .if (poi(@ebx+0xa4)==0x10) { "
           +body+" } .else { .echo NL_D1_LAYOUT_BAD; qd } } .else { gc } } .else { gc }")
    rp=(".if (@$t3==1) { "+pr("RP","%u %08x %08x",["poi(@esi+0x2c20)","@esi","poi(@esi+0x2c18)"])
       +"; r @$t3=0; r @$t4=@$t4+1; .if (@$t4>=0n20) { .echo NL_D1_END; qd } .else { gc } } .else { gc }")
    return "\n".join([".echo NL_D1_READY","r @$t0=0","r @$t1=0","r @$t2=0","r @$t3=0","r @$t4=0",
       bp(0x7583,rb),bp(0x48a0,cells("PRE")),bp(0x4911,cells("POST")),bp(0x759a,rp),"g"])+"\n"
EVENT=re.compile(r"^NL_D1_(RB|RP|PRE|POST|PRE_CELL|POST_CELL) ([0-9a-fA-F ]+)$")
EXPECTED=["RB","PRE"]+["PRE_CELL"]*16+["POST"]+["POST_CELL"]*16+["RP"]
def parse(raw):
    counts=Counter(); errors=Counter(); cycles=[]; current=None; subject=None; stable=True
    ready=end=0
    for line in raw.splitlines():
        s=line.strip()
        if not s.startswith("NL_D1_"):continue
        if s=="NL_D1_READY":ready+=1;continue
        if s=="NL_D1_END":end+=1;continue
        if s=="NL_D1_LAYOUT_BAD":errors["layout"]+=1;continue
        m=EVENT.fullmatch(s)
        if not m:errors["unrecognized_marker_shape"]+=1;continue
        tag=m.group(1);a=m.group(2).split();counts[tag]+=1
        try:
            tick=int(a[0])
            if tag in ("RB","RP"):
                if len(a)!=3 or not all(re.fullmatch(r"[0-9a-fA-F]{8}",x) for x in a[1:]):raise ValueError()
                ident=tuple(int(x,16) for x in a[1:])
                if not all(x>0 for x in ident):raise ValueError()
                if subject is None:subject=ident
                if ident!=subject:stable=False
            if tag=="RB":
                if current is not None:errors["nested_regular"]+=1
                current={"tick":tick,"events":[tag],"pre":[],"post":[]}
                continue
            if current is None:errors["orphan_event"]+=1;continue
            if tick!=current["tick"]:errors["tick_mismatch"]+=1
            current["events"].append(tag)
            if tag=="RP":
                complete=current["events"]==EXPECTED and len(current["pre"])==len(current["post"])==16
                current["complete"]=complete
                if complete:
                    pre=[r[1] for r in current["pre"]];exc=[r[2] for r in current["pre"]]
                    post=[r[1] for r in current["post"]]
                    indices=all([r[0] for r in current[k]]==list(range(16)) for k in ("pre","post"))
                    if not indices:errors["cell_order"]+=1;current["complete"]=False
                    flag,active=current["PRE_meta"][1:]
                    if not flag&1 or not current["POST_meta"][1]&1:errors["wta_flag"]+=1
                    expected=predict(pre,exc,flag,active);positives=[i for i,v in enumerate(post) if v]
                    eligible=[v for v,e in zip(pre,exc) if not e and v>0]
                    current.update({"pre_outputs":pre,"excluded":exc,"post_outputs":post,
                        "predicted":expected,"match":expected==post,"wta_branch":bool(flag&1 and active),
                        "positive_opportunity":bool(flag&1 and active and eligible),
                        "pre_tie":bool(eligible and eligible.count(max(eligible))>1),
                        "winner":positives[0] if len(positives)==1 else None,
                        "post_positive_count":len(positives)})
                cycles.append(current);current=None;continue
            if len(a)!=4:raise ValueError()
            vals=list(map(int,a[1:]))
            if tag in ("PRE","POST"):
                if vals[0]!=16 or not 0<=vals[1]<=255 or vals[2]<0:raise ValueError()
                if tag+"_meta" in current:errors["duplicate_meta"]+=1
                current[tag+"_meta"]=vals
            else:
                if not 0<=vals[0]<16 or not all(0<=v<=255 for v in vals[1:]):raise ValueError()
                current["pre" if tag=="PRE_CELL" else "post"].append(vals)
        except (ValueError,IndexError,KeyError):
            errors["malformed_numeric_or_order"]+=1
    if current is not None:errors["unfinished_regular"]+=1
    for k,p in (("syntax",r"Syntax error|Extra character|Illegal"),("access",r"Memory access error|Unable to read|access violation"),
                ("breakpoint",r"Unable to resolve|Couldn't resolve|Unable to insert breakpoint|Couldn't set breakpoint"),
                ("operand",r"Operand error|Bad register|Invalid register"),("quote",r"unterminated|quote.*error")):
        if re.search(p,raw,re.I):errors[k]+=1
    longest=seq=0;last=None
    for f in cycles:
        if f.get("complete") and f.get("match"):
            seq=seq+1 if last is not None and f["tick"]==last+1 else 1
            longest=max(longest,seq);last=f["tick"]
        else:seq=0;last=None
    complete=[f for f in cycles if f.get("complete")]
    return {"ready_count":ready,"end_count":end,"event_counts":dict(counts),"diagnostics":dict(errors),
        "same_subject_brain":stable and subject is not None,"cycles":cycles,"regular_cycles":len(cycles),
        "complete_cycles":len(complete),"longest_consecutive_matches":longest,
        "matched_cycles":sum(f.get("match",False) for f in complete),
        "positive_opportunities":sum(f.get("positive_opportunity",False) for f in complete),
        "wta_branches":sum(f.get("wta_branch",False) for f in complete),
        "pre_ties":sum(f.get("pre_tie",False) for f in complete),
        "multiple_outputs":sum(f.get("post_positive_count",0)>1 for f in complete),
        "no_output":sum(f.get("post_positive_count",0)==0 for f in complete),
        "raw_bytes":len(raw.encode("utf-8")),"raw_lines":len(raw.splitlines())}
def self_test():
    assert predict([3,9,9,11],[0,0,0,1],1,4)==[0,9,0,0]
    assert predict([3,4],[0,0],0,4)==[3,4]
    assert predict([0,0],[0,0],1,0)==[0,0]
    pre=[0]*16;pre[2]=6;pre[5]=6;pre[3]=10
    excluded=[0]*16;excluded[3]=1
    post=predict(pre,excluded,1,4)
    raw=["NL_D1_READY","NL_D1_RB 10 00010000 00020000","NL_D1_PRE 10 16 1 4"]
    raw += [f"NL_D1_PRE_CELL 10 {i} {pre[i]} {excluded[i]}" for i in range(16)]
    raw += ["NL_D1_POST 10 16 1 4"]+[f"NL_D1_POST_CELL 10 {i} {post[i]} {excluded[i]}" for i in range(16)]
    raw += ["NL_D1_RP 10 00010000 00020000","NL_D1_END"]
    r=parse("\n".join(raw))
    assert r["complete_cycles"]==r["matched_cycles"]==r["positive_opportunities"]==r["pre_ties"]==1
    assert r["cycles"][0]["winner"]==2 and not r["diagnostics"]
    assert parse("\n".join(raw[:5]+raw[6:]))["complete_cycles"]==0
    assert not parse('0:000> .printf "NL_D1_RB 10 00010000 00020000"')["event_counts"]
    assert parse("\n".join(raw[:-2]+["NL_D1_RP 10 00010000 00030000","NL_D1_END"]))["same_subject_brain"] is False
    print("PASS: synthetic WTA rule, parser, identity and incomplete frame",flush=True)
def save(result):
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
def trace(pid,root,game):
    cdb=pathlib.Path(os.environ["ProgramFiles(x86)"])/"Windows Kits"/"10"/"Debuggers"/"x86"/"cdb.exe"
    cmd=root/"h08d-d1.txt";cmd.write_text(commands(),encoding="ascii")
    log=root/"h08d-d1.log";start=time.monotonic();ret=None;timed=False
    try:
        with log.open("wb") as f:
            p=subprocess.run([str(cdb),"-G","-pd","-p",str(pid),"-cf",str(cmd)],cwd=game,
                 stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,timeout=45)
        ret=p.returncode
    except subprocess.TimeoutExpired:timed=True
    raw=log.read_bytes().decode("utf-8","replace") if log.exists() else ""
    return {**parse(raw),"returncode":ret,"timeout":timed,"elapsed_ms":round((time.monotonic()-start)*1000)}
RESULT={"stage":"H08d.D1","subject_created":False,"classification":"launcher_not_reached","pass":False,"stimuli":0,"reward_pulses":0}
def observe(game,pid,root):
    import h08b_mounted_launch as launch
    q=launch.query_macro;base=launch.base
    def ident():
        return q("dde: putv totl 4 1 0",1).get("ok") and q("enum 4 1 0,dde: getb monk,next",IDENT,"moniker").get("ok")
    error=None
    try:
        if not q("dde: putv totl 4 1 0",0).get("ok"):raise RuntimeError("world_not_empty")
        dest=game/"Genetics"/"NL01.gen"
        if dest.exists():raise RuntimeError("moniker_collision")
        shutil.copyfile(game/"Genetics"/"dad1.gen",dest)
        if base.digest(dest)!=base.GEN:raise RuntimeError("genome_mismatch")
        if not q("new: crea tokn nl01 1,mvto 2408 870,dde: putv totl 4 1 0",1).get("ok"):raise RuntimeError("birth_transport")
        RESULT["subject_created"]=True;save(RESULT)
        end=time.perf_counter()+85
        while time.perf_counter()<end:
            time.sleep(min(5,max(0,end-time.perf_counter())))
            if not q("dde: putv 123",123).get("ok"):raise RuntimeError("initialization_dde")
        RESULT["identity_before"]=bool(ident())
        if not RESULT["identity_before"]:raise RuntimeError("identity_before")
        r=trace(pid,root,game);RESULT["trace"]=r
        RESULT["identity_after"]=bool(ident())
        gate={"transport":r["returncode"]==0 and not r["timeout"] and r["ready_count"]==r["end_count"]==1 and not r["diagnostics"],
              "identity":r["same_subject_brain"] and RESULT["identity_before"] and RESULT["identity_after"],
              "bound":8<=r["regular_cycles"]<=LIMIT,
              "consecutive":r["longest_consecutive_matches"]>=8,
              "match":r["complete_cycles"]==r["matched_cycles"] and r["complete_cycles"]>=8,
              "opportunity":r["positive_opportunities"]>=1}
        RESULT["gate_checks"]=gate;RESULT["pass"]=all(gate.values())
        RESULT["classification"]="PASS_minimal_WTA" if RESULT["pass"] else ("no_opportunity" if all(gate[k] for k in gate if k!="opportunity") else "instrumental_incomplete_or_prediction_mismatch")
    except Exception as e:
        error=str(e) if type(e) is RuntimeError and re.fullmatch(r"[a-z_]+",str(e)) else type(e).__name__
        RESULT["classification"]="instrumental_failure";RESULT["error"]=error
    finally:
        save(RESULT)
        r=RESULT.get("trace",{})
        base.emit(gate="h08d_d1_result",classification=RESULT["classification"],passed=RESULT["pass"],subject_created=RESULT["subject_created"],gate_checks=RESULT.get("gate_checks"),error=error,
            trace_summary={k:v for k,v in r.items() if k!="cycles"})
def main():
    self_test()
    if "--self-test" in sys.argv:return
    save(RESULT)
    sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"inherited"/"experiments"/"neurolab"))
    import h08b_mounted_launch as launch
    launch.observe_one_norn=observe
    launch.main()
    if not RESULT["pass"]:raise SystemExit(1)
if __name__=="__main__":main()
