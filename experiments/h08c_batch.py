"""H08c.1 session 1: original C1 native sensory pulses, read-only synchronized observation.
No CHEM, no Decision forcing, no direct state or weight writes. Calibration, not learning.
Raw debugger stream remains private in memory; only derived indices, bytes and event times persist.
"""
import ctypes as c
import json, os, pathlib, random, re, shutil, struct, subprocess, sys, threading, time
from collections import Counter
from pathlib import Path

SESSION=int(os.environ.get("NL_SESSION","2"))
require_session=SESSION in (2,3)
if not require_session:raise ValueError("unregistered session")
SEED=10800+SESSION
ORDER=["A"]*4+["B"]*4+["S"]*4
random.Random(SEED).shuffle(ORDER)
SIZE={0:112,5:32,6:16,8:640}
IDENT="31306c6e"
CHEM=(49,50,51,54,55)
RESULT=None

class InstrumentError(RuntimeError): pass
def require(ok,code):
    if not ok: raise InstrumentError(code)
def uint(b,off=0): return struct.unpack_from("<I",b,off)[0]
def lobe(brain,k): return brain+8+200*k
def sigset(frame):
    return { (x["cell"],tuple(sorted(x["sources"]))) for x in frame.get("concept_pre",[]) }
def wta_expected(before,excluded,active,flag):
    if not active or not flag: return list(before)
    best=max((v for v,e in zip(before,excluded) if not e),default=0)
    result=[0]*len(before)
    if best:
        k=next(i for i,(v,e) in enumerate(zip(before,excluded)) if not e and v==best)
        result[k]=best
    return result
def winner(out):
    pos=[i for i,v in enumerate(out) if v>0]
    return pos[0] if len(pos)==1 else None
def similarity(a,b):
    return len(a&b)/len(a|b) if a and b else 0.0
def classify(a,protos):
    s=[similarity(a,protos[k]) for k in ("A","B")]
    return ("A" if s[0]>s[1] else "B") if max(s)>=0.5 and s[0]!=s[1] else None
def zero_chem(v):
    # bloodstream reward/punishment/reinforcement/echoes, Decision CHEM0/1, Concept CHEM0
    return len(v)==10 and all(v[i]==0 for i in (0,1,2,3,4,5,6,9))
def longest_wash(frames):
    count=best=0; last=None
    for f in frames:
        good=(f.get("complete") and zero_chem(f.get("chem_pre",[])) and zero_chem(f.get("chem_post",[])))
        count=(count+1 if last is not None and f["tick"]==last+1 else 1) if good else 0
        best=max(best,count);last=f["tick"]
    return best

def self_test():
    assert wta_expected([3,9,9,11],[0,0,0,1],4,True)==[0,9,0,0]
    assert wta_expected([0,0],[0,0],0,True)==[0,0]
    assert wta_expected([3,4],[0,0],2,False)==[3,4]
    assert winner([0,8,0])==1 and winner([1,1]) is None and winner([0,0]) is None
    assert classify({(1,(2,))},{"A":{(1,(2,))},"B":{(1,(3,))}})=="A"
    assert classify({(1,(2,))},{"A":{(1,(2,))},"B":{(1,(2,))}}) is None
    assert classify(set(),{"A":{(1,(2,))},"B":set()}) is None
    fs=[{"tick":i,"complete":True,"chem_pre":[0]*10,"chem_post":[0]*10} for i in range(10)]
    assert longest_wash(fs)==10
    fs[4]["chem_pre"][0]=1
    assert longest_wash(fs)==5
    fs[7]["tick"]=99
    assert longest_wash(fs)==4
    assert Counter(ORDER)=={"A":4,"B":4,"S":4}
    assert uint(bytes([2,1,0,0]))==258
    reader=SnapshotReader();out=[]
    parser=BatchParser(reader,lambda k,a:out.append((k,a,reader.read(0x10000,20))))
    for line in ["NL_EVT RB 1 2 3","NL_BUF 00010000 20","00010000  00 01 02 03 04 05 06 07-08 09 0a 0b 0c 0d 0e 0f  ................","00010010  10 11 12 13                                      ....","NL_END"]:
        parser.line(line)
    assert out==[("RB",["1","2","3"],bytes(range(20)))]
    assert "NL_OBSERVER_READY" in commands() and "NL_END; gc" in commands()
    print("PASS: synthetic batch parser, WTA, signatures, wash and allocation",flush=True)

