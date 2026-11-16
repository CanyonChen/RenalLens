/* Shared arithmetic for the offline explorer; also exercised by node:test. */
(function(root) {
  "use strict";
  function quantile(values, probability) {
    const ordered=values.filter(Number.isFinite).slice().sort((a,b)=>a-b);
    if(!ordered.length) return null;
    const index=(ordered.length-1)*probability, lo=Math.floor(index), hi=Math.ceil(index);
    return ordered[lo]+(ordered[hi]-ordered[lo])*(index-lo);
  }
  function ranks(values) {
    const order=values.map((value,index)=>({value,index})).sort((a,b)=>a.value-b.value), result=[];
    for(let i=0;i<order.length;) {
      let j=i+1;
      while(j<order.length && order[j].value===order[i].value) j++;
      for(let k=i;k<j;k++) result[order[k].index]=(i+j+1)/2;
      i=j;
    }
    return result;
  }
  function correlation(points, method) {
    const finite=points.filter(p=>p.every(Number.isFinite));
    if(finite.length<2) return null;
    let x=finite.map(p=>p[0]), y=finite.map(p=>p[1]);
    if(method==='spearman') { x=ranks(x); y=ranks(y); }
    const mean=a=>a.reduce((sum,v)=>sum+v,0)/a.length, mx=mean(x), my=mean(y);
    let numerator=0, xx=0, yy=0;
    x.forEach((v,i)=>{const a=v-mx,b=y[i]-my;numerator+=a*b;xx+=a*a;yy+=b*b;});
    return xx>0 && yy>0 ? Math.max(-1,Math.min(1,numerator/Math.sqrt(xx*yy))) : null;
  }
  function retained(patient, rule, core, current) {
    if(rule==='all24') return patient.missing.length===0;
    const fields=rule==='core5'?core:current;
    return fields.every(f=>!patient.missing.includes(f));
  }
  const api={quantile,correlation,retained};
  root.RenalMath=api;
  if(typeof module!=='undefined' && module.exports) module.exports=api;
})(globalThis);
