"""D2: isolated native stimulus delivery, not learning."""
import json, pathlib, sys, shutil, time
OUT=pathlib.Path("h08d-d2-result.json")
ARMS=[("S8",8,False),("S9",9,False),("A8",8,True),("B9",9,True)]
RESULT={"stage":"H08d.D2","subject_created":False,"classification":"launcher_not_reached","pass":False,"order":[x[0] for x in ARMS],"arms":[],"reward_pulses":0,"trig_attempts":0}
def valid(r):
    v=r.get("value")
    return r.get("ok") is True and isinstance(v,list) and len(v)==7 and all(type(x) is int and x>=0 for x in v) and max(v[:2])<=255
def gate(before,after,pulse):
    if not valid(before) or not valid(after):return False
    a,b=before["value"][:2],after["value"][:2]
    return all(x<32 for x in a) and b==[32,32] if pulse else all(y<=x for x,y in zip(a,b))
def self_test():
    def c(a,b):return {"ok":True,"value":[a,b,0,0,0,0,0]}
    assert gate(c(0,0),c(32,32),True)
    assert not gate(c(32,0),c(32,32),True)
    assert not gate(c(0,0),c(32,31),True)
    assert gate(c(8,8),c(0,8),False)
    assert not gate(c(0,0),c(1,0),False)
    assert not valid(c(256,0)) and not valid({"ok":True,"value":[1,2]})
    print("PASS: D2 readout eligibility and sham/pulse gate",flush=True)
def save():OUT.write_text(json.dumps(RESULT,indent=2,sort_keys=True)+"\n",encoding="utf-8")
def require(ok,msg):
    if not ok:raise RuntimeError(msg)
def observe(game,pid,root):
    import h08b_mounted_launch as launch
    base=launch.base
    origin=time.perf_counter_ns()
    def q(cmd,expected=None,kind="number"):
        t=time.perf_counter_ns();r=launch.query_macro(cmd,expected,kind)
        return {**r,"start_us":(t-origin)//1000,"end_us":(time.perf_counter_ns()-origin)//1000}
    def n(cmd,expected=None,kind="number"):return q("enum 4 1 0,"+cmd+",next",expected,kind)
    def ident():return bool(q("dde: putv totl 4 1 0",1)["ok"] and n("dde: getb monk","31306c6e","moniker")["ok"])
    def cell(i):return n(f"dde: cell 5 {i} 0",kind="cell")
    def context():
        return {k:n("dde: putv "+k) for k in ("chem 49","chem 50","chem 51","chem 54","chem 55","cage","aslp","ins#","dead")}
    try:
        require(q("dde: putv totl 4 1 0",0)["ok"],"world_not_empty")
        dest=game/"Genetics"/"NL01.gen"
        require(not dest.exists(),"moniker_collision")
        shutil.copyfile(game/"Genetics"/"dad1.gen",dest)
        require(base.digest(dest)==base.GEN,"genome_mismatch")
        require(q("new: crea tokn nl01 1,mvto 2408 870,dde: putv totl 4 1 0",1)["ok"],"birth_transport")
        RESULT["subject_created"]=True;save()
        start=time.monotonic()
        while time.monotonic()-start<85:
            time.sleep(min(5,max(0,85-(time.monotonic()-start))))
            require(q("dde: putv 123",123)["ok"],"initialization_dde")
        require(ident(),"initial_identity")
        for label,i,pulse in ARMS:
            row={"arm":label,"cell":i,"pulse":pulse,"identity_before":ident(),"passed":False}
            RESULT["arms"].append(row);save()
            require(row["identity_before"],"pre_identity")
            row["context"]=context()
            other=17-i
            row["other_before"]=cell(other);row["before"]=cell(i)
            require(valid(row["before"]) and valid(row["other_before"]),"invalid_cell_baseline")
            if pulse and not all(x<32 for x in row["before"]["value"][:2]):
                row["classification"]="no_opportunity";save()
                raise RuntimeError("no_opportunity")
            cmd=f"dde: cell 5 {i} 0"
            if pulse:
                cmd=f"trig 5 {i} 32,"+cmd
                RESULT["trig_attempts"]+=1;save()
            row["after"]=n(cmd,kind="cell")
            row["other_after"]=cell(other);row["identity_after"]=ident()
            require(valid(row["after"]) and valid(row["other_after"]),"invalid_cell_after")
            require(row["identity_after"],"post_identity")
            row["passed"]=gate(row["before"],row["after"],pulse)
            row["classification"]="pass" if row["passed"] else "delivery_or_sham_mismatch"
            save()
            if not row["passed"]:raise RuntimeError("delivery_or_sham_mismatch")
            if label!="B9":time.sleep(2)
        RESULT["pass"]=len(RESULT["arms"])==4 and all(x["passed"] for x in RESULT["arms"])
        RESULT["classification"]="PASS_local_delivery" if RESULT["pass"] else "incomplete"
    except Exception as e:
        msg=str(e) if type(e) is RuntimeError else type(e).__name__
        allowed={"world_not_empty","moniker_collision","genome_mismatch","birth_transport","initialization_dde","initial_identity","pre_identity","invalid_cell_baseline","no_opportunity","invalid_cell_after","post_identity","delivery_or_sham_mismatch"}
        RESULT["error"]=msg if msg in allowed else type(e).__name__
        RESULT["classification"]="no_opportunity" if msg=="no_opportunity" else ("observed_mismatch" if msg=="delivery_or_sham_mismatch" else "instrumental_failure")
    finally:save()
def main():
    self_test()
    if "--self-test" in sys.argv:return
    save()
    sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"inherited"/"experiments"/"neurolab"))
    import h08b_mounted_launch as launch
    launch.observe_one_norn=observe
    launch.main()
    # Print only bounded derived values; no IDs, raw logs, or original assets.
    print("NL_D2_RESULT "+json.dumps(RESULT,sort_keys=True),flush=True)
    if not RESULT["pass"]:raise SystemExit(1)
if __name__=="__main__":main()
