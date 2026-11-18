/* SBC5 3.3.0 — read-only grouped diagnostics. Never renders sensor text as HTML. */
(() => {
  'use strict';
  const groups = [
    {id:'cpu',name:'CPU i wydajność',icon:'🖥️',patterns:[/cpu(?!.*(?:ai_|thermal_))/i,/core_[0-9]/i,/clock|frequency|overclock|throttl/i]},
    {id:'cooling',name:'Chłodzenie i wentylator',icon:'🌬️',patterns:[/fan|pwm|cooling|cooler|curve|calibrat/i]},
    {id:'ai',name:'AI Cooling',icon:'🧠',patterns:[/ai_(?!thermal)|ai_cooling|learning|qualified|training|workload|dynamic_quality/i]},
    {id:'predictor',name:'Thermal Predictor',icon:'📈',patterns:[/thermal|forecast|predictor|shadow|mae/i]},
    {id:'power',name:'Zasilanie i PMIC',icon:'⚡',patterns:[/pmic|power|supply|vdd|voltage|current|usb/i]},
    {id:'system',name:'System, pamięć i sieć',icon:'🌐',patterns:[/network|ethernet|memory|swap|rootfs|disk|storage|uptime|firmware|operating|version|system|architecture|boot/i]},
    {id:'other',name:'Pozostałe sensory SBC5',icon:'📋',patterns:[]}
  ];
  let loading=false, lastLoaded=0;
  const $=id=>document.getElementById(id);
  const active=()=>document.body.dataset.sbc5Tab==='diagnostics';
  function classify(e){
    const id=String(e.entity_id||'').replace(/^(?:sensor|binary_sensor)\.sbc5_/,'');
    for(const group of groups.slice(0,-1)){
      if(group.patterns.some(re=>re.test(id)))return group.id;
    }
    return 'other';
  }
  const node=(tag,klass,txt)=>{
    const el=document.createElement(tag);
    if(klass)el.className=klass;
    if(txt!==undefined)el.textContent=String(txt);
    return el;
  };
  function render(items){
    const root=$('sbc5DiagnosticsGroups');if(!root)return;
    const grouped=new Map(groups.map(g=>[g.id,[]]));
    for(const e of items){
      if(!e||typeof e.entity_id!=='string'||! /^(sensor|binary_sensor)\.sbc5_[a-z0-9_]+$/.test(e.entity_id))continue;
      grouped.get(classify(e)).push(e);
    }
    const fragment=document.createDocumentFragment();
    for(const g of groups){
      const entries=grouped.get(g.id);
      if(!entries.length)continue;
      entries.sort((a,b)=>String(a.name||a.entity_id).localeCompare(String(b.name||b.entity_id),'pl'));
      const section=node('details','sbc5-diag-section');
      section.open=g.id==='cpu'||g.id==='cooling';
      const summary=node('summary','sbc5-diag-summary');
      summary.append(node('span','sbc5-diag-group-name',g.icon+' '+g.name),node('span','sbc5-diag-count',entries.length));
      section.append(summary);
      const list=node('div','sbc5-diag-list');
      for(const e of entries){
        const row=node('div','sbc5-diag-row');
        const label=node('div','sbc5-diag-label',e.name||e.entity_id);
        label.title=e.entity_id;
        const value=node('div','sbc5-diag-value',(e.state===undefined?'—':e.state)+(e.unit?' '+e.unit:''));
        row.append(label,value);
        list.append(row);
      }
      section.append(list);fragment.append(section);
    }
    root.replaceChildren(fragment);
    $('sbc5DiagnosticsCount').textContent=String(items.length)+' encji SBC5';
  }
  async function refresh(force){
    if(!active()||loading||document.hidden)return;
    if(!force&&Date.now()-lastLoaded<15000)return;
    loading=true;
    const status=$('sbc5DiagnosticsStatus');
    status.textContent='Odczyt sensorów…';
    try {
      const response=await fetch('api/diagnostics/entities',{cache:'no-store',credentials:'same-origin'});
      if(!response.ok)throw Error('HTTP '+response.status);
      const payload=await response.json();
      if(!payload||payload.ok!==true||!Array.isArray(payload.entities))throw Error('Nieprawidłowa odpowiedź');
      render(payload.entities);
      lastLoaded=Date.now();
      status.textContent='Ostatni odczyt: '+new Date().toLocaleTimeString('pl-PL');
    } catch(_err) {
      status.textContent='Nie można pobrać sensorów. Sprawdź połączenie Home Assistant i odśwież.';
    } finally {loading=false;}
  }
  function select(tab){
    const diagnostics=tab==='diagnostics';
    document.body.dataset.sbc5Tab=diagnostics?'diagnostics':'configuration';
    $('sbc5ConfigTab').hidden=diagnostics;
    $('sbc5DiagnosticsTab').hidden=!diagnostics;
    $('sbc5TabConfig').setAttribute('aria-selected',String(!diagnostics));
    $('sbc5TabDiagnostics').setAttribute('aria-selected',String(diagnostics));
    if(diagnostics)refresh(true);
  }
  $('sbc5TabConfig').addEventListener('click',()=>select('configuration'));
  $('sbc5TabDiagnostics').addEventListener('click',()=>select('diagnostics'));
  $('sbc5DiagnosticsRefresh').addEventListener('click',()=>refresh(true));
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh(false)});
  window.setInterval(()=>refresh(false),30000);
  select('configuration');
})();
