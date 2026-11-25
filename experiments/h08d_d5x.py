"""D5x: observe the native attention-change reset, not a D5 rerun."""
import json,pathlib,re,sys
from collections import Counter
import h08d_d4 as d4
import h08d_d3 as d3
OUT=pathlib.Path("h08d-d5x-result.json")
RESULT={"stage":"H08d.D5x.1","subject_created":False,"pass":False,"classification":"launcher_not_reached","trig_attempts":0,"reward_pulses":0,"arms":[]}
BASE_COMMANDS=d4.commands;BASE_PARSE=d4.parse;BASE_ANALYZE=d4.analyze
def save():OUT.write_text(json.dumps(RESULT,indent=2,sort_keys=True)+"\n",encoding="utf-8")
def pr(tag,args):
    fmt=" ".join(["%08x" if i==1 else "%u" for i in range(len(args))])
    return d3.pr(tag,fmt,args).replace("NL_D3_","NL_DX_")
def commands():
    base=BASE_COMMANDS().splitlines()
    tick="poi(@esi+0x2c20)"
    brain="poi(@esi+0x2c18)"
    sense=d4.cells("@$t0",5,(8,9))
    start="r @$t10=poi(@esi+0x7f0); r @$t11=poi(@esp); "+pr("CHANGE_PRE",[tick,brain,"@ebx","(@$t10!=@$t11)","(@$t10!=0)","(@$t11!=0)"]+sense)
    after=pr("CHANGE_POST",[tick,brain,"@ebx","(poi(@esi+0x7f0)==@$t11)"]+sense)
    row=["by(poi(@$t0+0x48c)+@edi*0x10+2)","by(poi(@$t0+0x48c)+@edi*0x10+3)"]
    pre=pr("CLEAR_PRE",[tick,brain,"@edi","poi(@esp)","poi(@esp+4)","poi(@esp+8)"]+row)
    post=pr("CLEAR_POST",[tick,brain,"@edi"]+row)
    def guard(s,check=""):
        return ".if ((@$t0!=0)&("+brain+"==@$t0)"+check+") { "+s+"; gc } .else { gc }"
    bp=[d3.bp(0x9cf8,guard(start)),d3.bp(0x9cfd,guard(after)),d3.bp(0x9d22,guard(pre,"&(@ecx==@$t0)")),d3.bp(0x9d27,guard(post))]
    return "\n".join(base[:-1]+["r @$t10=0","r @$t11=0"]+bp+["g"])+"\n"
def parse(raw,final=True):
    ev,ct,err=BASE_PARSE(raw,final)
    aliases={};ordered=[];extras=[];i=0
    def brain(x):
        if not re.fullmatch("[0-9a-fA-F]{8}",x) or int(x,16)==0:raise ValueError()
        return aliases.setdefault(x.lower(),"B"+str(len(aliases)+1))
    for line in raw.splitlines():
        s=line.strip()
        if s.startswith("NL_D4_"):
            a=s.split();tag=a[0][6:]
            try:
                if tag in d4.ORDER or tag in ("PULSE_PRE","PULSE_POST"):
                    brain(a[1] if tag.startswith("PULSE_") else a[2])
                if i<len(ev) and ev[i]["tag"]==tag:
                    ordered.append(("D4",ev[i]));i+=1
            except (ValueError,IndexError):err["DX_alias"]=1
        elif s.startswith("NL_DX_"):
            a=s.split();tag=a[0][6:]
            try:
                n={"CHANGE_PRE":8,"CHANGE_POST":6,"CLEAR_PRE":6,"CLEAR_POST":3}[tag]
                if len(a)!=n+3 or not a[1].isdigit() or not all(x.isdigit() for x in a[3:]):raise ValueError()
                x={"tag":tag,"tick":int(a[1]),"brain":brain(a[2]),"v":list(map(int,a[3:]))}
                extras.append(x);ordered.append(("DX",x))
            except (ValueError,IndexError,KeyError):err["DX_malformed_marker"]=err.get("DX_malformed_marker",0)+1
    if i!=len(ev):err["DX_order_mapping"]=1
    return {"d4":ev,"dx":extras,"ordered":ordered},ct,err
