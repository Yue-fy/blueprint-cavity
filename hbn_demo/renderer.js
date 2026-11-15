function createHbnRenderer(canvas, viewport) {
  try {
    const context = canvas.getContext('webgl2', {alpha:true, antialias:true, preserveDrawingBuffer:true}) || canvas.getContext('webgl', {alpha:true, antialias:true, preserveDrawingBuffer:true});
    if (context) return new THREE.WebGLRenderer({canvas, context, antialias:true, alpha:true, preserveDrawingBuffer:true});
  } catch (_) { /* The numerical and 2D panels are independent of WebGL. */ }
  canvas.hidden = true;
  const notice = document.createElement('div');
  notice.className = 'no-webgl';
  notice.setAttribute('role', 'status');
  notice.innerHTML = '<strong>3D view unavailable</strong><p>This browser could not create a WebGL context. Explore the mode map, linewidth windows and mathematical checks using the tabs above.</p>';
  viewport.appendChild(notice);
  return null;
}