class Reader:
    def __init__(self,pid):
        k=c.WinDLL("kernel32",use_last_error=True);self.k=k
        k.OpenProcess.argtypes=[c.c_uint32,c.c_int,c.c_uint32];k.OpenProcess.restype=c.c_void_p
        k.ReadProcessMemory.argtypes=[c.c_void_p,c.c_void_p,c.c_void_p,c.c_size_t,c.POINTER(c.c_size_t)]
        k.ReadProcessMemory.restype=c.c_int
        k.CloseHandle.argtypes=[c.c_void_p];k.CloseHandle.restype=c.c_int
        self.handle=k.OpenProcess(0x1010,False,pid)
        require(bool(self.handle),"read_handle")
    def close(self):
        self.k.CloseHandle(self.handle)
    def read(self,p,n):
        require(0x10000<=p<=0xffffffff and 0<n<=65536 and p+n<=0x100000000,"read_bounds")
        b=(c.c_ubyte*n)();got=c.c_size_t()
        ok=self.k.ReadProcessMemory(self.handle,c.c_void_p(p),b,n,c.byref(got))
        require(ok and got.value==n,"read_exact")
        return bytes(b)
    def ptr(self,p):return uint(self.read(p,4))
    def cells(self,brain,k):
        p=lobe(brain,k); h=self.read(p,200); n=uint(h,0xa4); start=uint(h,0x9c)
        require(n==SIZE[k],"lobe_size")
        b=self.read(start,n*16)
        return start,[b[i*16:(i+1)*16] for i in range(n)],h
    def sense(self,brain):
        _,cells,_=self.cells(brain,5)
        return [[cells[i][2],cells[i][3]] for i in (8,9)]
    def chem(self,norn,brain):
        p=self.ptr(norn+0x2c1c);b=self.read(p,8+2*56)
        return [b[8+2*x] for x in CHEM]+list(self.read(lobe(brain,6)+0xc3,4))+list(self.read(lobe(brain,8)+0xc3,1))
    def concept(self,brain):
        p0,per,_=self.cells(brain,0)
        pc,cells,_=self.cells(brain,8)
        out=[x[2] for x in cells]; active=[]
        for i,x in enumerate(cells):
            if not x[2]:continue
            n=x[12];require(1<=n<=3 and x[13]==0,"concept_dendrite_count")
            data=self.read(uint(x,4),n*12);src=[];slots=[]
            for j in range(n):
                d=data[j*12:(j+1)*12];p=uint(d)
                require(p0<=p<p0+16*len(per) and (p-p0)%16==0,"concept_source")
                idx=(p-p0)//16
                slots.append([idx,*d[6:10]])
                if d[9]>0:src.append(idx)
            active.append({"cell":i,"output":x[2],"sources":src,"contacts":slots})
        return pc,out,active,[x[2] for x in per]
    def decision_contacts(self,brain,pc,concept_out,previous=None):
        _,cells,h=self.cells(brain,6)
        rows=[]
        selected=None if previous is None else {(x[0],x[1],x[2]) for x in previous}
        for i,x in enumerate(cells):
            require(x[12]==128 and x[13]==128,"decision_dendrite_count")
            for typ in (0,1):
                if selected is not None and not any(a==i and b==typ for a,b,_ in selected):continue
                data=self.read(uint(x,4+4*typ),128*12)
                for j in range(128):
                    if selected is not None and (i,typ,j) not in selected:continue
                    d=data[j*12:(j+1)*12];p=uint(d)
                    require(pc<=p<pc+16*len(concept_out) and (p-pc)%16==0,"decision_source")
                    idx=(p-pc)//16
                    if selected is not None or concept_out[idx]>0:
                        rows.append([i,typ,j,idx,*d[6:10]])
        return rows

