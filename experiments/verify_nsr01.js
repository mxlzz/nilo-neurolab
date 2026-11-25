/* Independent replay implementation for NSR01 metrics; same deterministic tapes. */
function verify(r){
 function rng(seed,salt){let x=(Math.imul(seed,0x9e3779b1)^salt)>>>0;if(!x)x=1;return()=>{x^=x<<13;x^=x>>>17;x^=x<<5;return(x>>>0)/4294967296;};}
 const result={stage:"NSR01_secondary_metric_correction",definition:"recent = encounter 1..3 after an actual latent flip; never-flipped initial visits excluded",source_result_sha256:"5745c031c58af7fba5164d7101d073d005453b74b1a7cc2d0ad4f1cd2dafb679",arms:r.arms,conditions:[],same_tapes:true,old_primary_unchanged:true};
 const mi=r.metrics.indexOf("recent"),primary=r.metrics.indexOf("all"),ret=r.metrics.indexOf("return");
 const check=(b,m)=>{if(!b)throw Error(m);};
 let checks=0,ma=0,mr=0;
 for(const c of r.conditions){
  const {q,h}=c,worlds=[];
  for(const w of c.worlds){
   const ini=rng(w.seed,0xb573a9bd),fl=rng(w.seed,0x6e2bc799),noi=rng(w.seed,0x52ce8a39),ord=rng(w.seed,0x1a1ff349);
   const state=Array.from({length:64},()=>({y:ini()<.5?0:1,age:0,ever:false,last:0,sat:0,win:[],p:[7,127,.5]}));
   const all=Array.from({length:6},()=>[0,0,0]),returns=Array.from({length:6},()=>[0,0,0]),recent=Array.from({length:6},()=>[0,0,0]);
   for(const [block,ctx] of [0,1,2,3,0,2,1,3].entries())for(let sweep=0;sweep<8;sweep++){
    const xs=Array.from({length:16},(_,i)=>i);for(let j=15;j>0;j--){let k=Math.floor(ord()*(j+1));[xs[j],xs[k]]=[xs[k],xs[j]];}
    for(const x of xs){let s=state[16*ctx+x],flip=fl()<h,noise=noi()<q,probe=block>=4&&sweep===0;if(flip){s.y^=1;s.age=0;s.ever=true;}else s.age++;
     const pp=[h+(1-2*h)*s.p[0]/14,h+(1-2*h)*s.p[1]/254,h+(1-2*h)*s.p[2]],a=[s.last,+(s.sat>0),+(s.win.reduce((a,b)=>a+b,0)*2>s.win.length),...pp.map(p=>+(p>.5))],z=probe?null:s.y^Number(noise),truth=pp[2],best=Math.max(truth,1-truth);
     for(let i=0;i<6;i++){const correct=+(a[i]===s.y),loss=Math.max(0,best-(a[i]?truth:1-truth));
      for(const v of [all[i],...(probe?[returns[i]]:[]),...(!flip&&s.ever&&s.age>=1&&s.age<=3?[recent[i]]:[])]){v[0]+=correct;v[1]++;v[2]+=loss;}
     }
     if(z!==null){s.last=z;s.sat=Math.max(-3,Math.min(3,s.sat+(z?1:-1)));s.win.push(z);if(s.win.length>7)s.win.shift();}
     s.p=pp.map((p,i)=>{let newp=p;if(z!==null){const l=z===1?1-q:q,m=1-l;newp=p*l/(p*l+(1-p)*m);}if(i===2)return newp;return Math.round(newp*(i===0?14:254));});
    }
   }
   for(let i=0;i<6;i++){const x=w.data[i][primary],y=w.data[i][ret];check(all[i][0]===x[0]&&all[i][1]===x[1],`all counts ${q}/${h}/${w.seed}/${i}: ${all[i]} vs ${x}`);check(returns[i][0]===y[0]&&returns[i][1]===y[1],"return counts");ma=Math.max(ma,Math.abs(all[i][2]-x[2]));mr=Math.max(mr,Math.abs(returns[i][2]-y[2]));check(recent[i][1]<=w.data[i][mi][1],"recent subset");checks+=2;}
   worlds.push({seed:w.seed,recent});
  }
  const summary=r.arms.map((name,i)=>{let z=worlds.reduce((a,w)=>a.map((v,k)=>v+w.recent[i][k]),[0,0,0]);return {name,n:z[1],accuracy:z[1]?z[0]/z[1]:null,mean_conditional_regret:z[1]?z[2]/z[1]:null};});
  result.conditions.push({q,h,summary,worlds});
 }
 check(ma<1e-8&&mr<1e-8,"regret check");result.primary_replay={checks,maximum_absolute_sum_error_all:ma,maximum_absolute_sum_error_return:mr};return result;
}
const r=JSON.parse(require('fs').readFileSync(process.argv[2]||'evidence/NSR01_result.json','utf8'));
console.log(JSON.stringify(verify(r)));
