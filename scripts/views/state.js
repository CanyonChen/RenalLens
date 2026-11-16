/* Query-string state works when opening an exported file directly. */
(function() {
  "use strict";
  let keys=[];
  function links() {
    const patient=document.getElementById('patient');
    if(!patient) return;
    for(const link of document.querySelectorAll('[data-carry-patient]')) {
      const url=new URL(link.getAttribute('href'),location.href);
      url.searchParams.set('patient',patient.value);
      const feature=document.getElementById('feature') || document.getElementById('log-feature');
      if(feature) url.searchParams.set('feature',feature.value);
      link.setAttribute('href',url.href);
    }
  }
  function save() {
    const url=new URL(location.href);
    for(const id of keys) {
      const control=document.getElementById(id);
      if(control) url.searchParams.set(id,control.type==='checkbox'?String(control.checked):control.value);
    }
    history.replaceState(null,'',url);
    links();
  }
  function restore(ids) {
    keys=ids;
    const params=new URLSearchParams(location.search);
    for(const id of keys) {
      const control=document.getElementById(id), value=params.get(id);
      if(!control || value===null) continue;
      if(control.type==='checkbox') control.checked=value==='true';
      else if(control.tagName!=='SELECT' || [...control.options].some(o=>o.value===value)) control.value=value;
    }
    document.addEventListener('change',()=>queueMicrotask(save));
    links();
  }
  globalThis.RenalState={restore,save,links};
})();
