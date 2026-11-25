"""H08c.1 input gate only. Reuse historic hash/archive validator; never start game."""
import os, pathlib, tempfile, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]/"inherited"/"experiments"/"neurolab"))
import h08b_original_launch as base

def main():
    with tempfile.TemporaryDirectory(prefix="neurolab-verify-data-") as d:
        game=base.prepare(pathlib.Path(d))
        base.emit(gate="data_fingerprints_verified", data_sha256=base.EXPECTED, exe_sha256=base.digest(game/"Creatures.exe"), gen_sha256=base.digest(game/"Genetics"/"dad1.gen"))
    cdb=pathlib.Path(os.environ.get("ProgramFiles(x86)","C:/Program Files (x86)"))/"Windows Kits"/"10"/"Debuggers"/"x86"/"cdb.exe"
    base.emit(gate="debugger_presence", present=cdb.is_file())
    if not cdb.is_file():
        raise SystemExit("Required debugger unavailable")
    base.emit(gate="medium_preflight_pass", game_launched=False, scientific_sessions_consumed=0)

if __name__=="__main__": main()