# Batch CDB transport: commands read memory while target is stopped and immediately gc.
# No interactive debugger stdin handshake. Raw addresses/dumps exist only in temp log.
class SnapshotReader(Reader):
    def __init__(self):self.blocks={}
    def reset(self):self.blocks={}
    def close(self):pass
    def read(self,p,n):
        require(0x10000<=p<=0xffffffff and 0<n<=65536 and p+n<=0x100000000,"read_bounds")
        for start,data in self.blocks.items():
            if start<=p and p+n<=start+len(data):return data[p-start:p-start+n]
        raise InstrumentError("snapshot_missing_block")
    def add(self,p,data):
        if p in self.blocks and self.blocks[p]!=data:
            raise InstrumentError("snapshot_conflicting_block")
        self.blocks[p]=data

def commands():
    def bp(off,cmd):
        return 'bp Creatures+0x%x "%s"'%(off,cmd.replace('"','\\"'))
    def pr(name,fmt,args):
        return '.printf "NL_EVT '+name+' '+fmt+'\\n", '+', '.join(args)
    end='.echo NL_END; gc'
    def dump(p,n):
        return 'r @$t15='+p+'; .printf "NL_BUF %08x %u\\n", @$t15, 0n'+str(n)+'; db @$t15 L0n'+str(n)
    def lob(k):return '(@$t0+0x%x)'%(8+200*k)
    def header(k):return dump(lob(k),200)
    def cells(k,n):
        return header(k)+'; '+dump('poi('+lob(k)+'+0x9c)',16*n)
    def sense():
        return header(5)+'; '+dump('poi('+lob(5)+'+0x9c)',512)
    def chemistry():
        return dump('(@$t1+0x2c18)',8)+'; '+dump('poi(@$t1+0x2c1c)',120)+'; '+dump(lob(6)+'+0xc3',4)+'; '+dump(lob(8)+'+0xc3',1)
    def concept_and_contacts():
        concept=cells(0,112)+'; '+cells(8,640)
        # Read active Concept dendrites only; 1..3 expected from dad1.
        cloop=('r @$t5=poi('+lob(8)+'+0x9c); '
          +'.for (r @$t6=0; @$t6<0n640; r @$t6=@$t6+1) { r @$t7=@$t5+@$t6*0x10; '
          +'.if (by(@$t7+2)>0) { .if (by(@$t7+0xc)==1) { '+dump('poi(@$t7+4)',12)
          +' } .elsif (by(@$t7+0xc)==2) { '+dump('poi(@$t7+4)',24)
          +' } .elsif (by(@$t7+0xc)==3) { '+dump('poi(@$t7+4)',36)
          +' } .else { .echo NL_LAYOUT_BAD; qd } } }')
        dloop=(cells(6,16)+'; r @$t5=poi('+lob(6)+'+0x9c); '
          +'.for (r @$t6=0; @$t6<0n16; r @$t6=@$t6+1) { r @$t7=@$t5+@$t6*0x10; '
          +'.if (by(@$t7+0xc)==0x80) { .if (by(@$t7+0xd)==0x80) { '
          +dump('poi(@$t7+4)',1536)+'; '+dump('poi(@$t7+8)',1536)
          +' } .else { .echo NL_LAYOUT_BAD; qd } } .else { .echo NL_LAYOUT_BAD; qd } }')
        return concept+'; '+cloop+'; '+dloop
    def wrap(condition,body):
        return '.if ('+condition+') { '+body+' } .else { gc }'
    def evt(name,fmt,args,body=""):
        return pr(name,fmt,args)+('; '+body if body else '')+'; '+end
    regular="@$t3==1"
    active="@$t4>0"
    decision="@$t0+0x4b8"
    items=[
      bp(0x7583,"r @$t0=@ecx; r @$t1=@esi; r @$t2=poi(@esi+0x2c20); r @$t3=1; "+evt("RB","%08x %08x %u",["@esi","@ecx","@$t2"],sense()+"; "+chemistry())),
      bp(0x3e00,wrap(regular,wrap("@ecx=="+decision,wrap(active,evt("D0","%u",["@$t2"],sense()+"; "+concept_and_contacts()))))),
      bp(0x48a0,wrap(regular,wrap("@ebx=="+decision,wrap(active,evt("PREW","%u",["@$t2"],cells(6,16)))))),
      bp(0x4911,wrap(regular,wrap("@ebx=="+decision,evt("WTA","%u",["@$t2"],cells(6,16))))),
      bp(0x3caa,wrap(regular,wrap("@esi==@$t0",wrap("@edi==8",wrap(active,evt("C8","%u",["@$t2"],concept_and_contacts())))))),
      bp(0x759a,wrap(regular,wrap("@esi==@$t1","r @$t3=0; .if (@$t4>0) { r @$t4=@$t4-1 }; "+evt("RP","%u",["@$t2"],chemistry())))),
      bp(0x5daf,"r @$t3=0; "+evt("ALT","%08x %u",["@ecx","poi(@esp)"])),
      bp(0x16b39,evt("TRIG","%08x %u %u %u",["@ecx","poi(@esp)","poi(@esp+4)","poi(@esp+8)"])),
      bp(0x156df,".if (@eax==0n30200) { "+pr("DETACH","%u",["@eax"])+"; .echo NL_END; qd } .else { .if (@eax>=0n30000) { .if (@eax<=0n30111) { .if (@eax<0n30100) { r @$t4=4 } .else { r @$t4=1 }; "+evt("MARK","%u %08x",["@eax","poi(@ebx+0xa4)"],sense())+" } .else { gc } } .else { gc } }")
    ]
    require(all(len(x)<4096 for x in items),"debugger_command_length")
    return "\n".join([".echo NL_OBSERVER_READY","r @$t0=0","r @$t1=0","r @$t2=0","r @$t3=0","r @$t4=0",*items,"g"])+"\n"

