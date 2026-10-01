/* Film engine: deterministic, time-driven Canvas 2D helpers.
   Everything is a pure function of time t (seconds). */
(function () {
  const F = {};
  F.W = 1920; F.H = 1080; F.fps = 30;

  // ---------- math ----------
  F.clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
  F.lerp = (a, b, t) => a + (b - a) * t;
  F.map = (v, a, b, c, d, clampIt = true) => { let t = (v - a) / (b - a); if (clampIt) t = F.clamp(t); return c + (d - c) * t; };
  F.smooth = (t) => { t = F.clamp(t); return t * t * (3 - 2 * t); };
  F.ease = {
    linear: t => t,
    inQuad: t => t * t,
    outQuad: t => 1 - (1 - t) * (1 - t),
    inOutQuad: t => t < .5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2,
    outCubic: t => 1 - Math.pow(1 - t, 3),
    inCubic: t => t * t * t,
    inOutCubic: t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2,
    outQuart: t => 1 - Math.pow(1 - t, 4),
    inQuart: t => t * t * t * t,
    inOutQuart: t => t < .5 ? 8 * t * t * t * t : 1 - Math.pow(-2 * t + 2, 4) / 2,
    outQuint: t => 1 - Math.pow(1 - t, 5),
    inOutQuint: t => t < .5 ? 16 * t * t * t * t * t : 1 - Math.pow(-2 * t + 2, 5) / 2,
    outExpo: t => t >= 1 ? 1 : 1 - Math.pow(2, -10 * t),
    inExpo: t => t <= 0 ? 0 : Math.pow(2, 10 * t - 10),
    inOutExpo: t => t <= 0 ? 0 : t >= 1 ? 1 : t < .5 ? Math.pow(2, 20 * t - 10) / 2 : (2 - Math.pow(2, -20 * t + 10)) / 2,
    outBack: t => { const c = 1.70158; return 1 + (c + 1) * Math.pow(t - 1, 3) + c * Math.pow(t - 1, 2); },
    outCirc: t => Math.sqrt(1 - Math.pow(t - 1, 2)),
  };
  // progress of t between a and b, eased
  F.p = (t, a, b, e = 'linear') => (F.ease[e] || F.ease.linear)(F.clamp((t - a) / (b - a)));
  // 1 while t in [a,b] with fade in/out of f seconds
  F.win = (t, a, b, fi = 0, fo = 0, e = 'inOutQuad') => {
    if (t < a || t > b) return 0;
    let v = 1;
    if (fi > 0) v = Math.min(v, F.p(t, a, a + fi, e));
    if (fo > 0) v = Math.min(v, 1 - F.p(t, b - fo, b, e));
    return v;
  };
  // seeded hash noise
  F.hash = (x, y = 0, z = 0) => { let h = Math.sin(x * 127.1 + y * 311.7 + z * 74.7) * 43758.5453; return h - Math.floor(h); };
  F.noise1 = (x) => { const i = Math.floor(x), f = x - i; const a = F.hash(i), b = F.hash(i + 1); return F.lerp(a, b, F.smooth(f)); };
  // beats
  F.setTimeline = (tl) => { F.tl = tl; F.bpm = tl.bpm; F.beatLen = 60 / tl.bpm; F.barLen = 240 / tl.bpm; };
  F.beat = (t) => t / F.beatLen;           // continuous beat index
  F.bar = (t) => t / F.barLen;
  F.beatPhase = (t) => { const b = F.beat(t); return b - Math.floor(b); }; // 0..1 within beat
  // pulse that fires on every Nth beat (decay in beats)
  F.pulse = (t, every = 1, decay = 0.6, offset = 0) => { const b = F.beat(t) - offset; const ph = ((b % every) + every) % every; return Math.exp(-ph / decay * 4); };

  // ---------- color ----------
  F.hex = (h) => { const n = parseInt(h.slice(1), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; };
  F.rgb = (c, a = 1) => `rgba(${c[0]|0},${c[1]|0},${c[2]|0},${a})`;
  F.mixc = (h1, h2, t) => { const a = F.hex(h1), b = F.hex(h2); return [F.lerp(a[0], b[0], t), F.lerp(a[1], b[1], t), F.lerp(a[2], b[2], t)]; };
  F.withA = (h, a) => F.rgb(F.hex(h), a);

  // ---------- text ----------
  // family keys map to loaded @font-face names
  F.fonts = { sans: 'Inter', zh: 'Noto Sans SC', serif: 'Instrument Serif', zhserif: 'Noto Serif SC', grotesk: 'Space Grotesk' };
  F.font = (size, weight = 400, fam = 'sans', italic = false) => `${italic ? 'italic ' : ''}${weight} ${size}px "${F.fonts[fam] || fam}"`;
  // draw text with tracking (letter-spacing in em). Uses canvas letterSpacing so kerning is kept.
  F.text = (ctx, str, o) => {
    const { x = 0, y = 0, size = 48, weight = 400, fam = 'sans', color = '#fff', align = 'left', baseline = 'alphabetic', tracking = 0, alpha = 1, italic = false, blur = 0 } = o;
    if (alpha <= 0 || !str) return 0;
    ctx.save();
    ctx.globalAlpha *= alpha;
    ctx.font = F.font(size, weight, fam, italic);
    ctx.fillStyle = color;
    ctx.textBaseline = baseline;
    ctx.textAlign = 'left';
    if (blur > 0) ctx.filter = `blur(${blur}px)`;
    const sp = tracking * size;
    if ('letterSpacing' in ctx) ctx.letterSpacing = sp + 'px';
    let w = ctx.measureText(str).width;
    if (!('letterSpacing' in ctx)) w += sp * (Array.from(str).length - 1);
    const visible = w - (('letterSpacing' in ctx) ? sp : 0); // trailing spacing is not ink
    let cx = x; if (align === 'center') cx = x - visible / 2; else if (align === 'right') cx = x - visible;
    ctx.fillText(str, cx, y);
    ctx.restore();
    return visible;
  };
  F.textWidth = (ctx, str, o) => {
    const { size = 48, weight = 400, fam = 'sans', tracking = 0, italic = false } = o;
    ctx.save(); ctx.font = F.font(size, weight, fam, italic); const sp = tracking * size;
    if ('letterSpacing' in ctx) ctx.letterSpacing = sp + 'px';
    let w = ctx.measureText(str).width; if ('letterSpacing' in ctx) w -= sp; else w += sp * (Array.from(str).length - 1);
    ctx.restore(); return w;
  };
  // text that reveals character by character (n in 0..1)
  F.textReveal = (ctx, str, o, n) => { const chars = Array.from(str); const k = Math.round(F.clamp(n) * chars.length); return F.text(ctx, chars.slice(0, k).join(''), o); };

  // ---------- images ----------
  F.images = {};
  F.loadImage = (key, src) => new Promise((res, rej) => { const im = new Image(); im.onload = () => { F.images[key] = im; res(im); }; im.onerror = () => rej(new Error('img ' + src)); im.src = src; });
  // cover-fit rect for image into box, with zoom and focal offset (fx,fy in 0..1 = which point of the image sits at box center when zoomed)
  F.coverRect = (im, x, y, w, h, zoom = 1, fx = 0.5, fy = 0.5) => {
    const s = Math.max(w / im.width, h / im.height) * zoom;
    const dw = im.width * s, dh = im.height * s;
    const dx = x + w / 2 - dw * fx - (0.5 - fx) * w * 0; // anchor focal point to center
    const dy = y + h / 2 - dh * fy;
    // clamp so image always covers box
    const cx = F.clamp(dx, x + w - dw, x), cy = F.clamp(dy, y + h - dh, y);
    return { dx: cx, dy: cy, dw, dh, s };
  };
  F.drawCover = (ctx, im, x, y, w, h, zoom = 1, fx = 0.5, fy = 0.5, alpha = 1) => {
    if (alpha <= 0) return; const r = F.coverRect(im, x, y, w, h, zoom, fx, fy);
    ctx.save(); ctx.globalAlpha *= alpha; ctx.beginPath(); ctx.rect(x, y, w, h); ctx.clip(); ctx.drawImage(im, r.dx, r.dy, r.dw, r.dh); ctx.restore();
  };

  // ---------- mosaic ----------
  // offscreen cache of downsampled image → block colors
  F._small = {};
  // returns a canvas of size (cols x rows) holding the block-average colors of the cover-fitted image region
  F.blockCanvas = (im, cols, rows, x, y, w, h, zoom = 1, fx = 0.5, fy = 0.5) => {
    const k = [im.src, cols, rows, x | 0, y | 0, w | 0, h | 0, zoom.toFixed(3), fx.toFixed(3), fy.toFixed(3)].join('|');
    if (F._small[k]) return F._small[k];
    const c = document.createElement('canvas'); c.width = cols; c.height = rows;
    const g = c.getContext('2d'); g.imageSmoothingEnabled = true; g.imageSmoothingQuality = 'high';
    const r = F.coverRect(im, x, y, w, h, zoom, fx, fy);
    // map image region covering box (x,y,w,h) into cols x rows
    const sx = (x - r.dx) / r.s, sy = (y - r.dy) / r.s, sw = w / r.s, sh = h / r.s;
    // two-step downscale for quality
    let tmp = im, tsx = sx, tsy = sy, tsw = sw, tsh = sh;
    const steps = Math.max(1, Math.floor(Math.log2(Math.min(sw / cols, sh / rows))) );
    if (steps > 1) {
      const t2 = document.createElement('canvas'); const f = Math.pow(2, steps - 1);
      t2.width = Math.max(cols, Math.round(sw / f)); t2.height = Math.max(rows, Math.round(sh / f));
      const g2 = t2.getContext('2d'); g2.imageSmoothingEnabled = true; g2.imageSmoothingQuality = 'high';
      g2.drawImage(im, sx, sy, sw, sh, 0, 0, t2.width, t2.height);
      tmp = t2; tsx = 0; tsy = 0; tsw = t2.width; tsh = t2.height;
    }
    g.drawImage(tmp, tsx, tsy, tsw, tsh, 0, 0, cols, rows);
    const data = g.getImageData(0, 0, cols, rows).data;
    const entry = { canvas: c, data, cols, rows };
    F._small[k] = entry; return entry;
  };
  // quantize a color toward a flat palette: posterize levels + saturation shift (flat look)
  F.quant = (r, g, b, levels, sat = 1, lift = 0) => {
    if (levels > 0) { const q = 255 / levels; r = Math.round(r / q) * q; g = Math.round(g / q) * q; b = Math.round(b / q) * q; }
    if (sat !== 1 || lift !== 0) { const l = 0.299 * r + 0.587 * g + 0.114 * b; r = l + (r - l) * sat + lift; g = l + (g - l) * sat + lift; b = l + (b - l) * sat + lift; }
    return [F.clamp(r, 0, 255), F.clamp(g, 0, 255), F.clamp(b, 0, 255)];
  };
  /* Draw image as a mosaic of blocks.
     o: {x,y,w,h, block (px), gutter (px), zoom, fx, fy, alpha, levels (posterize, 0=off), sat, lift,
         reveal (0..1 fraction of blocks shown), order ('scan'|'random'|'center'|'edges'|'left'|'top'|'bottom'), pop (0..1 scale-in of newest blocks),
         radius (corner radius px), jitter (0..1 random alpha variation), fill ('rect'|'circle') } */
  F.mosaic = (ctx, im, o) => {
    const { x = 0, y = 0, w = F.W, h = F.H, block = 48, gutter = 0, zoom = 1, fx = 0.5, fy = 0.5, alpha = 1, levels = 0, sat = 1, lift = 0, reveal = 1, order = 'scan', pop = 0, radius = 0, jitter = 0, fill = 'rect', seed = 1 } = o;
    if (alpha <= 0) return;
    const cols = Math.max(1, Math.round(w / block)), rows = Math.max(1, Math.round(h / block));
    const bw = w / cols, bh = h / rows;
    const e = F.blockCanvas(im, cols, rows, x, y, w, h, zoom, fx, fy);
    ctx.save(); ctx.globalAlpha *= alpha;
    // fast path: no gutter, no quantize, full reveal → draw scaled canvas
    if (gutter === 0 && levels === 0 && sat === 1 && lift === 0 && reveal >= 1 && pop === 0 && radius === 0 && jitter === 0 && fill === 'rect') {
      ctx.imageSmoothingEnabled = false; ctx.drawImage(e.canvas, 0, 0, cols, rows, x, y, w, h); ctx.imageSmoothingEnabled = true; ctx.restore(); return;
    }
    const n = cols * rows;
    for (let j = 0; j < rows; j++) for (let i = 0; i < cols; i++) {
      let rank;
      switch (order) {
        case 'random': rank = F.hash(i + 1, j + 1, seed); break;
        case 'center': { const dx = (i + .5) / cols - .5, dy = ((j + .5) / rows - .5) * (rows / cols) * (h / w) * (cols / rows); rank = Math.sqrt(dx * dx + dy * dy) / 0.72 + F.hash(i, j, seed) * 0.08; break; }
        case 'edges': { const dx = (i + .5) / cols - .5, dy = (j + .5) / rows - .5; rank = 1 - Math.sqrt(dx * dx + dy * dy) / 0.72 + F.hash(i, j, seed) * 0.08; break; }
        case 'left': rank = i / cols + F.hash(i, j, seed) * (1.5 / cols); break;
        case 'right': rank = 1 - i / cols + F.hash(i, j, seed) * (1.5 / cols); break;
        case 'top': rank = j / rows + F.hash(i, j, seed) * (1.5 / rows); break;
        case 'bottom': rank = 1 - j / rows + F.hash(i, j, seed) * (1.5 / rows); break;
        case 'diag': rank = (i / cols + j / rows) / 2 + F.hash(i, j, seed) * 0.03; break;
        default: rank = (j * cols + i) / n;
      }
      if (rank > reveal) continue;
      const k = (j * cols + i) * 4;
      let c = [e.data[k], e.data[k + 1], e.data[k + 2]];
      if (levels || sat !== 1 || lift) c = F.quant(c[0], c[1], c[2], levels, sat, lift);
      let a = 1; if (jitter) a = 1 - jitter * F.hash(i, j, seed + 7);
      let s = 1; if (pop > 0) { const age = (reveal - rank) / Math.max(1e-6, pop); s = F.ease.outCubic(F.clamp(age)); }
      const px = x + i * bw, py = y + j * bh;
      const gw = bw - gutter, gh = bh - gutter;
      const dw = gw * s, dh = gh * s;
      const ox = px + gutter / 2 + (gw - dw) / 2, oy = py + gutter / 2 + (gh - dh) / 2;
      ctx.fillStyle = F.rgb(c, a);
      if (fill === 'circle') { ctx.beginPath(); ctx.arc(ox + dw / 2, oy + dh / 2, Math.min(dw, dh) / 2, 0, Math.PI * 2); ctx.fill(); }
      else if (radius > 0) { ctx.beginPath(); ctx.roundRect(ox, oy, dw, dh, Math.min(radius, dw / 2, dh / 2)); ctx.fill(); }
      else ctx.fillRect(ox - 0.25, oy - 0.25, dw + 0.5, dh + 0.5);
    }
    ctx.restore();
  };

  /* Quadtree mosaic. Blocks subdivide first where detail is highest.
     level: 0..1 → overall subdivision budget. depthMax: finest depth (base grid 16x9 at depth 0).
     Precomputes per-depth block canvases (cheap). */
  F._qt = {};
  F.quadtree = (ctx, im, o) => {
    const { x = 0, y = 0, w = F.W, h = F.H, level = 0.5, depthMax = 5, gutter = 0, zoom = 1, fx = 0.5, fy = 0.5, alpha = 1, levels = 0, sat = 1, lift = 0, baseCols = 16, baseRows = 9, bias = 1.0, seed = 3, radius = 0 } = o;
    if (alpha <= 0) return;
    const key = [im.src, x | 0, y | 0, w | 0, h | 0, zoom.toFixed(3), fx, fy, depthMax, baseCols, baseRows].join('|');
    let q = F._qt[key];
    if (!q) {
      q = { lv: [] };
      for (let d = 0; d <= depthMax; d++) q.lv.push(F.blockCanvas(im, baseCols << d, baseRows << d, x, y, w, h, zoom, fx, fy));
      // detail per node at depth d = color variance among its 4 children at depth d+1 (and recursively children's detail), normalized
      q.detail = [];
      for (let d = 0; d < depthMax; d++) {
        const a = q.lv[d], b = q.lv[d + 1]; const det = new Float32Array(a.cols * a.rows); let mx = 1e-6;
        for (let j = 0; j < a.rows; j++) for (let i = 0; i < a.cols; i++) {
          let v = 0; const k = (j * a.cols + i) * 4; const cr = a.data[k], cg = a.data[k + 1], cb = a.data[k + 2];
          for (let dj = 0; dj < 2; dj++) for (let di = 0; di < 2; di++) { const kk = ((j * 2 + dj) * b.cols + (i * 2 + di)) * 4; v += Math.abs(b.data[kk] - cr) + Math.abs(b.data[kk + 1] - cg) + Math.abs(b.data[kk + 2] - cb); }
          det[j * a.cols + i] = v; if (v > mx) mx = v;
        }
        // propagate max child detail upward later; store normalized
        for (let k = 0; k < det.length; k++) det[k] = det[k] / mx;
        q.detail.push(det);
      }
      // make detail monotone: parent detail = max(own, children) so subdivision reaches fine detail
      for (let d = depthMax - 2; d >= 0; d--) {
        const a = q.lv[d], det = q.detail[d], cd = q.detail[d + 1], b = q.lv[d + 1];
        for (let j = 0; j < a.rows; j++) for (let i = 0; i < a.cols; i++) { let m = det[j * a.cols + i]; for (let dj = 0; dj < 2; dj++) for (let di = 0; di < 2; di++) m = Math.max(m, cd[(j * 2 + dj) * b.cols + (i * 2 + di)] * 0.92); det[j * a.cols + i] = m; }
      }
      F._qt[key] = q;
    }
    ctx.save(); ctx.globalAlpha *= alpha;
    const bw0 = w / baseCols, bh0 = h / baseRows;
    const draw = (d, i, j) => {
      const lv = q.lv[d]; const k = (j * lv.cols + i) * 4;
      // decide subdivide: threshold rises with depth; detail must exceed (1-level) scaled by depth
      if (d < depthMax) {
        const det = Math.pow(q.detail[d][j * lv.cols + i], 0.6);
        // budget needed to open this node: deeper costs more; detailed nodes cost less (bias controls contrast)
        const need = ((d + 1) / (depthMax + 1)) * (1 - bias * 0.62 * det) + (det < 0.06 ? 0.25 * (d + 1) / (depthMax + 1) : 0);
        const jit = (F.hash(i, j, seed + d) - 0.5) * 0.03;
        if (level + jit >= need) { for (let dj = 0; dj < 2; dj++) for (let di = 0; di < 2; di++) draw(d + 1, i * 2 + di, j * 2 + dj); return; }
      }
      let c = [lv.data[k], lv.data[k + 1], lv.data[k + 2]];
      if (levels || sat !== 1 || lift) c = F.quant(c[0], c[1], c[2], levels, sat, lift);
      const bw = bw0 / (1 << d), bh = bh0 / (1 << d);
      const g = Math.min(gutter, bw * 0.3);
      ctx.fillStyle = F.rgb(c, 1);
      const px = x + i * bw + g / 2, py = y + j * bh + g / 2;
      if (radius > 0 && g > 0) { ctx.beginPath(); ctx.roundRect(px, py, bw - g, bh - g, Math.min(radius, (bw - g) / 2)); ctx.fill(); }
      else ctx.fillRect(px - (g ? 0 : 0.25), py - (g ? 0 : 0.25), bw - g + (g ? 0 : 0.5), bh - g + (g ? 0 : 0.5));
    };
    for (let j = 0; j < baseRows; j++) for (let i = 0; i < baseCols; i++) draw(0, i, j);
    ctx.restore();
  };

  // ---------- shapes ----------
  F.line = (ctx, x1, y1, x2, y2, color, width = 1, alpha = 1) => { if (alpha <= 0) return; ctx.save(); ctx.globalAlpha *= alpha; ctx.strokeStyle = color; ctx.lineWidth = width; ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke(); ctx.restore(); };
  F.rect = (ctx, x, y, w, h, color, alpha = 1) => { if (alpha <= 0) return; ctx.save(); ctx.globalAlpha *= alpha; ctx.fillStyle = color; ctx.fillRect(x, y, w, h); ctx.restore(); };
  F.circle = (ctx, x, y, r, color, alpha = 1, stroke = 0) => { if (alpha <= 0 || r <= 0) return; ctx.save(); ctx.globalAlpha *= alpha; ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); if (stroke) { ctx.strokeStyle = color; ctx.lineWidth = stroke; ctx.stroke(); } else { ctx.fillStyle = color; ctx.fill(); } ctx.restore(); };
  F.vignette = (ctx, strength = 0.5, color = '#000') => { if (strength <= 0) return; ctx.save(); const g = ctx.createRadialGradient(F.W / 2, F.H / 2, F.H * 0.35, F.W / 2, F.H / 2, F.H * 0.95); g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, F.withA(color, strength)); ctx.fillStyle = g; ctx.fillRect(0, 0, F.W, F.H); ctx.restore(); };
  F.grain = (ctx, amount = 0.04, t = 0, cell = 3) => { /* cheap film grain: sparse random dots */ if (amount <= 0) return; ctx.save(); ctx.globalAlpha = amount; const n = 1800; const s = Math.floor(t * 30); for (let i = 0; i < n; i++) { const xx = F.hash(i, s, 1) * F.W, yy = F.hash(i, s, 2) * F.H; ctx.fillStyle = F.hash(i, s, 3) > 0.5 ? '#fff' : '#000'; ctx.fillRect(xx, yy, cell, cell); } ctx.restore(); };

  window.F = F;
})();
