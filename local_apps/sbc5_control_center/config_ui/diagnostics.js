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
  let loading=false, lastLoaded=0, compact=true, search='', records=[];
  const $=id=>document.getElementById(id);
  const active=()=>document.body.dataset.sbc5Tab==='diagnostics';
  function classify(e){
    const id=String(e.entity_id||'').replace(/^(?:sensor|binary_sensor)\.sbc5_/,'');
    // Prioritize predictive/AI entities: their names can contain "PWM",
    // "CPU" or "fan", which must not move them into physical controls.
    if(/^(?:ai_thermal_|thermal_predictor|thermal_shadow)|(?:forecast|predictor)/i.test(id))return 'predictor';
    if(/^(?:ai_|workload_|dynamic_quality)|(?:qualified|learning)/i.test(id))return 'ai';
    if(/(?:^|_)(?:pmic|power|supply|vdd|voltage|current|usb)(?:_|$)/i.test(id))return 'power';
    if(/(?:fan|pwm|cooling|cooler|curve|calibrat)/i.test(id))return 'cooling';
    if(/(?:cpu|core_[0-9]|clock|frequency|overclock|throttl)/i.test(id))return 'cpu';
    if(/(?:network|ethernet|memory|swap|rootfs|disk|storage|uptime|firmware|operating|version|system|architecture|boot)/i.test(id))return 'system';
    return 'other';
  }
  const node=(tag,klass,txt)=>{
    const el=document.createElement(tag);
    if(klass)el.className=klass;
    if(txt!==undefined)el.textContent=String(txt);
    return el;
  };

  // Presentation-only labels; original entity_id and HA state remain untouched.
  function shortName(entity){
    const id=String(entity.entity_id||'').replace(/^(?:sensor|binary_sensor)\.sbc5_/,'');
    const core=id.match(/(?:^|_)cpu_core_([0-9]+)_(frequency|usage)$/);
    if(core)return 'Rdzeń '+core[1]+' · '+(core[2]==='usage'?'Obciążenie':'Taktowanie');
    const common=[
      [/(?:^|_)cpu_temperature$/,'Temperatura CPU'],
      [/(?:^|_)cpu_usage$/,'Obciążenie CPU'],
      [/(?:^|_)fan_percent$/,'Prędkość wentylatora'],
      [/(?:^|_)fan_rpm$/,'Obroty wentylatora'],
      [/(?:^|_)fan_pwm$/,'PWM (0–255)'],
      [/(?:^|_)ai_confidence$/,'Pewność AI'],
      [/(?:^|_)ai_qualified_samples$/,'Próbki jakościowe'],
      [/(?:^|_)ai_thermal_predictor_quality$/,'Jakość prognozy'],
      [/(?:^|_)pmic_temperature$/,'Temperatura PMIC']
    ];
    for(const [pattern,name] of common)if(pattern.test(id))return name;
    let label=String(entity.name||entity.entity_id);
    label=label.replace(/^(?:(?:SBC5 Control Center|SBC5)\s*)+/i,'');
    if(classify(entity)==='predictor')label=label.replace(/^(?:AI\s+)?Thermal\s+Predictor\s*/i,'');
    if(classify(entity)==='ai')label=label.replace(/^AI\s+/i,'');
    return label.trim()||id.replace(/_/g,' ');
  }
  const fold=value=>String(value??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
  function tone(entity){
    const id=String(entity.entity_id||'').toLowerCase();
    const value=String(entity.state??'').toLowerCase();
    if(['unknown','unavailable','none'].includes(value))return 'missing';
    if(/(?:problem|issue|throttling|high_temperature|low_disk|high_memory|fault)/.test(id)){
      if(value==='on'||value==='true')return 'danger';
      if(value==='off'||value==='false'||value==='ok')return 'good';
    }
    if(['critical','failed','error','fault'].includes(value))return 'danger';
    if(['warning','degraded','probation','quality_below_good'].includes(value))return 'warning';
    if(['ok','good','ready','active','eligible','assist','current'].includes(value))return 'good';
    if(['forecast_hot','forecast_hot_strong','learning','pending'].includes(value))return 'info';
    return 'neutral';
  }
  function displayValue(entity){
    const value=String(entity.state??'—');
    if(['unknown','unavailable','none'].includes(value.toLowerCase()))return 'Brak danych';
    return value+(entity.unit?' '+entity.unit:'');
  }
  function valueBadge(entity){
    const wrap=node('div','sbc5-diag-value');
    const pill=node('span','sbc5-diag-pill tone-'+tone(entity),displayValue(entity));
    pill.title=entity.entity_id;
    wrap.append(pill);
    const percent=Number(entity.state);
    if(entity.unit==='%'&&Number.isFinite(percent)&&percent>=0&&percent<=100){
      const track=node('span','sbc5-diag-progress');
      track.setAttribute('aria-hidden','true');
      const fill=node('span','sbc5-diag-progress-fill');
      fill.style.width=String(percent)+'%';
      track.append(fill);wrap.append(track);
    }
    return wrap;
  }
  const highlights=[
    ['🌡️','CPU',/(?:^|_)cpu_temperature$/],
    ['🌬️','Wentylator',/(?:^|_)fan_percent$/],
    ['⚙️','Obroty',/(?:^|_)fan_rpm$/],
    ['🧠','Pewność AI',/(?:^|_)ai_confidence$/],
    ['📈','Prognoza',/(?:^|_)ai_thermal_predictor_quality$/],
    ['⚡','PMIC',/(?:^|_)pmic_temperature$/]
  ];
  function renderHighlights(){
    const box=$('sbc5DiagnosticsHighlights');
    const fragment=document.createDocumentFragment();
    let count=0;
    for(const [icon,label,pattern] of highlights){
      const item=records.find(e=>pattern.test(e.entity_id));
      if(!item)continue;
      count++;
      const card=node('div','sbc5-diag-metric');
      card.append(node('span','sbc5-diag-metric-label',icon+' '+label));
      card.append(node('strong','sbc5-diag-metric-value',displayValue(item)));
      fragment.append(card);
    }
    box.replaceChildren(fragment);
    box.hidden=count===0;
  }
  function setCompact(value){
    compact=value;
    $('sbc5DiagnosticsCompact').setAttribute('aria-pressed',String(compact));
    $('sbc5DiagnosticsFull').setAttribute('aria-pressed',String(!compact));
    render(records);
  }

  function render(items){
    const root=$('sbc5DiagnosticsGroups');if(!root)return;
    // Preserve open groups during background refresh, including user choices.
    const opened=new Map(Array.from(root.querySelectorAll('details[data-group]'))
      .map(section=>[section.dataset.group,section.open]));
    const grouped=new Map(groups.map(g=>[g.id,[]]));
    for(const e of items){
      if(!e||typeof e.entity_id!=='string'||! /^(sensor|binary_sensor)\.sbc5_[a-z0-9_]+$/.test(e.entity_id))continue;
      if(search&&!fold(shortName(e)+' '+e.name+' '+e.entity_id+' '+e.state).includes(search))continue;
      grouped.get(classify(e)).push(e);
    }
    const fragment=document.createDocumentFragment();
    for(const g of groups){
      const entries=grouped.get(g.id);
      if(!entries.length)continue;
      entries.sort((a,b)=>shortName(a).localeCompare(shortName(b),'pl'));
      const section=node('details','sbc5-diag-section');
      section.dataset.group=g.id;
      section.open=search?true:(opened.has(g.id)?opened.get(g.id):g.id==='cpu'||g.id==='cooling');
      const summary=node('summary','sbc5-diag-summary');
      const heading=node('span','sbc5-diag-heading');
      heading.append(node('span','sbc5-diag-group-name',g.icon+' '+g.name));
      const previewMap={cpu:/(?:^|_)cpu_temperature$/,cooling:/(?:^|_)fan_percent$/,ai:/(?:^|_)ai_confidence$/,predictor:/(?:^|_)ai_thermal_predictor_quality$/,power:/(?:^|_)pmic_temperature$/,system:/(?:^|_)memory_used$/};
      const preview=entries.find(e=>previewMap[g.id]?.test(e.entity_id));
      if(preview)heading.append(node('small','sbc5-diag-group-preview',shortName(preview)+': '+displayValue(preview)));
      summary.append(heading,node('span','sbc5-diag-count',entries.length+' encji'));
      section.append(summary);
      const list=node('div','sbc5-diag-list');
      const shown=compact&&!search?entries.slice(0,8):entries;
      for(const e of shown){
        const row=node('div','sbc5-diag-row');
        const label=node('div','sbc5-diag-label');
        const brief=node('span','sbc5-diag-short',shortName(e));
        brief.title=e.name||e.entity_id;
        label.append(brief);
        if(!compact)label.append(node('small','sbc5-diag-entity',e.entity_id));
        row.append(label,valueBadge(e));
        list.append(row);
      }
      if(shown.length<entries.length){
        const footer=node('div','sbc5-diag-footer','+'+(entries.length-shown.length)+' pozostałych · ');
        const more=node('button','sbc5-diag-show-all','Pokaż wszystkie');
        more.type='button';
        more.addEventListener('click',()=>setCompact(false));
        footer.append(more);list.append(footer);
      }
      section.append(list);fragment.append(section);
    }
    if(!fragment.childNodes.length)fragment.append(node('p','sbc5-diag-empty',search?'Brak pasujących sensorów.':'Brak dostępnych sensorów SBC5.'));
    root.replaceChildren(fragment);
    const shown=Array.from(grouped.values()).reduce((sum,entries)=>sum+entries.length,0);
    $('sbc5DiagnosticsCount').textContent=search?shown+' z '+items.length+' encji':items.length+' encji SBC5';
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
      // A request started in Diagnostics may finish after switching tabs.
      if(!active())return;
      records=payload.entities;
      renderHighlights();
      render(records);
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
  $('sbc5DiagnosticsSearch').addEventListener('input',event=>{
    search=fold(event.target.value.trim());
    render(records);
  });
  $('sbc5DiagnosticsCompact').addEventListener('click',()=>setCompact(true));
  $('sbc5DiagnosticsFull').addEventListener('click',()=>setCompact(false));
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh(false)});
  window.setInterval(()=>refresh(false),30000);
  select('configuration');
})();