EVENT=re.compile(r"^\s*NL_EVT (RB|D0|PREW|WTA|C8|RP|ALT|TRIG|MARK|DETACH) ([0-9a-fA-F ]+)\s*$")
BUF=re.compile(r"^\s*NL_BUF ([0-9a-fA-F]{8}) (\d+)\s*$")
DB=re.compile(r"^\s*([0-9a-fA-F]{8})\s+((?:[0-9a-fA-F]{2}(?:[ -]|$)){1,16})")

class BatchParser:
    def __init__(self,reader,on_event):
        self.reader=reader;self.on_event=on_event;self.event=None;self.buf=None;self.data=bytearray()
    def finish_buf(self):
        if self.buf:
            require(len(self.data)==self.buf[1],"snapshot_incomplete")
            self.reader.add(self.buf[0],bytes(self.data))
            self.buf=None;self.data=bytearray()
    def line(self,line):
        m=EVENT.fullmatch(line.strip())
        if m:
            require(self.event is None,"snapshot_event_overlap")
            self.reader.reset();self.event=(m.group(1),m.group(2).split());return
        if self.event is None:return
        m=BUF.fullmatch(line.strip())
        if m:
            self.finish_buf();self.buf=(int(m.group(1),16),int(m.group(2)));return
        if line.strip()=="NL_END":
            self.finish_buf();k,args=self.event;self.event=None;self.on_event(k,args);return
        if self.buf:
            m=DB.match(line)
            if m:
                p=int(m.group(1),16);data=bytes.fromhex(m.group(2).replace("-"," "))
                require(p==self.buf[0]+len(self.data) and len(self.data)+len(data)<=self.buf[1],"snapshot_address_or_length")
                self.data.extend(data)

