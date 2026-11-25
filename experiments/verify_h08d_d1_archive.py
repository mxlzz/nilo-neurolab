"""Recompute D1 archive WTA prediction without importing acquisition analyzer."""
import hashlib,json,pathlib,zipfile
p=pathlib.Path(__file__).resolve().parents[1]/"evidence"/"H08d_D1_derived.zip"
assert hashlib.sha256(p.read_bytes()).hexdigest()=="f5517f7d1f97612741f7fef663e2effb067f95963ab80d7a53e27855b88064e8"
with zipfile.ZipFile(p) as z:
    assert z.testzip() is None and z.namelist()==["h08d-d1-result.json"]
    raw=z.read("h08d-d1-result.json")
assert hashlib.sha256(raw).hexdigest()=="beef42787dfd4cd80d858d86bad48c693445b1b9f28fb34aec61a7b1069bc420"
r=json.loads(raw);frames=r["trace"]["cycles"]
assert len(frames)==20 and [f["tick"] for f in frames]==list(range(478,498))
for f in frames:
    a,e=f["pre_outputs"],f["excluded"]
    assert len(a)==len(e)==len(f["post_outputs"])==16
    elig=[(v,-i) for i,v in enumerate(a) if not e[i] and v>0]
    pred=[0]*16
    if f["PRE_meta"][1]&1 and f["PRE_meta"][2]:
        if elig:
            v,ni=max(elig);pred[-ni]=v
    else:pred=a
    assert pred==f["post_outputs"]
assert r["identity_before"] and r["identity_after"] and r["trace"]["same_subject_brain"]
assert r["stimuli"]==r["reward_pulses"]==0
print("PASS: archive and JSON SHA256; 20/20 original WTA observations recomputed")
