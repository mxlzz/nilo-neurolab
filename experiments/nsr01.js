/* NSR01; deterministic baseline-only diagnostic. Node.js, no dependencies. */
function sha256(bytes){
  const K=[0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2];
  const H=[0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19];
  const n=bytes.length,m=(n+9+63)&~63,b=new Uint8Array(m);b.set(bytes);b[n]=128;
  const v=new DataView(b.buffer);v.setUint32(m-8,Math.floor(n/0x20000000));v.setUint32(m-4,(n*8)>>>0);
  const w=new Uint32Array(64),r=(x,k)=>(x>>>k)|(x<<(32-k));
  for(let i=0;i<m;i+=64){for(let j=0;j<16;j++)w[j]=v.getUint32(i+4*j);for(let j=16;j<64;j++){const a=w[j-15],z=w[j-2];w[j]=(w[j-16]+(r(a,7)^r(a,18)^(a>>>3))+w[j-7]+(r(z,17)^r(z,19)^(z>>>10)))>>>0;}let [a,c,d,e,f,g,h,k]=H;
    for(let j=0;j<64;j++){const t1=(k+(r(f,6)^r(f,11)^r(f,25))+((f&g)^(~f&h))+K[j]+w[j])>>>0,t2=((r(a,2)^r(a,13)^r(a,22))+((a&c)^(a&d)^(c&d)))>>>0;k=h;h=g;g=f;f=(e+t1)>>>0;e=d;d=c;c=a;a=(t1+t2)>>>0;}
    [a,c,d,e,f,g,h,k].forEach((x,j)=>H[j]=(H[j]+x)>>>0);
  }return H.map(x=>x.toString(16).padStart(8,"0")).join("");
}

function rng(seed,salt){let x=(Math.imul(seed,0x9e3779b1)^salt)>>>0;if(!x)x=1;return ()=>{x^=x<<13;x^=x>>>17;x^=x<<5;return (x>>>0)/4294967296;};}

function tape(seed,h,q){
 const p=rng(seed,0xb573a9bd),f=rng(seed,0x6e2bc799),n=rng(seed,0x52ce8a39),u=rng(seed,0x1a1ff349);
 const y=Uint8Array.from({length:64},()=>p()<.5?0:1),age=new Uint16Array(64),rows=[];
 for(const [block,c] of [0,1,2,3,0,2,1,3].entries())for(let sweep=0;sweep<8;sweep++){
  const xs=Array.from({length:16},(_,i)=>i);for(let j=15;j>0;j--){const k=Math.floor(u()*(j+1));[xs[j],xs[k]]=[xs[k],xs[j]];}
  for(const x of xs){const k=16*c+x,flip=f()<h?1:0,noise=n()<q?1:0,probe=block>=4&&sweep===0?1:0;y[k]^=flip;age[k]=flip?0:age[k]+1;rows.push([k,y[k],flip,noise,probe,Math.min(255,age[k])]);}
 }return rows;
}

function update(p,z,q){if(z===null)return p;const l=z===1?1-q:q,m=1-l;return p*l/(p*l+(1-p)*m);}

function checkBayes(){
 let total=0,err=0;
 for(const h of [0,.01,.05])for(const q of [.10,.25])for(let id=0;id<81;id++){
  let a=id;const zs=Array.from({length:4},()=>{const z=a%3;a=Math.floor(a/3);return z===2?null:z;});
  let p=.5,paths=[[0,.5],[1,.5]];
  for(const z of zs){p=update(h+(1-2*h)*p,z,q);const next=[];for(const [y,w] of paths)for(const bit of [0,1]){let weight=w*(bit===y?1-h:h);if(z!==null)weight*=bit===z?1-q:q;next.push([bit,weight]);}paths=next;const exact=paths.filter(x=>x[0]===1).reduce((a,x)=>a+x[1],0)/paths.reduce((a,x)=>a+x[1],0);err=Math.max(err,Math.abs(p-exact));total++;}
 }if(err>1e-12)throw Error("posterior check");return {histories:486,posterior_checks:total,max_abs_error:err};
}