class Observer:
    def __init__(self,pid,root,game,deadline):
        self.reader=SnapshotReader();self.cv=threading.Condition()
        self.deadline=deadline;self.frames=[];self.markers={};self.triggers=[];self.alt=[];self.cur=None
        self.norn=None;self.brain=None;self.last_tick=None;self.mark=None;self.remaining=0;self.error=None;self.detached=False
        self.ready=False;self.order_errors=0;self.cdb_return=None;self.event_counts=Counter()
        self.raw_lines=0;self.raw_bytes=0;self.diagnostics=set()
        cdb=Path(os.environ.get("ProgramFiles(x86)","C:/Program Files (x86)"))/"Windows Kits"/"10"/"Debuggers"/"x86"/"cdb.exe"
        require(cdb.is_file(),"debugger_absent")
        cmd=root/"h08c-batch.txt";cmd.write_text(commands(),encoding="ascii")
        self.log=root/"h08c-batch.log"
        self.out=self.log.open("wb")
        self.p=subprocess.Popen([str(cdb),"-G","-pd","-p",str(pid),"-cf",str(cmd)],cwd=game,stdin=subprocess.DEVNULL,stdout=self.out,stderr=subprocess.STDOUT)
        self.worker=threading.Thread(target=self.run,daemon=True);self.worker.start()
    def wait(self,pred,timeout):
        end=min(self.deadline,time.monotonic()+timeout)
        with self.cv:
            while not pred():
                if self.error:raise InstrumentError(self.error)
                if self.p.poll() is not None:raise InstrumentError("debugger_early_exit")
                rem=end-time.monotonic()
                if rem<=0:raise InstrumentError("observer_wait_timeout")
                self.cv.wait(min(rem,0.2))
    def handle(self,k,args):
        r=self.reader
        if k=="RB":
            n,b,t=int(args[0],16),int(args[1],16),int(args[2])
            require(r.ptr(n+0x2c18)==b,"brain_identity")
            if self.norn is None:self.norn,self.brain=n,b
            require((n,b)==(self.norn,self.brain),"subject_changed")
            require(self.cur is None and (self.last_tick is None or t>self.last_tick),"regular_order")
            self.last_tick=t
            f={"ordinal":len(self.frames)+1,"tick":t,"marker":self.mark if self.remaining else None,
               "sensor_rb":r.sense(b),"chem_pre":r.chem(n,b),"events":["RB"],"complete":False}
            self.cur=f;return
        if k=="ALT":
            if self.norn is not None and int(args[0],16)==self.brain:
                self.alt.append({"tick":int(args[1]),"after_ordinal":len(self.frames)})
                if self.cur is not None:raise InstrumentError("alternate_inside_regular")
            return
        if k=="TRIG":
            b=int(args[0],16);vals=list(map(int,args[1:]))
            if self.brain is not None and b==self.brain:
                self.triggers.append({"ordinal":len(self.frames),"tick":self.last_tick,"arguments":vals})
            return
        if k=="MARK":
            m,n=int(args[0]),int(args[1],16)
            require(self.norn is not None and n==self.norn and self.cur is None,"marker_identity_or_phase")
            require(m not in self.markers and self.remaining==0,"marker_duplicate_or_overlap")
            require(30000<=m<=30011 or 30100<=m<=30111,"marker_range")
            self.mark=m;self.remaining=4 if m<30100 else 1
            self.markers[m]={"ordinal":len(self.frames),"tick":self.last_tick,"sensor":r.sense(self.brain),"trigger_count":len(self.triggers)}
            return
        if k=="DETACH":
            self.detached=True;return
        f=self.cur;require(f is not None and f["tick"]==int(args[0]),"phase_identity")
        f["events"].append(k)
        if k=="D0":
            pc,out,active,per=r.concept(self.brain)
            f["concept_pre"]=active;f["perception"]=per;f["sensor_d0"]=r.sense(self.brain)
            f["decision_contacts_pre"]=r.decision_contacts(self.brain,pc,out)
        elif k=="PREW":
            _,cells,h=r.cells(self.brain,6)
            f["pre_wta"]=[x[2] for x in cells];f["excluded"]=[x[14] for x in cells]
            f["wta_active"]=uint(h,0xb0);f["wta_flag"]=bool(h[0x22]&1)
        elif k=="WTA":
            _,cells,h=r.cells(self.brain,6);out=[x[2] for x in cells]
            require(h[0x22]&1 and sum(v>0 for v in out)<=1,"wta_layout_or_multiple")
            f["decision"]=out;f["winner"]=winner(out)
            if f["marker"] is not None:
                require("pre_wta" in f and f["wta_flag"],"missing_wta_pre")
                f["wta_match"]=wta_expected(f["pre_wta"],f["excluded"],f["wta_active"],f["wta_flag"])==out
                require(f["wta_match"],"wta_prediction_mismatch")
        elif k=="C8":
            pc,out,active,_=r.concept(self.brain);f["concept_post"]=active
            f["decision_contacts_post"]=r.decision_contacts(self.brain,pc,out,previous=f["decision_contacts_pre"])
        elif k=="RP":
            f["chem_post"]=r.chem(self.norn,self.brain)
            expected=["RB","D0","PREW","WTA","C8","RP"] if f["marker"] is not None else ["RB","WTA","RP"]
            require(f["events"]==expected,"phase_order")
            f["complete"]=True;self.frames.append(f);self.cur=None
            if self.remaining:self.remaining-=1
            if not self.remaining:self.mark=None
    def process(self,k,args):
        with self.cv:
            self.event_counts[k]+=1
            self.handle(k,args);self.cv.notify_all()
    def run(self):
        parser=BatchParser(self.reader,self.process)
        try:
            with self.log.open("rb") as f:
                pending=b""
                while True:
                    block=f.read(65536)
                    if not block:
                        if self.p.poll() is not None:break
                        if time.monotonic()>self.deadline:raise InstrumentError("observer_deadline")
                        time.sleep(.02);continue
                    self.raw_bytes+=len(block)
                    require(self.raw_bytes<=64*1024*1024,"raw_capture_limit")
                    pending+=block
                    lines=pending.split(b"\n");pending=lines.pop()
                    for raw in lines:
                        self.raw_lines+=1;line=raw.decode("ascii","replace").rstrip("\r")
                        if line.strip()=="NL_OBSERVER_READY":
                            with self.cv:self.ready=True;self.cv.notify_all()
                        for code,pat in [("syntax","Syntax error|Extra character|Illegal"),("breakpoint","Unable to insert breakpoint|Unable to resolve|Couldn't resolve"),("access","Memory access error|Unable to read"),("operand","Operand error"),("layout",r"^\s*NL_LAYOUT_BAD\s*$")]:
                            if re.search(pat,line,re.I):self.diagnostics.add(code)
                        if self.diagnostics:raise InstrumentError("debugger_"+sorted(self.diagnostics)[0])
                        parser.line(line)
                if pending.strip():parser.line(pending.decode("ascii","replace"))
                require(parser.event is None,"snapshot_truncated_at_exit")
        except Exception as e:
            with self.cv:
                self.error=str(e) if isinstance(e,InstrumentError) else type(e).__name__
                self.cv.notify_all()
        finally:
            with self.cv:self.cdb_return=self.p.poll();self.cv.notify_all()
    def stop(self):
        if self.p.poll() is None:
            try:self.p.wait(timeout=8)
            except subprocess.TimeoutExpired:
                self.p.terminate();self.p.wait(timeout=8)
        self.worker.join(timeout=3);self.out.close();self.reader.close()
    def marker_frames(self,m):
        return [x for x in self.frames if x["marker"]==m]

