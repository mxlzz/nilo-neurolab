"use strict";
// Documentary inspection of existing NSR01 random streams; no tape, agent, or reward experiment.
function rng(seed,salt){let x=(Math.imul(seed,0x9e3779b1)^salt)>>>0;if(!x)x=1;return ()=>{x^=x<<13;x^=x>>>17;x^=x<<5;return (x>>>0)/4294967296;};}
function audit(){
const salts=[0xb573a9bd,0x6e2bc799,0x52ce8a39,0x1a1ff349],counts=Array(64).fill(0),patterns=new Set(),events=Array.from({length:4},()=>[0,0,0,0]),diffs=Array(1024).fill(null);let zero=0,violations=0;
for(let seed=31000;seed<31064;seed++){for(const salt of salts)if(((Math.imul(seed,0x9e3779b1)^salt)>>>0)===0)zero++;
const p=rng(seed,salts[0]),f=rng(seed,salts[1]),n=rng(seed,salts[2]);let init=[];
for(let i=0;i<64;i++){let b=+(p()>=.5);counts[i]+=b;init.push(b)}patterns.add(init.join(""));
for(let t=0;t<1024;t++){const F=f(),N=n(),d=((F*4294967296)^(N*4294967296))>>>0;if(diffs[t]===null)diffs[t]=d;else if(diffs[t]!==d)violations++;let i=0;for(const h of [.01,.05])for(const q of [.1,.25])events[i++][2*+(F<h)+ +(N<q)]++}}
return {source_blob:"284f38a57686c170c54c0e6f219fccc8a336abd5",seed_range:[31000,31063],initial_ones:counts,initial_distinct_patterns:patterns.size,zero_guard_uses:zero,xor_identity_violations:violations,distinct_xor_differences:new Set(diffs).size,first_xor:diffs[0],draw_pairs:65536,condition_order:[[.01,.1],[.01,.25],[.05,.1],[.05,.25]],event_order:["neither","noise_only","flip_only","both"],events};
}
process.stdout.write(JSON.stringify(audit())+"\n");