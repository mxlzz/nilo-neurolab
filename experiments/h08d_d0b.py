"""D0b: isolate legacy escaping and marker boundaries on owned x86 fixture."""
import json, os, pathlib, subprocess, tempfile, sys
from h08d_d0 import EXPECTED, bp, pr, parse
EXPECTED_FORMS=["NL_D0_READY","NL_D0_HIT","NL_D0_LEGACY 11","NL_D0_HIT","NL_D0_LEGACY 22","NL_D0_HIT","NL_D0_LEGACY 33","NL_D0_END"]
def main():
    target=pathlib.Path(sys.argv[1]).resolve()
    cdb=pathlib.Path(os.environ["ProgramFiles(x86)"])/"Windows Kits"/"10"/"Debuggers"/"x86"/"cdb.exe"
    result={"stage":"D0b","expected":EXPECTED,"target":"project_fixture_x86","originals_used":False}
    with tempfile.TemporaryDirectory(prefix="nl-d0b-") as tmp:
        root=pathlib.Path(tmp);cmd=root/"commands.txt";log=root/"trace.log"
        body="; ".join([".echo NL_D0_HIT",pr("LEGACY",2),"r @$t0=@$t0+1",".if (@$t0>=3) { .echo NL_D0_END; qd } .else { gc }"])
        cmd.write_text("\n".join([".echo NL_D0_READY","r @$t0=0",bp("fixture!nl_tick",body),"g"])+"\n",encoding="ascii")
        try:
            with log.open("wb") as out:
                p=subprocess.run([str(cdb),"-G","-pd","-cf",str(cmd),str(target)],cwd=target.parent,stdin=subprocess.DEVNULL,stdout=out,stderr=subprocess.STDOUT,timeout=40)
            result["returncode"]=p.returncode
        except subprocess.TimeoutExpired:
            result["returncode"]=None;result["timeout"]=True
        raw=log.read_bytes().decode("utf-8","replace") if log.exists() else ""
        result.update(parse(raw))
    result["pass"]=result["hit"]==3 and result["end"] and result["legacy_anchored"]==EXPECTED and result["forms"]==EXPECTED_FORMS and result["returncode"]==0 and not result["categories"]
    print("NL_D0B_RESULT "+json.dumps(result,sort_keys=True),flush=True)
    pathlib.Path("h08d-d0b-result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return 0 if result["pass"] else 1
if __name__=="__main__":raise SystemExit(main())