def evaluate(trials,frames,alt):
    valid=[t for t in trials if t.get("valid")]
    inputs={k:[t for t in valid if t["arm"]==k] for k in ("A","B","S")}
    correct={k:sum(t.get("input_correct",False) for t in inputs[k]) for k in ("A","B")}
    false_sham=sum(t.get("input_correct",False) for t in inputs["S"])
    protos={}
    for k in ("A","B"):
        protos[k]=set().union(*(t["features_set"] for t in inputs[k][:2]))
    hold={k:[classify(t["features_set"],protos) for t in inputs[k][2:]] for k in ("A","B")}
    sham_classes=[classify(t["features_set"],protos) for t in inputs["S"]]
    basal=Counter(t["baseline_winner"] for t in valid if t["baseline_winner"] is not None)
    actions=sorted(basal,key=lambda x:(-basal[x],x))[:2]
    free=Counter(t["first_winner"] for t in valid if t["arm"]!="S" and t["first_winner"] is not None)
    opp={}
    for k in ("A","B"):
        for a in actions:
            for typ in (0,1):
                opp[f"{k}:{a}:{typ}"]=sum(t["opportunities"].get(f"{a}:{typ}",0) for t in inputs[k])
    wash=longest_wash(frames)
    checks={"identities_transport":len(trials)==12 and all(t.get("transport_valid") for t in trials),
            "input":correct["A"]>=3 and correct["B"]>=3 and false_sham<=1,
            "readout":len(valid)>=10 and all(len(inputs[k])==4 for k in ("A","B")),
            "signature":hold["A"]==["A","A"] and hold["B"]==["B","B"] and len(sham_classes)==4 and all(x is None for x in sham_classes),
            "free_actions":len(actions)==2 and all(free[a]>=2 for a in actions),
            "opportunities":len(opp)==8 and all(n>0 for n in opp.values()),
            "active_wash":wash>=8}
    return {"gate_checks":checks,"all_checks":all(checks.values()),"valid_trials":len(valid),"input_correct":correct,
            "sham_false_positive":false_sham,"heldout_classification":hold,"sham_classification":sham_classes,
            "actions":actions,"baseline_winners":dict(basal),"free_winners":dict(free),"opportunities":opp,
            "longest_wash":wash,"regular_frames":len(frames),"alternate_events":len(alt)}

