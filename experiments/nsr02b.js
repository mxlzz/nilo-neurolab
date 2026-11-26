"use strict";
// NSR02b: PCG32 XSH-RR reimplementation of published algorithm (O’Neill). Source: https://www.pcg-random.org/download.html
function pcg(initstate,initseq){
let state=0n,inc=2n*BigInt(initseq)+1n,mask=(1n<<64n)-1n;
function next(){let old=state;state=(old*6364136223846793005n+inc)&mask;let x=Number(((old^(old>>18n))>>27n)&0xffffffffn),rot=Number(old>>59n);return ((x>>>rot)|(x<<((-rot)&31)))>>>0}
next();state=(state+BigInt(initstate))&mask;next();return next;
}
function rng(seed,domain){const next=pcg(0x853c49e6748fea9bn+BigInt(seed),3n*BigInt(seed)+BigInt(domain));return()=>next()/4294967296}
function preflight(){
const start=Date.now(),expected=["a15c02b7","7b47f409","ba1d3330","83d2f293","bfa4784b","cbed606e"],next=pcg(42n,54n),actual=expected.map(()=>next().toString(16).padStart(8,"0")),N=2048,T=64,p=[.5,.1,.1,.1,.5,.1,.1,.1],counts=Array(8).fill(0),pairs=Array.from({length:8},()=>Array(8).fill(0)),rates=Array(6).fill(0),halfPairs=Array.from({length:5},()=>Array(5).fill(0)),lag=Array(5).fill(0),half=Array(5).fill(0);
for(let seed=43000;seed<45048;seed++){let ri=rng(seed,0),rt=rng(seed,1),rn=rng(seed,2),b=p.map(v=>+(ri()<v));for(let i=0;i<8;i++){counts[i]+=b[i];for(let j=i+1;j<8;j++)pairs[i][j]+=b[i]*b[j]}let prev=null;for(let t=0;t<T;t++){let u=[rt(),rt(),rt(),rt(),rn()];let a=[+(u[0]<.03),+(u[1]<.01),+(u[2]<.01),+(u[3]<.01),+(u[4]<.1),+(u[4]<.25)];a.forEach((v,i)=>rates[i]+=v);let h=u.map(v=>+(v<.5));for(let i=0;i<5;i++){half[i]+=h[i];for(let j=i+1;j<5;j++)halfPairs[i][j]+=h[i]*h[j];if(prev)lag[i]+=prev[i]*h[i]}prev=h}}
let checks=[];function test(name,n,k,p){let z=(k-n*p)/Math.sqrt(n*p*(1-p));checks.push({name,n,k,p,z,pass:Math.abs(z)<=5})}
for(let i=0;i<8;i++){test("init"+i,N,counts[i],p[i]);for(let j=i+1;j<8;j++)test("initpair"+i+"_"+j,N,pairs[i][j],p[i]*p[j])}
rates.forEach((k,i)=>test("rate"+i,N*T,k,[.03,.01,.01,.01,.1,.25][i]));
for(let i=0;i<5;i++){test("half"+i,N*T,half[i],.5);for(let j=i+1;j<5;j++)test("halfPair"+i+"_"+j,N*T,halfPairs[i][j],.25);test("lag"+i,N*(T-1),lag[i],.25)}
return {version:1,seed_range:[43000,45047],expected,actual,checks,pass:expected.every((s,i)=>s===actual[i])&&checks.every(c=>c.pass),max_abs_z:Math.max(...checks.map(c=>Math.abs(c.z))),elapsed_ms:Date.now()-start}
}
function run(){
const t0=Date.now(),masks=[1,2,4],arms=["LOCAL64","LOCAL8","MF8","JOINT64","JOINT8"],keys=["all","return","valid","transfer","exception","local"],states=[0,1,2,3,4,5,6,7],bit=(s,x)=>(s>>x)&1,pc=s=>bit(s,0)+bit(s,1)+bit(s,2),q8=p=>Math.round(p*254)/254,trans=(p,h)=>h+(1-2*h)*p;
function assert(b,m){if(!b)throw Error(m)}
function norm(a){let s=a.reduce((x,y)=>x+y,0);assert(s>0,"zero mass");return a.map(x=>x/s)}
function quant(a){let z=norm(a).map(x=>255*x),b=z.map(Math.floor),n=255-b.reduce((x,y)=>x+y,0),order=states.slice().sort((i,j)=>(z[j]-b[j])-(z[i]-b[i])||i-j);for(let i=0;i<n;i++)b[order[i]]++;assert(b.reduce((x,y)=>x+y,0)===255,"mass");return b.map(x=>x/255)}
function prior(){return states.map(s=>.5*(.1**pc(s)*.9**(3-pc(s))+.1**(3-pc(s))*.9**pc(s)))}
function kernel(hg,he){let k=states.map(s=>(1-hg)*he**pc(s)*(1-he)**(3-pc(s))+hg*he**(3-pc(s))*(1-he)**pc(s));let other=Array(8).fill(0);for(let g=0;g<2;g++)for(let e=0;e<8;e++)other[e^(g?7:0)]+=(g?hg:1-hg)*he**pc(e)*(1-he)**(3-pc(e));assert(k.every((p,i)=>Math.abs(p-other[i])<1e-13)&&Math.abs(k.reduce((a,b)=>a+b,0)-1)<1e-13,"kernel");return k}
function jstep(p,k){return states.map(s=>states.reduce((acc,u)=>acc+p[u]*k[s^u],0))}
function pred(p,x){return p.reduce((a,b,s)=>a+b*bit(s,x),0)}
function obs(p,x,z,q){return norm(p.map((v,s)=>v*(bit(s,x)===z?1-q:q)))}
function update(p,z,q){let a=p*(z?1-q:q),b=(1-p)*(z?q:1-q);return a/(a+b)}
function check(hg,he,q,k){let p=prior(),l=Array.from({length:16},(_,s)=>.5*.1**pc(s>>1)*.9**(3-pc(s>>1))),err=0,n=0;
for(let t=0;t<12;t++){let x=t%3,z=t%4===0?null:((t*7+1)>>1)&1;p=jstep(p,k);let next=Array(16).fill(0);for(let s=0;s<16;s++)for(let u=0;u<16;u++){let d=s^u;next[u]+=l[s]*(d&1?hg:1-hg)*he**pc(d>>1)*(1-he)**(3-pc(d>>1))}l=next;
let lp=l.reduce((a,b,s)=>a+b*((s&1)^bit(s>>1,x)),0);err=Math.max(err,Math.abs(lp-pred(p,x)));n++;if(z!==null){p=obs(p,x,z,q);l=norm(l.map((v,s)=>v*(((s&1)^bit(s>>1,x))===z?1-q:q)))}
let marginal=Array(8).fill(0);for(let s=0;s<16;s++)marginal[(s>>1)^((s&1)?7:0)]+=l[s];for(let s=0;s<8;s++){err=Math.max(err,Math.abs(marginal[s]-p[s]));n++}}
assert(err<1e-12,"latent fixture");return {err,n}}
function initial(arm){if(arm.startsWith("JOINT"))return arm==="JOINT8"?quant(prior()):prior();if(arm==="MF8")return [.5,.1,.1,.1].map(q8);return [.5,.5,.5]}
function pre(arm,p,k,hg,he){if(arm.startsWith("JOINT"))return jstep(p,k);if(arm==="MF8")return p.map((v,i)=>trans(v,i===0?hg:he));return p.map(v=>trans(v,hg+he-2*hg*he))}
function probability(arm,p,x){if(arm.startsWith("JOINT"))return pred(p,x);if(arm==="MF8")return p[0]+p[x+1]-2*p[0]*p[x+1];return p[x]}
function post(arm,p,x,z,q){if(arm.startsWith("JOINT")){if(z!==null)p=obs(p,x,z,q);return arm==="JOINT8"?quant(p):p}if(arm==="MF8"){if(z!==null){let g=p[0],e=p[x+1],G=0,E=0,Z=0;for(let i=0;i<2;i++)for(let j=0;j<2;j++){let w=(i?g:1-g)*(j?e:1-e)*((i^j)===z?1-q:q);Z+=w;G+=i*w;E+=j*w}p[0]=G/Z;p[x+1]=E/Z}return p.map(q8)}if(z!==null)p[x]=update(p[x],z,q);return arm==="LOCAL8"?p.map(q8):p}
const result={version:2,arms,keys,metric_fields:["n","correct","regret_sum"],logical_bytes:[48,6,8,128,16],conditions:[]};
for(let q of [.1,.25])for(let hg of [0,.03]){let he=.01,k=kernel(hg,he),fixture=check(hg,he,q,k),worlds=[];
for(let seed=33000;seed<33064;seed++){let ri=rng(seed,0),rt=rng(seed,1),rn=rng(seed,2),g=[],e=[],gf=[-1,-1],lf=[[-1,-1,-1],[-1,-1,-1]],last=Array.from({length:2},()=>Array.from({length:3},()=>({t:-1,g:0,y:0}))),lastAny=[-1,-1],models=arms.map(a=>[initial(a),initial(a)]),metrics=arms.map(()=>keys.map(()=>[0,0,0])),checksum=2166136261;
for(let c=0;c<2;c++){g[c]=+(ri()<.5);e[c]=masks.map(()=>+(ri()<.1))}
for(let t=0;t<384;t++){let block=Math.floor(t/48),c=block%2,x=t%3,probe=block>=2&&t%48<3;if(rt()<hg){g[c]^=1;gf[c]=t}for(let i=0;i<3;i++)if(rt()<he){e[c][i]^=1;lf[c][i]=t}
let y=g[c]^e[c][x],z=y^+(rn()<q),L=last[c][x],has=L.t>=0,transfer=has&&g[c]!==L.g&&lf[c][x]<=L.t&&gf[c]<t&&lastAny[c]>gf[c]&&lastAny[c]>L.t,local=has&&gf[c]<=L.t&&lf[c][x]>L.t&&y!==L.y;
let flags=[true,probe,probe&&has&&y===L.y,transfer,transfer&&e[c][x]===1,local];checksum=Math.imul(checksum^((g[c]<<7)|(e[c][0]<<6)|(e[c][1]<<5)|(e[c][2]<<4)|(x<<2)|(y<<1)|z),16777619)>>>0;
let pp=models.map((m,i)=>pre(arms[i],m[c],k,hg,he)),p=probability("JOINT64",pp[3],x);assert(p>=-1e-12&&p<=1+1e-12,"prediction");for(let i=0;i<arms.length;i++){let a=+(probability(arms[i],pp[i],x)>.5),r=probe?null:(a===z?1:-1),seen=r===null?null:r===1?a:1-a;assert(seen===null||seen===z,"feedback");let regret=Math.max(p,1-p)-(a?p:1-p);for(let j=0;j<keys.length;j++)if(flags[j]){metrics[i][j][0]++;metrics[i][j][1]+=+(a===y);metrics[i][j][2]+=regret}models[i][c]=post(arms[i],pp[i],x,seen,q)}
if(!probe){last[c][x]={t,g:g[c],y};lastAny[c]=t}}
assert(metrics.every(m=>m[0][0]===384&&m[1][0]===18),"counts");assert(metrics[3].every(m=>Math.abs(m[2])<1e-12),"ref regret");worlds.push({seed,checksum:checksum.toString(16).padStart(8,"0"),metrics})}
let summary=arms.map((a,i)=>keys.map((key,j)=>{let rows=worlds.map(w=>w.metrics[i][j]).filter(m=>m[0]>0),n=rows.reduce((v,m)=>v+m[0],0),correct=rows.reduce((v,m)=>v+m[1],0),reg=rows.reduce((v,m)=>v+m[2],0);return {n,worlds:rows.length,accuracy:n?correct/n:null,regret:n?reg/n:null,world_accuracy:n?rows.reduce((v,m)=>v+m[1]/m[0],0)/rows.length:null,world_regret:n?rows.reduce((v,m)=>v+m[2]/m[0],0)/rows.length:null}}));result.conditions.push({q,hg,he,fixture,summary,worlds})}
result.elapsed_ms=Date.now()-t0;assert(result.elapsed_ms<=60000,"budget");return result;
}
const p=preflight();
if(process.argv.includes('--preflight')) process.stdout.write(JSON.stringify(p)+'\n');
else {if(!p.pass)throw Error('preflight');const d=run();if(p.elapsed_ms+d.elapsed_ms>60000)throw Error('budget');process.stdout.write(JSON.stringify(d)+'\n');}
