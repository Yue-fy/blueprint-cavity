// Keyboard and dialog behavior are independent of the 3D renderers.
const liveDialog = document.getElementById('live');
const liveCard = liveDialog.querySelector('.card');
liveCard.setAttribute('role','dialog');
liveCard.setAttribute('aria-modal','true');
liveCard.setAttribute('aria-label','Local reply checker');
liveCard.tabIndex = -1;
let previousFocus;
const openLive = document.getElementById('liveopen').onclick;
document.getElementById('liveopen').onclick = () => {
  previousFocus = document.activeElement;
  openLive();
  document.querySelector('main').inert = true;
  document.querySelector('header').inert = true;
  document.querySelector('.research-heading').inert = true;
  document.querySelector('.research-footer').inert = true;
  liveCard.focus();
};
function closeLive() {
  liveDialog.classList.remove('show');
  document.querySelectorAll('[inert]').forEach(e => e.inert = false);
  previousFocus?.focus();
}
document.getElementById('liveclose').onclick = closeLive;
liveDialog.addEventListener('click', e => { if (e.target === liveDialog) closeLive(); });
document.addEventListener('keydown', e => {
  if (!liveDialog.classList.contains('show')) return;
  if (e.key === 'Escape') { e.preventDefault(); closeLive(); return; }
  if (e.key !== 'Tab') return;
  const buttons = [...liveCard.querySelectorAll('button,input,textarea,select,a[href],[tabindex="0"]')].filter(el => !el.disabled && el.offsetParent);
  const first = buttons[0], last = buttons.at(-1);
  if (e.shiftKey && (document.activeElement === first || document.activeElement === liveCard)) { e.preventDefault(); last.focus(); }
  else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
}, true);
const zoomControls = (viewport, zoom) => {
  const panel = document.createElement('div'); panel.className = 'view-controls';
  for (const [label, value, symbol] of [['Zoom in',.8,'+'],['Zoom out',1.25,'−'],['Reset view',0,'↺']]) {
    const button = document.createElement('button'); button.type='button'; button.textContent=symbol; button.setAttribute('aria-label',label); button.onclick = () => zoom(value); panel.appendChild(button);
  }
  viewport.appendChild(panel);
};
if (renderer) zoomControls(document.getElementById('viewport'), factor => { orb = factor ? {...orb,r:Math.max(500,Math.min(4000,orb.r*factor))} : {...HOME}; });
if (window.sqInst?.zoom) zoomControls(document.getElementById('sqview'), factor => sqInst.zoom(factor));
document.getElementById('c3d').addEventListener('pointercancel', () => { drag = null; });
document.getElementById('qplot').addEventListener('pointercancel', () => { qDrag = null; });
if (matchMedia('(prefers-reduced-motion: reduce)').matches) { if (playing) togglePlay(); sqInst?.freeze(); }
document.querySelectorAll('.tab').forEach(tab => tab.addEventListener('click', () => tab.scrollIntoView({block:'nearest',inline:'nearest'})));