def diagnose(packet,base):
    ordered=packet["ordered"];r={"markers":len(packet["dx"]),"changes":[],"witnesses":[],"incomplete_groups":0,"classification":"no_opportunity"}
    # Validate every full block of 32 indexed clears, including inactive controls.
    block=None;prev_pulse=None;last_phase=None
    def finish(b):
        if b is None:return
        if len(b["events"])!=66:
            r["incomplete_groups"]+=1;return
        e=b["events"];p,q=e[:2]
        valid=p["tag"]=="CHANGE_PRE" and q["tag"]=="CHANGE_POST" and len({(x["tick"],x["brain"]) for x in e})==1
        valid=valid and p["v"][1]==1 and q["v"][1]==1 and p["v"][0]==q["v"][0] and 0<=p["v"][0]<40 and all(v in (0,1) for v in p["v"][1:4])
        pairs=[]
        for j in range(32):
            a,z=e[2+2*j:4+2*j]
            valid=valid and a["tag"]=="CLEAR_PRE" and z["tag"]=="CLEAR_POST" and a["v"][:4]==[j,5,j,0] and z["v"]==[j,0,0] and all(0<=v<=255 for v in a["v"][4:])
            pairs.append({"index":j,"pre":a["v"][4:],"post":z["v"][1:]})
        group={"tick":p["tick"],"brain":p["brain"],"candidate_class":p["v"][0],"old_present":p["v"][2],"new_present":p["v"][3],"before":p["v"][4:],"after_setter":q["v"][2:],"pairs":pairs,"valid":bool(valid)}
        r["changes"].append(group)
        if not valid:return
        # No attribution without a pulse marker, a positive value, and the following PRE.
        for j in (8,9):
            a=pairs[j]
            if not any(a["pre"]) or b["pulse"] is None or b["pulse"]["cell"]!=j or b["last_phase"] is None:continue
            off=2*(j-8)
            if b["last_phase"]["v"][10+off:12+off]!=a["pre"]:continue
            nxt=next((x for kind,x in ordered[b["end"]+1:] if kind=="D4" and x["tag"] in ("PRE","PULSE_PRE","PULSE_POST")),None)
            if nxt is None or nxt["tag"]!="PRE" or nxt["brain"]!=p["brain"] or nxt["route"]!="regular":continue
            if nxt["tick"] not in (p["tick"],p["tick"]+1) or nxt["v"][10+off:12+off]!=[0,0]:continue
            r["witnesses"].append({"cell":j,"reset_tick":p["tick"],"next_pre_tick":nxt["tick"],"pre":a["pre"],"post":a["post"],"next_pre":[0,0],"candidate_class":p["v"][0],"pulse":b["pulse"]})
    for pos,(kind,x) in enumerate(ordered):
        if kind=="D4":
            if x["tag"]=="PULSE_PRE":prev_pulse={"cell":x["args"][1],"args":x["args"],"brain":x["brain"],"valid":x["args"] in ([5,8,32],[5,9,32]) and x["in_cycle"]==0}
            elif x["tag"]=="PULSE_POST":
                if prev_pulse and prev_pulse["valid"] and prev_pulse["brain"]==x["brain"]:
                    off=2*(prev_pulse["cell"]-8);prev_pulse["valid"]=x["v"][10+off:12+off]==[32,32]
                else:prev_pulse=None
                last_phase=x
            elif x["tag"] in ("PRE","POST","COPY","PERCEPTION"):last_phase=x
            if block is not None:
                block["end"]=pos-1;finish(block);block=None
        elif x["tag"]=="CHANGE_PRE":
            if block is not None:block["end"]=pos-1;finish(block)
            block={"events":[x],"pulse":prev_pulse.copy() if prev_pulse and prev_pulse["valid"] else None,"last_phase":last_phase,"end":pos}
        elif block is not None:
            block["events"].append(x);block["end"]=pos
            if len(block["events"])==66:finish(block);block=None
        else:r["incomplete_groups"]+=1
    if block is not None:finish(block)
    if any(not c["valid"] for c in r["changes"]) or r["incomplete_groups"]:r["classification"]="instrumental_incomplete"
    elif r["witnesses"]:r["classification"]="observed_attention_change_reset"
    elif base.get("classification")=="observed_conditional_divergence":r["classification"]="unattributed_divergence"
    return r
