'use strict';
document.addEventListener('click',event=>{
 const open=event.target.closest('[data-open]'); if(open) document.getElementById(open.dataset.open)?.showModal();
 const close=event.target.closest('[data-close]'); if(close) close.closest('dialog').close();
 const dismiss=event.target.closest('[data-dismiss]'); if(dismiss) dismiss.closest('.message').remove();
 if(event.target.closest('[data-menu]')) document.getElementById('sidebar').classList.toggle('visible');
 const tab=event.target.closest('[data-tab]'); if(tab){
  document.querySelectorAll('[data-tab]').forEach(b=>{b.classList.toggle('active',b===tab);b.setAttribute('aria-selected',b===tab?'true':'false');});
  document.querySelectorAll('.tab-panel').forEach(p=>{p.hidden=p.id!=='tab-'+tab.dataset.tab;p.classList.toggle('active',!p.hidden);});
  history.replaceState(null,'','#'+tab.dataset.tab);
 }
});
const hash=location.hash.slice(1); if(hash) document.querySelector('[data-tab="'+CSS.escape(hash)+'"]')?.click();
document.querySelectorAll('dialog').forEach(d=>d.addEventListener('click',e=>{if(e.target===d){const r=d.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)d.close();}}));
document.querySelectorAll('form').forEach(form=>form.addEventListener('submit',()=>{
 if(form.method.toLowerCase()==='post') setTimeout(()=>{form.querySelectorAll('button[type="submit"],button:not([type])').forEach(b=>{b.disabled=true;b.classList.add('loading');});},0);
}));
document.querySelectorAll('[data-print]').forEach(button=>button.addEventListener('click',()=>window.print()));

const rolePermissions={chair:['edit','finance','discount','export','audit','approve'],accountant:['edit','finance','export'],clerk:['edit'],viewer:[]};
document.addEventListener('change',event=>{
 const role=event.target.closest('[data-permission-preset]'); if(!role)return;
 const form=role.closest('form'); const allowed=rolePermissions[role.value]||[];
 form.querySelectorAll('input[name="permissions"]').forEach(input=>{input.checked=allowed.includes(input.value);});
});