function runWorld(seed,h,q){
 const rows=tape(seed,h,q),names=["LAST","SAT3","WIN7","BAYES4","BAYES8","BAYES64"],metrics=["all","feedback","return","return_unchanged","flip","recent","stable","spurious_after_noise"];
 const data=names.map(()=>metrics.map(()=>[0,0,0]));const last=new Uint8Array(64),sat=new Int8Array(64),win=new Uint8Array(64),cnt=new Uint8Array(64),b4=new Uint8Array(64).fill(7),b8=new Uint8Array(64).fill(127),exact=new Float64Array(64).fill(.5);
 const prev=names.map(()=>new Int8Array(64).fill(-1)),prevNoise=new Uint8Array(64),prevFlip=new Uint8Array(64),prevFeedback=new Uint8Array(64);
 for(const [k,y,flip,noise,probe,age] of rows){
  const pp=[h+(1-2*h)*b4[k]/14,h+(1-2*h)*b8[k]/254,h+(1-2*h)*exact[k]];
  let ones=0;for(let j=0;j<cnt[k];j++)ones+=(win[k]>>>j)&1;
  const acts=[last[k],sat[k]>0?1:0,ones*2>cnt[k]?1:0,...pp.map(p=>p>.5?1:0)];
  const truth=pp[2],best=Math.max(truth,1-truth),z=probe?null:y^noise;
  for(let i=0;i<names.length;i++){
   const action=acts[i],regret=Math.max(0,best-(action?truth:1-truth)),ok=action===y?1:0;
   const inds=[0,probe?2:1];if(probe&&!flip)inds.push(3);if(flip)inds.push(4);else if(age>=1&&age<=3)inds.push(5);else if(age>=4)inds.push(6);
   for(const j of inds){const v=data[i][j];v[0]+=ok;v[1]++;v[2]+=regret;}
   if(!flip&&prevFeedback[k]&&prevNoise[k]&&!prevFlip[k]&&prev[i][k]>=0){const v=data[i][7];v[0]+=action!==prev[i][k]?1:0;v[1]++;}
   prev[i][k]=action;
   if(!probe){const reward=action===z?1:-1,observed=reward===1?action:1-action;if(observed!==z)throw Error("feedback mismatch");}
  }
  if(z!==null){last[k]=z;sat[k]=Math.max(-3,Math.min(3,sat[k]+(z?1:-1)));win[k]=((win[k]<<1)|z)&127;cnt[k]=Math.min(7,cnt[k]+1);}
  b4[k]=Math.round(update(pp[0],z,q)*14);b8[k]=Math.round(update(pp[1],z,q)*254);exact[k]=update(pp[2],z,q);
  prevNoise[k]=noise;prevFlip[k]=flip;prevFeedback[k]=probe?0:1;
 }
 return {seed,tape_sha256:sha256(Uint8Array.from(rows.flat())),data};
}

function experiment(){
 if(sha256(new Uint8Array([97,98,99]))!=="ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")throw Error("sha256 selftest");
 const posterior=checkBayes(),names=["LAST","SAT3","WIN7","BAYES4","BAYES8","BAYES64"],metrics=["all","feedback","return","return_unchanged","flip","recent","stable","spurious_after_noise"],conditions=[];
 for(const q of [.10,.25])for(const h of [0,.01,.05]){
  const worlds=Array.from({length:64},(_,i)=>runWorld(31000+i,h,q));const summary=names.map((name,i)=>({name,metrics:Object.fromEntries(metrics.map((m,j)=>{const v=worlds.reduce((a,w)=>a.map((x,k)=>x+w.data[i][j][k]),[0,0,0]);return [m,{correct_or_events:v[0],n:v[1],rate:v[1]?v[0]/v[1]:null,mean_conditional_regret:v[1]&&j!==7?v[2]/v[1]:null}];}))}));
  conditions.push({q,h,summary,worlds});
 }
 const stop=conditions.every(c=>{const b=c.summary.find(x=>x.name==="BAYES8").metrics;return b.all.mean_conditional_regret<=.01&&b.return.mean_conditional_regret<=.01;});
 return {stage:"NSR01",posterior_check:posterior,arms:names,metrics,state_bits_per_pair:[1,3,10,4,8,64],state_bits_total:[64,192,640,256,512,4096],worlds_per_condition:64,steps_per_world:1024,conditions,stop_independent_family:stop,ci_jobs:0,neuronal_runs:0,historical_seeds_used:0};
}
console.log(JSON.stringify(experiment()));