def record_trial(i,arm,obs,before,delivery,identity,meta):
    baseline=obs.marker_frames(30100+i);pulse=obs.marker_frames(30000+i)
    bmark=obs.markers.get(30100+i);pmark=obs.markers.get(30000+i)
    transport=bool(before and delivery.get("ok") and identity and bmark and pmark)
    if transport:
        trig=obs.triggers[bmark["trigger_count"]:pmark["trigger_count"]]
        expected=[] if arm=="S" else [[5,8 if arm=="A" else 9,32]]
        transport=[x["arguments"] for x in trig]==expected
        if expected:
            k=0 if arm=="A" else 1
            transport=transport and trig[0]["ordinal"]==pmark["ordinal"] and pmark["sensor"][k]==[32,32]
        if i:
            prev=obs.markers.get(30000+i-1)
            transport=transport and bool(prev and 128<=pmark["ordinal"]-prev["ordinal"]<=512)
    valid=transport and len(baseline)==1 and len(pulse)==4 and all(f.get("complete") and f.get("wta_match") for f in baseline+pulse)
    t={"index":i,"arm":arm,"transport_valid":bool(transport),"valid":bool(valid),"metadata":meta,
       "baseline_ordinal":bmark["ordinal"] if bmark else None,"pulse_ordinal":pmark["ordinal"] if pmark else None,
       "marker_sensor":pmark["sensor"] if pmark else None,"delivery_ok":bool(delivery.get("ok"))}
    if valid:
        b=baseline[0];base_sig=sigset(b)
        features=set().union(*(sigset(f) for f in pulse))-base_sig
        rises=[any(max(f["sensor_rb"][k])>max(b["sensor_rb"][k]) for f in pulse) for k in (0,1)]
        t["input_correct"]=any(rises) if arm=="S" else rises[0 if arm=="A" else 1] and not rises[1 if arm=="A" else 0]
        t["baseline_winner"]=b["winner"];t["first_winner"]=next((f["winner"] for f in pulse if f["winner"] is not None),None)
        t["features_set"]=features;t["features"]=[[cell,list(src)] for cell,src in sorted(features)]
        opp=Counter(f"{x[0]}:{x[1]}" for f in pulse for x in f["decision_contacts_pre"] if x[4]>0 and x[7]>0)
        t["opportunities"]=dict(opp);t["sensor_rises"]=rises
        t["active_concept_counts"]=[len(f["concept_pre"]) for f in pulse]
    return t

def write_result(data):
    p=Path(os.environ["NL_RESULT_FILE"])
    p.write_text(json.dumps(data,sort_keys=True,ensure_ascii=True,indent=2)+"\n",encoding="utf-8")

