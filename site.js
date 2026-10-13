(function(){
var root=document.documentElement;root.classList.add('js');
function $(id){return document.getElementById(id)}
function all(sel,el){return [].slice.call((el||document).querySelectorAll(sel))}
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
/* the same folding as catalog.py: "xerek" finds "xərək", "елка" finds "ёлка" */
function fold(s){s=s.toLowerCase().replace(/̇/g,'');var m={'ə':'e','ı':'i','ö':'o','ü':'u','ş':'s','ç':'c','ğ':'g','ё':'е'};return s.replace(/[əıöüşçğё]/g,function(c){return m[c]})}

/* A freshly opened page starts at its top; back/forward keeps the browser's own position.
   Inside an embedding frame (a preview window) the host may keep its old scroll offset, so there the page
   also asks to be brought to its top again while it loads, until the visitor starts scrolling. */
(function(){
  var framed=false;try{framed=window.self!==window.top}catch(e){framed=true}
  var nav=null;try{nav=performance.getEntriesByType('navigation')[0]}catch(e){}
  var fresh=!location.hash&&(!nav||nav.type==='navigate'||framed&&nav.type!=='back_forward');
  function up(){try{window.scrollTo(0,0)}catch(e){}
    try{document.documentElement.scrollTop=0;if(document.body)document.body.scrollTop=0}catch(e){}
    var h=document.querySelector('.top');if(framed&&h&&h.scrollIntoView){try{h.scrollIntoView({block:'start',behavior:'instant'})}catch(e){h.scrollIntoView(true)}}}
  if(!fresh)return;
  up();
  if(!framed)return;
  try{history.scrollRestoration='manual'}catch(e){}
  var stop=false,timers=[0,60,200,500,1000,1800].map(function(ms){return setTimeout(function(){if(!stop)up()},ms)});
  function quit(){stop=true;timers.forEach(clearTimeout)}
  ['wheel','touchstart','keydown','pointerdown'].forEach(function(t){window.addEventListener(t,quit,{passive:true,once:true})});
  window.addEventListener('load',function(){if(!stop)up()});
  /* leaving for another page of the site: bring this one to its top first, in case the frame's host keeps the offset */
  document.addEventListener('click',function(ev){
    if(ev.defaultPrevented||ev.button||ev.metaKey||ev.ctrlKey||ev.shiftKey||ev.altKey)return;
    var a=ev.target.closest&&ev.target.closest('a[href]');if(!a||a.target==='_blank'||a.hasAttribute('data-f'))return;
    var href=a.getAttribute('href');if(!href||href.charAt(0)==='#'||/^(https?:|mailto:|tel:)/.test(href))return;
    stop=true;window.scrollTo(0,0);var h=document.querySelector('.top');if(h&&h.scrollIntoView)h.scrollIntoView(true)},true);
})();

/* back-to-top button */
var tt=$('totop');
if(tt){var seen=false,tick=function(){var on=(window.pageYOffset||root.scrollTop)>window.innerHeight*1.5;if(on!==seen){seen=on;tt.hidden=!on}};
  window.addEventListener('scroll',tick,{passive:true});window.addEventListener('resize',tick);tick();
  tt.addEventListener('click',function(){window.scrollTo(0,0);var b=document.querySelector('.brand');if(b)b.focus({preventScroll:true})})}

/* search: the index is fetched the first time a field is used, and shared by every search field on the page */
var D=null,wait=null;
all('form.search').forEach(function(form){
  var f=form.querySelector('input'),box=form.querySelector('.sres'),base=form.getAttribute('data-base')||'';
  function load(){return wait||(wait=fetch(form.getAttribute('data-src')).then(function(r){return r.json()}).then(function(d){D=d}).catch(function(){wait=null}))}
  function close(){box.hidden=true;box.innerHTML=''}
  function run(){
    var q=fold(f.value.trim());if(q.length<2){close();return}
    if(!D){load().then(function(){if(D)run()});return}
    var t=q.split(/\s+/),r=[];
    D.forEach(function(p){if(t.every(function(x){return p.h.indexOf(x)>-1})){var s=p.n.indexOf(t[0]);r.push([s===0?0:s>0?1:2,p])}});
    r.sort(function(a,b){return a[0]-b[0]});
    box.innerHTML=r.length?r.slice(0,10).map(function(x){var p=x[1];return '<li><a href="'+base+p.u+'">'+(p.i?'<img src="'+base+p.i+'" alt="" width="44" height="44">':'')+'<span><b>'+p.t+'</b><small>'+p.k+'</small></span></a></li>'}).join(''):'<li class="none">'+esc(form.getAttribute('data-none'))+'</li>';
    box.hidden=false}
  f.addEventListener('input',run);f.addEventListener('focus',function(){load();run()});
  form.addEventListener('submit',function(ev){ev.preventDefault();var a=box.querySelector('a');if(a)location.href=a.href;else run()});
  form.addEventListener('keydown',function(ev){
    var links=all('a',box),i=links.indexOf(document.activeElement);
    if(ev.key==='ArrowDown'&&links.length){ev.preventDefault();links[Math.min(i+1,links.length-1)].focus()}
    else if(ev.key==='ArrowUp'&&links.length){ev.preventDefault();if(i<=0)f.focus();else links[i-1].focus()}
    else if(ev.key==='Escape'){close();f.blur()}});
  document.addEventListener('click',function(ev){if(!form.contains(ev.target))close()});
});

/* catalogue page: one list, narrowed by section and by words; nothing is fetched */
var fq=$('fq'),list=$('crows');
if(fq&&list){
  var rws=all('.row',list),chips=all('#fchips [data-f]'),fc=$('fcount'),none=$('fnone'),cur='';
  var apply=function(){
    var t=fold(fq.value.trim()).split(/\s+/).filter(Boolean),n=0;
    rws.forEach(function(r){
      var ok=(!cur||(' '+r.getAttribute('data-s')+' ').indexOf(' '+cur+' ')>-1)&&t.every(function(x){return r.getAttribute('data-h').indexOf(x)>-1});
      r.hidden=!ok;if(ok)n++});
    fc.textContent=(cur||t.length)?fc.getAttribute('data-t').replace('{n}',n).replace('{m}',rws.length):'';
    none.hidden=!!n;list.hidden=!n};
  var pick=function(key){cur=key;chips.forEach(function(x){x.setAttribute('aria-pressed',x.getAttribute('data-f')===key?'true':'false')});apply()};
  chips.forEach(function(c){c.setAttribute('role','button');c.addEventListener('click',function(ev){ev.preventDefault();pick(c.getAttribute('data-f'))})});
  fq.addEventListener('input',apply);
  var h=location.hash.slice(1);if(h&&chips.some(function(c){return c.getAttribute('data-f')===h}))pick(h);
}

/* request list: kept in this browser; falls back to memory when storage is unavailable */
var foot=$('foot');if(!foot)return;
var KEY='ta-list',ORG='ta-org',mem=null,F=foot.dataset;
function read(){if(mem)return mem;try{var v=JSON.parse(localStorage.getItem(KEY)||'[]');mem=Array.isArray(v)?v:[]}catch(e){mem=[]}return mem}
function write(v,quiet){mem=v;try{localStorage.setItem(KEY,JSON.stringify(v))}catch(e){}paint(quiet)}
var req=$('req'),R=req?req.dataset:null,items=$('ritems');
function field(id){var el=$(id);return el?el.value.trim():''}
function text(v){
  var out=R.hello+'\n'+v.map(function(x,i){return (i+1)+'. '+x.n+' — '+x.q+' '+R.unit}).join('\n');
  var extra=[[R.org,field('rorg')],[R.person,field('rname')],[R.note,field('rnote')]].filter(function(p){return p[1]}).map(function(p){return p[0]+': '+p[1]});
  return out+(extra.length?'\n\n'+extra.join('\n'):'')+'\n\n'+R.end}
function links(v){
  if(!req||!v.length)return;var m=text(v);
  $('rwa').href='https://wa.me/'+R.wa+'?text='+encodeURIComponent(m);
  $('rmail').href='mailto:'+R.mail+'?subject='+encodeURIComponent(R.subject)+'&body='+encodeURIComponent(m);
  var box=$('rtext');if(box)box.value=m}
function paint(quiet){
  var v=read(),ids={};v.forEach(function(x){ids[x.id]=1});
  all('[data-add]').forEach(function(b){
    var on=!!ids[b.getAttribute('data-add')];b.setAttribute('aria-pressed',on?'true':'false');
    var l=b.querySelector('.t');if(l)l.textContent=on?(b.getAttribute('data-on')||F.tAdded):(b.getAttribute('data-off')||F.tAdd)});
  all('.lcount').forEach(function(c){c.textContent=v.length;c.hidden=!v.length});
  if(!req)return;
  $('rempty').hidden=!!v.length;$('rbody').hidden=!v.length;
  if(!quiet)items.innerHTML=v.map(function(x,i){return '<li data-id="'+esc(x.id)+'"><span class="no">'+(i+1)+'</span>'+
    '<span class="inm">'+(x.u?'<a href="'+esc(x.u)+'">'+esc(x.n)+'</a>':'<a>'+esc(x.n)+'</a>')+'</span>'+
    '<span class="qty"><button type="button" data-q="-1" aria-label="'+esc(R.less)+'">−</button>'+
    '<input type="number" id="rq'+esc(x.id)+'" inputmode="numeric" min="1" max="9999" value="'+x.q+'" aria-label="'+esc(R.qty)+': '+esc(x.n)+'">'+
    '<button type="button" data-q="1" aria-label="'+esc(R.more)+'">+</button></span>'+
    '<button type="button" class="rm" data-rm aria-label="'+esc(R.remove)+': '+esc(x.n)+'" title="'+esc(R.remove)+'">'+
    '<svg class="i" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg></button></li>'}).join('');
  links(v)}
function clamp(n){n=parseInt(n,10);return isNaN(n)?1:Math.max(1,Math.min(9999,n))}
document.addEventListener('click',function(ev){
  var b=ev.target.closest('[data-add]');
  if(b){var id=b.getAttribute('data-add'),v=read().slice(),i=v.findIndex(function(x){return x.id===id});
    if(i>-1)v.splice(i,1);else v.push({id:id,n:b.getAttribute('data-name'),u:b.getAttribute('data-url'),q:1});write(v);return}
  var li=ev.target.closest('#ritems li');
  if(li){var id2=li.getAttribute('data-id'),v2=read().slice(),j=v2.findIndex(function(x){return x.id===id2});if(j<0)return;
    var q=ev.target.closest('[data-q]');
    if(q){v2[j]=Object.assign({},v2[j],{q:clamp(v2[j].q+Number(q.getAttribute('data-q')))});li.querySelector('input').value=v2[j].q;write(v2,true)}
    else if(ev.target.closest('[data-rm]')){v2.splice(j,1);write(v2)}}
});
if(req){
  items.addEventListener('input',function(ev){
    var li=ev.target.closest('li');if(!li||ev.target.tagName!=='INPUT')return;
    var id=li.getAttribute('data-id'),v=read().slice(),j=v.findIndex(function(x){return x.id===id});if(j<0||ev.target.value==='')return;
    v[j]=Object.assign({},v[j],{q:clamp(ev.target.value)});write(v,true)});
  items.addEventListener('change',function(ev){if(ev.target.tagName==='INPUT'){var li=ev.target.closest('li'),x=read().filter(function(y){return y.id===li.getAttribute('data-id')})[0];if(x)ev.target.value=x.q}});
  /* who is asking: remembered in this browser so the next request starts filled in */
  var saved={};try{saved=JSON.parse(localStorage.getItem(ORG)||'{}')||{}}catch(e){}
  ['rorg','rname','rnote'].forEach(function(id){var el=$(id);if(!el)return;if(id!=='rnote'&&saved[id])el.value=saved[id];
    el.addEventListener('input',function(){links(read());if(id!=='rnote'){saved[id]=el.value;try{localStorage.setItem(ORG,JSON.stringify(saved))}catch(e){}}})});
  $('rclear').addEventListener('click',function(){write([])});
  var cp=$('rcopy'),lbl=cp.querySelector('span'),orig=lbl.textContent;
  cp.addEventListener('click',function(){
    var m=text(read()),box=$('rtext'),done=function(){lbl.textContent=R.copied;setTimeout(function(){lbl.textContent=orig},1800)};
    var manual=function(){box.hidden=false;box.value=m;box.focus();box.select();try{if(document.execCommand('copy'))done()}catch(e){}};
    if(navigator.clipboard&&navigator.clipboard.writeText)navigator.clipboard.writeText(m).then(done,manual);else manual()});
}
window.addEventListener('storage',function(ev){if(ev.key===KEY){mem=null;paint()}});
paint();
})();
