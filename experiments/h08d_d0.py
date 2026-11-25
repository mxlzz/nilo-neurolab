"""D0: genuine CDB transport, using a project-owned synthetic x86 target only."""
import json, os, pathlib, re, subprocess, tempfile, sys
EXPECTED=[11,22,33]
def bp(name,cmd):
    return 'bu '+name+' "'+cmd.replace('"','\\"')+'"'
def pr(label,slashes):
    return '.printf "NL_D0_'+label+' %u'+('\\'*slashes)+'n", poi(@esp+4)'
def parse(raw):
    # Actual .echo lines only; no commands, addresses, or unbounded raw strings.
    hit=len(re.findall(r"(?m)^\s*NL_D0_HIT\s*$",raw))
    end=bool(re.search(r"(?m)^\s*NL_D0_END\s*$",raw))
    def anchored(label):
        return [int(x) for x in re.findall(r"(?m)^\s*NL_D0_"+label+r" (\d+)\s*$",raw)]
    def flexible(label):
        # A preceding command is not allowed: token must start a line or follow literal backslash-n.
        return [int(x) for x in re.findall(r"(?:^|\\n)NL_D0_"+label+r" (\d+)(?=\s|\\n|$)",raw,re.M)]
    forms=[]
    for line in raw.splitlines():
        s=line.strip()
        if not s.startswith("NL_D0_"):continue
        if len(forms)>=24:break
        if re.fullmatch(r"(?:NL_D0_(?:HIT|END|READY|LEGACY|SINGLE)(?: [0-9]{1,3})?(?:\\n|\s)*)+",s):
            forms.append(s)
        else:
            forms.append("recognized_prefix_unexpected_shape")
    cats=[k for k,p in (("syntax",r"Syntax error|Extra character|Illegal"),("symbol",r"Unable to resolve|Couldn't resolve|Unable to insert breakpoint"),("access",r"Memory access error|Unable to read"),("quote",r"unterminated|quote.*error")) if re.search(p,raw,re.I)]
    return dict(hit=hit,end=end,legacy_anchored=anchored("LEGACY"),single_anchored=anchored("SINGLE"),legacy_flexible=flexible("LEGACY"),single_flexible=flexible("SINGLE"),forms=forms,categories=cats,bytes=len(raw.encode("utf-8")),lines=len(raw.splitlines()))
def main():
    # Reject debugger command echo and incomplete numeric fields as events.
    assert parse('0:000> .printf "NL_D0_LEGACY 11"\nNL_D0_LEGACY\nNL_D0_HITx\n')["legacy_anchored"]==[]
    target=pathlib.Path(sys.argv[1]).resolve()
    cdb=pathlib.Path(os.environ["ProgramFiles(x86)"])/"Windows Kits"/"10"/"Debuggers"/"x86"/"cdb.exe"
    result={"stage":"D0","target":"project_fixture_x86","expected":EXPECTED,"originals_used":False}
    with tempfile.TemporaryDirectory(prefix="nl-d0-") as tmp:
        root=pathlib.Path(tmp);cmd=root/"commands.txt";log=root/"trace.log"
        body="; ".join([".echo NL_D0_HIT",pr("LEGACY",2),pr("SINGLE",1),"r @$t0=@$t0+1",".if (@$t0>=3) { .echo NL_D0_END; qd } .else { gc }"])
        cmd.write_text("\n".join([".echo NL_D0_READY","r @$t0=0",bp("fixture!nl_tick",body),"g"])+"\n",encoding="ascii")
        try:
            with log.open("wb") as out:
                p=subprocess.run([str(cdb),"-G","-pd","-cf",str(cmd),str(target)],cwd=target.parent,stdin=subprocess.DEVNULL,stdout=out,stderr=subprocess.STDOUT,timeout=40)
            result["returncode"]=p.returncode
        except subprocess.TimeoutExpired:
            result["returncode"]=None;result["timeout"]=True
        raw=log.read_bytes().decode("utf-8","replace") if log.exists() else ""
        result.update(parse(raw))
    result["pass"]=result["hit"]==3 and result["end"] and result["legacy_anchored"]==EXPECTED and result["returncode"]==0
    print("NL_D0_RESULT "+json.dumps(result,sort_keys=True),flush=True)
    pathlib.Path("h08d-d0-result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return 0 if result["pass"] else 1
if __name__=="__main__":raise SystemExit(main())