def observe(game,pid,root):
    global RESULT
    import h08b_mounted_launch as launch
    base=launch.base;obs=None;trials=[];error=None
    def q(cmd,expected=None,kind="number"):
        t0=time.perf_counter_ns();r=launch.query_macro(cmd,expected,kind)
        return {**r,"elapsed_us":(time.perf_counter_ns()-t0)//1000}
    def norn(cmd,expected=None,kind="number"):return q("enum 4 1 0,"+cmd+",next",expected,kind)
    def identity():return q("dde: putv totl 4 1 0",1)["ok"] and norn("dde: getb monk",IDENT,"moniker")["ok"]
    try:
        require(q("dde: putv totl 4 1 0",0)["ok"],"world_not_empty")
        dest=game/"Genetics"/"NL01.gen";require(not dest.exists(),"moniker_collision")
        shutil.copyfile(game/"Genetics"/"dad1.gen",dest);require(base.digest(dest)==base.GEN,"genome_mismatch")
        birth=q("new: crea tokn nl01 1,mvto 2408 870,dde: putv totl 4 1 0",1)
        require(birth["ok"],"birth_transport")
        RESULT["subject_created"]=True;write_result(RESULT)
        start=time.monotonic()
        while time.monotonic()-start<85:
            time.sleep(min(5,max(0,85-(time.monotonic()-start))))
            require(q("dde: putv 123",123)["ok"],"initialization_dde")
        require(identity(),"initial_identity")
        deadline=time.monotonic()+650
        obs=Observer(pid,root,game,deadline)
        obs.wait(lambda: len(obs.frames)>=8,30)
        require(identity(),"post_attach_identity")
        for i,arm in enumerate(ORDER):
            if i:
                prev=obs.markers[30000+i-1]["ordinal"]
                obs.wait(lambda:len(obs.frames)>=prev+128,240)
                require(len(obs.frames)-prev<=510,"wash_interval_exceeded")
            require(identity(),"baseline_identity")
            meta={k:norn("dde: putv "+k) for k in ("aslp","ins#","cage","dead","drv!")}
            require(all(x.get("ok") for x in meta.values()),"context_observation")
            b=norn("dde: putv "+str(30100+i),30100+i)
            require(b["ok"],"baseline_marker_transport")
            obs.wait(lambda:len(obs.marker_frames(30100+i))==1,30)
            require(identity(),"pre_pulse_identity")
            cmd=("trig 5 "+str(8 if arm=="A" else 9)+" 32," if arm!="S" else "")+"dde: putv "+str(30000+i)
            delivery=norn(cmd,30000+i)
            require(delivery["ok"],"pulse_marker_transport")
            obs.wait(lambda:len(obs.marker_frames(30000+i))==4,30)
            t=record_trial(i,arm,obs,b["ok"],delivery,identity(),meta)
            trials.append(t)
            base.emit(gate="h08c1_trial",trial=i,arm=arm,transport=t["transport_valid"],valid=t["valid"],first_winner=t.get("first_winner"))
            if not t["transport_valid"]:raise InstrumentError("native_pulse_or_identity_not_verified")
            if obs.error:raise InstrumentError(obs.error)
    except Exception as e:
        error=str(e) if isinstance(e,InstrumentError) else type(e).__name__
    finally:
        if obs is not None:
            # Native constant query causes CDB qd, never changes a neural state.
            if obs.p.poll() is None:
                try:norn("dde: putv 30200",30200)
                except Exception:pass
            try:obs.stop()
            except Exception as e:
                error=error or type(e).__name__
            frames=obs.frames;alt=obs.alt
            RESULT.update({"frames":frames,"alternate":alt,"triggers":obs.triggers,"markers":obs.markers,
                "debugger_detached":obs.detached,"event_counts":dict(obs.event_counts),"instrument_error":error or obs.error,"observer_diagnostics":{"ready":obs.ready,"raw_lines":obs.raw_lines,"raw_bytes":obs.raw_bytes,"categories":sorted(obs.diagnostics),"cdb_return":obs.cdb_return}})
            RESULT["summary"]=evaluate(trials,frames,alt)
        else:
            RESULT["instrument_error"]=error
        for t in trials:t.pop("features_set",None)
        RESULT["trials"]=trials
        RESULT["classification"]="feasibility_session_complete" if len(trials)==12 and not RESULT.get("instrument_error") else "instrumental_incomplete"
        write_result(RESULT)
        base.emit(gate="h08c1_session_summary",classification=RESULT["classification"],instrument_error=RESULT.get("instrument_error"),
                  trials=len(trials),summary=RESULT.get("summary"),debugger_detached=RESULT.get("debugger_detached",False))
def main():
    global RESULT
    self_test()
    if "--self-test" in sys.argv:return
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"inherited"/"experiments"/"neurolab"))
    import h08b_mounted_launch as launch
    RESULT={"session":SESSION,"purpose":"instrumental feasibility replication with batch correction","seed":SEED,"order":ORDER,"subject_created":False,
        "classification":"launcher_not_reached","trials":[],"instrument_error":None}
    write_result(RESULT)
    launch.observe_one_norn=observe
    launch.main()
if __name__=="__main__":main()