def analyze(packet,final=False):
    base=BASE_ANALYZE(packet["d4"],final)
    base["diagnosis"]=diagnose(packet,base)
    return base
def self_test():
    d4.self_test()
    brain="B1";v=[32,0,24,0,0,112,10,0,0,0]+[0,0,32,21,0,0,22,0]
    e=[("D4",{"tag":"PULSE_PRE","brain":brain,"args":[5,9,32],"in_cycle":0}),("D4",{"tag":"PULSE_POST","brain":brain,"v":v[:10]+[0,0,32,32,0,0,0,0]}),("D4",{"tag":"PERCEPTION","brain":brain,"v":v,"tick":503})]
    def dx(tag,val):return ("DX",{"tag":tag,"tick":503,"brain":brain,"v":val})
    e += [dx("CHANGE_PRE",[4,1,1,1,0,0,32,21]),dx("CHANGE_POST",[4,1,0,0,32,21])]
    for j in range(32):e += [dx("CLEAR_PRE",[j,5,j,0]+([32,21] if j==9 else [0,0])),dx("CLEAR_POST",[j,0,0])]
    e += [("D4",{"tag":"PRE","brain":brain,"route":"regular","tick":504,"v":v[:10]+[0]*8})]
    packet={"ordered":e,"dx":[x for k,x in e if k=="DX"]}
    r=diagnose(packet,{})
    assert r["classification"]=="observed_attention_change_reset" and len(r["witnesses"])==1
    assert diagnose({"ordered":e[:-1],"dx":packet["dx"]},{})["classification"]=="no_opportunity"
    assert diagnose({"ordered":e[:15]+e[16:],"dx":packet["dx"]},{})["classification"]=="instrumental_incomplete"
    raw="NL_DX_CHANGE_PRE 503 00010000 4 1 1 1 0 0 32 21\n"
    p,ct,err=parse(raw);assert not err and len(p["dx"])==1
    assert "NL_DX_CLEAR_PRE" in commands()
    print("PASS: D5x synthetic reset sequence and no-opportunity/corruption controls",flush=True)
def main():
    self_test()
    if "--self-test" in sys.argv:return
    d4.commands=commands;d4.parse=parse;d4.analyze=analyze;d4.RESULT=RESULT;d4.save=save
    d3.OUT=OUT;d3.RESULT=RESULT;d3.trace=d4.trace
    import h08b_mounted_launch as launch
    save();launch.observe_one_norn=d3.observe;launch.main()
    t=RESULT.get("trace",{});a=t.get("analysis",{});diag=a.get("diagnosis",{})
    checks=t.get("gate_checks",{})
    valid=all(checks.get(k) for k in ("transport","identity","ack")) and not t.get("observer_error")
    RESULT["d4_pass"]=RESULT["pass"]
    RESULT["pass"]=bool(valid and diag.get("classification")=="observed_attention_change_reset")
    RESULT["classification"]=diag.get("classification","instrumental_incomplete") if valid else "instrumental_incomplete_or_partial_witness"
    save()
    print("NL_DX_SUMMARY "+json.dumps({"classification":RESULT["classification"],"pass":RESULT["pass"],"d4_pass":RESULT["d4_pass"],"subject_created":RESULT["subject_created"],"trig_attempts":RESULT["trig_attempts"],"gate_checks":checks,"markers":diag.get("markers"),"changes":len(diag.get("changes",[])),"incomplete_groups":diag.get("incomplete_groups"),"witnesses":diag.get("witnesses"),"event_counts":t.get("event_counts"),"diagnostics":t.get("diagnostics"),"observer_error":t.get("observer_error")}),flush=True)
    if not RESULT["pass"]:raise SystemExit(1)
if __name__=="__main__":main()
