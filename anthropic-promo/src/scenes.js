/* 《从一个像素开始》 From One Pixel — Claude Fable 5.1 concept promo.
   Every frame is a pure function of t (seconds). Grid: 75 BPM, bar 3.2 s, beat 0.8, 8th 0.4, 16th 0.2.
   Spec: docs/storyboard.md */
(function () {
  const INK = '#0B0B0E', PAPER = '#F3EFE7', EMBER = '#E8613A';
  const X0 = 160, XR = 1260;            // copy safe area
  const FR = 1 / 30;                    // one frame
  const ORIGIN = { x: 960, y: 360, s: 120, cx: 1020, cy: 420, col: 8, row: 3 }; // column 9 / row 4 (1-indexed)
  const img = k => F.images[k];

  // ---------- stages ----------
  function stage(ctx, key, alpha = 1) {
    const im = img(key); if (!im) { ctx.fillStyle = '#f0f'; ctx.fillRect(0, 0, 60, 60); return; }
    ctx.save(); ctx.globalAlpha *= alpha; ctx.imageSmoothingEnabled = im.width >= F.W; ctx.imageSmoothingQuality = 'high';
    ctx.drawImage(im, 0, 0, F.W, F.H); ctx.restore();
  }
  // push-in by factor z about screen point (px,py); photograph only
  function zoomStage(ctx, key, z, px = 960, py = 540) {
    const im = img(key); if (!im) return;
    ctx.save(); ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = 'high';
    ctx.drawImage(im, px - px * z, py - py * z, F.W * z, F.H * z); ctx.restore();
  }
  function cell120(ctx, key, c, r) { const im = img(key); ctx.imageSmoothingEnabled = false; ctx.drawImage(im, c, r, 1, 1, c * 120, r * 120, 120, 120); }
  function origin2x2(ctx, key) { const im = img(key); ctx.save(); ctx.imageSmoothingEnabled = false; ctx.drawImage(im, ORIGIN.col * 2, ORIGIN.row * 2, 2, 2, ORIGIN.x, ORIGIN.y, 120, 120); ctx.restore(); }

  // ---------- type ----------
  const enterA = (t, tIn) => F.ease.outExpo(F.clamp((t - tIn) / 0.3));
  const enterDy = (t, tIn) => 16 * (1 - F.ease.outExpo(F.clamp((t - tIn) / 0.42)));
  const exitA = (t, tOut, frames = 4) => { const f0 = tOut - frames * FR; if (t >= tOut) return 0; if (t < f0) return 1; return 1 - (t - f0) / (frames * FR); };
  function line(ctx, str, o, t, tIn, tOut) {
    if (t < tIn || t >= tOut) return;
    const a = enterA(t, tIn) * exitA(t, tOut); const dy = enterDy(t, tIn);
    F.text(ctx, str, Object.assign({}, o, { y: o.y + dy, alpha: (o.alpha == null ? 1 : o.alpha) * a }));
  }
  const H = (ctx, str, t, tIn, tOut, ink = false, y = 880) => line(ctx, str, { x: X0, y, size: 72, weight: 600, fam: 'zhserif', color: ink ? INK : PAPER, tracking: 0.08 }, t, tIn, tOut);
  const E = (ctx, str, t, tIn, tOut, ink = false) => line(ctx, str, { x: X0, y: 932, size: 32, weight: 400, fam: 'serif', italic: true, color: ink ? INK : PAPER, tracking: 0.01, alpha: 0.72 }, t, tIn, tOut);
  const B = (ctx, str, t, tIn, tOut, ink = false, y = 800) => line(ctx, str, { x: X0, y, size: 18, weight: 500, fam: 'grotesk', color: ink ? INK : PAPER, tracking: 0.22, alpha: 0.5 }, t, tIn, tOut);

  // ---------- devices ----------
  // THE CEILING RULE: 1-px paper hairline at 50 %, labelled 「上限」; lifts one row per act-one downbeat, exits 28.8–30.4
  function ceiling(ctx, t) {
    if (t < 6.4) return;
    let y;
    if (t < 12.8) y = 600;
    else if (t < 19.2) y = 600 - 150 * Math.min(t - 12.8, 0.8);
    else if (t < 22.4) y = 480 - 150 * Math.min(t - 19.2, 0.8);
    else if (t < 28.8) y = 360 - 150 * Math.min(t - 22.4, 0.8);
    else y = 240 - 150 * (t - 28.8);
    y = Math.round(y);
    if (y < -40) return;
    const w = t < 7.2 ? (XR - X0) * (t - 6.4) / 0.8 : (XR - X0);
    if (y >= 0) F.rect(ctx, X0, y, w, 1, PAPER, 0.5);
    if (t >= 7.2 && y + 18 > 0) F.text(ctx, '上限', { x: XR, y: y + 18, size: 14, weight: 400, fam: 'zh', color: PAPER, tracking: 0.2, alpha: 0.5, align: 'right' });
  }
  // THE DIAL (S02): 1-px arc r 200 around the origin, 7 o'clock → over the top → 5 o'clock, 300° in 5.6 s
  function dial(ctx, t) {
    if (t < 6.4 || t >= 12.8) return;
    const a = exitA(t, 12.8);
    const prog = F.clamp((t - 6.4) / 5.6);
    ctx.save(); ctx.globalAlpha = 0.55 * a; ctx.strokeStyle = PAPER; ctx.lineWidth = 1; ctx.beginPath();
    const s = Math.PI * 2 / 3; ctx.arc(ORIGIN.cx, ORIGIN.cy, 200, s, s + prog * Math.PI * 5 / 3, false); ctx.stroke(); ctx.restore();
    F.text(ctx, 'LOW', { x: 878, y: 575, size: 14, weight: 500, fam: 'grotesk', color: PAPER, tracking: 0.2, alpha: 0.55 * a, align: 'right' });
    if (t >= 12.0) F.text(ctx, 'MAX', { x: 1162, y: 575, size: 14, weight: 500, fam: 'grotesk', color: PAPER, tracking: 0.2, alpha: 0.55 * a, align: 'left' });
  }
  // THE FLOOD (S03): 120-px field grows from the origin by Chebyshev rings, one per 8th
  function flood(ctx, t) {
    const d = Math.floor((t - 12.8) / 0.4) + 1;
    ctx.save();
    for (let r = 0; r < 9; r++) for (let c = 0; c < 16; c++) {
      const ring = Math.max(Math.abs(c - ORIGIN.col), Math.abs(r - ORIGIN.row));
      if (ring === 0 || ring > d) continue;
      cell120(ctx, 'face_120_tok_b55', c, r);
    }
    ctx.restore();
    origin2x2(ctx, 'face_60_tok2_b55');
  }
  // THE NUMERAL (S04): tabular digits, Instrument Serif 200 px
  function numeral(ctx, t) {
    if (t < 19.2 || t >= 22.4) return;
    const vals = ['0', '1,000', '10,000', '100,000', '1,000,000'];
    const s = vals[Math.min(4, Math.floor((t - 19.2) / 0.2))];
    const o = { size: 200, weight: 400, fam: 'serif' };
    ctx.save(); ctx.globalAlpha = 0.92 * exitA(t, 22.4); ctx.font = F.font(o.size, o.weight, o.fam); ctx.fillStyle = PAPER; ctx.textBaseline = 'alphabetic'; ctx.textAlign = 'left';
    const adv = ctx.measureText('0').width * 1.04, cw = ctx.measureText(',').width;
    let x = X0;
    for (const ch of s) { if (ch === ',') { ctx.fillText(ch, x, 560); x += cw + 6; } else { const w = ctx.measureText(ch).width; ctx.fillText(ch, x + (adv - w) / 2, 560); x += adv; } }
    ctx.restore();
  }
  // THE AGENT LINE (S05): one line, forks into four lanes, merges, finishes
  function agentLine(ctx, t) {
    if (t < 22.4 || t >= 28.8) return;
    const x = Math.min(1760, 160 + (1600 / 6.0) * (t - 22.4)); const a = 0.7, Y = 712, lanes = [676, 700, 724, 748];
    F.rect(ctx, 160, Y, Math.min(x, 587) - 160, 1, PAPER, a);
    if (x > 587) { F.rect(ctx, 587, 676, 1, 73, PAPER, a); const x2 = Math.min(x, 1440); for (const y of lanes) F.rect(ctx, 587, y, x2 - 587, 1, PAPER, a); }
    if (x > 1440) { F.rect(ctx, 1440, 676, 1, 73, PAPER, a); F.rect(ctx, 1440, Y, x - 1440, 1, PAPER, a); }
  }
  // MOSAIC-TEXT (S06): the headline rastered and block-sampled at 30 / 15 / 5 / 1 px
  const mt = {};
  function downscale(src, w, h) {
    let cur = src;
    while (cur.width / 2 >= w && cur.height / 2 >= h) { const c = document.createElement('canvas'); c.width = Math.round(cur.width / 2); c.height = Math.round(cur.height / 2); const g = c.getContext('2d'); g.imageSmoothingEnabled = true; g.imageSmoothingQuality = 'high'; g.drawImage(cur, 0, 0, c.width, c.height); cur = c; }
    const c = document.createElement('canvas'); c.width = w; c.height = h; const g = c.getContext('2d'); g.imageSmoothingEnabled = true; g.imageSmoothingQuality = 'high'; g.drawImage(cur, 0, 0, w, h); return c;
  }
  function mosaicText(ctx, str, b, alpha) {
    if (alpha <= 0) return;
    if (!mt.src) { const c = document.createElement('canvas'); c.width = F.W; c.height = F.H; const g = c.getContext('2d'); F.text(g, str, { x: X0, y: 880, size: 72, weight: 600, fam: 'zhserif', color: INK, tracking: 0.08 }); mt.src = c; }
    ctx.save(); ctx.globalAlpha *= alpha;
    if (b === 1) { ctx.drawImage(mt.src, 0, 0); ctx.restore(); return; }
    if (!mt[b]) mt[b] = downscale(mt.src, F.W / b, F.H / b);
    ctx.imageSmoothingEnabled = false; ctx.drawImage(mt[b], 0, 0, F.W, F.H); ctx.restore();
  }
  // THE BOUNDARY (S10–S11): 1-px paper rectangle inset 96, drawn clockwise from the top-left over one bar
  function boundary(ctx, t) {
    if (t < 51.2 || t >= 57.6) return;
    const x0 = 96, y0 = 96, x1 = 1824, y1 = 984, w = x1 - x0, h = y1 - y0, a = 0.7;
    const L = F.clamp((t - 51.2) / 3.2) * 2 * (w + h);
    const seg = (len, from, to) => F.clamp(L - from, 0, to - from);
    F.rect(ctx, x0, y0, seg(L, 0, w), 1, PAPER, a);
    F.rect(ctx, x1, y0, 1, seg(L, w, w + h), PAPER, a);
    const b = seg(L, w + h, 2 * w + h); F.rect(ctx, x1 - b, y1, b + 1, 1, PAPER, a);
    const l = seg(L, 2 * w + h, 2 * w + 2 * h); F.rect(ctx, x0, y1 - l, 1, l + 1, PAPER, a);
  }
  // THE LOCKUP (S13)
  function lockup(ctx, t) {
    if (t < 70.4) return;
    const fade = t < 74.4 ? 1 : 1 - F.clamp((t - 74.4) / 0.3); if (fade <= 0) return;
    line(ctx, 'Claude Fable 5.1', { x: 960, y: 528, size: 64, weight: 500, fam: 'sans', color: PAPER, tracking: -0.015, align: 'center', alpha: fade }, t, 70.4, 99);
    line(ctx, '我们能力最强的模型', { x: 960, y: 592, size: 26, weight: 300, fam: 'zh', color: PAPER, tracking: 0.2, align: 'center', alpha: 0.8 * fade }, t, 71.2, 99);
    line(ctx, 'Anthropic', { x: 960, y: 648, size: 24, weight: 500, fam: 'sans', color: PAPER, tracking: 0.18, align: 'center', alpha: 0.65 * fade }, t, 72.0, 99);
  }
  const pixel = (ctx) => F.rect(ctx, ORIGIN.x, ORIGIN.y, ORIGIN.s, ORIGIN.s, EMBER, 1);

  // ---------- the film ----------
  window.drawFilm = function (ctx, t) {
    ctx.fillStyle = INK; ctx.fillRect(0, 0, F.W, F.H);
    if (t < 6.4) {                                   // S01 一个像素
      if (t >= 0.8) pixel(ctx);
      H(ctx, '一个像素。', t, 3.2, 6.4); E(ctx, 'One pixel.', t, 4.0, 6.4);
    } else if (t < 12.8) {                           // S02 先想
      origin2x2(ctx, 'face_60_tok2_b55'); dial(ctx, t);
      H(ctx, '它是什么？', t, 6.4, 12.8, false, 786);
      B(ctx, 'ADAPTIVE THINKING · EFFORT DIAL', t, 8.0, 12.8, false, 706);
      H(ctx, '先想，再答。', t, 9.6, 12.8);
      E(ctx, 'What is it? Think first. Then answer.', t, 10.4, 12.8);
    } else if (t < 19.2) {                           // S03 它开始看见
      flood(ctx, t);
      B(ctx, 'VISION · DOCUMENTS · CHARTS', t, 16.0, 19.2); H(ctx, '它开始看见。', t, 16.0, 19.2); E(ctx, 'It begins to see.', t, 16.8, 19.2);
    } else if (t < 22.4) {                           // S04 记住全部
      stage(ctx, 'face_60_tok2_b65'); numeral(ctx, t);
      B(ctx, '1M CONTEXT · 128K OUTPUT', t, 20.0, 22.4); H(ctx, '记住全部，而不只是片段。', t, 20.0, 22.4); E(ctx, 'All of it, not just the fragment.', t, 20.8, 22.4);
    } else if (t < 28.8) {                           // S05 做到完成
      stage(ctx, 'face_30_tok_b75'); agentLine(ctx, t);
      B(ctx, 'SUB-AGENTS · MANAGED AGENTS · TOOL USE · COMPUTER USE', t, 23.2, 28.8); H(ctx, '一件事，做到完成。', t, 25.6, 28.8); E(ctx, 'One task, seen through.', t, 26.4, 28.8);
    } else if (t < 32.0) {                           // S06 读遍代码 (ink type)
      stage(ctx, t < 31.2 ? 'face_15_c8_b85' : 'face_5_c32_b92');
      if (t >= 29.2) mosaicText(ctx, '读遍代码，再写。', t < 29.6 ? 30 : t < 30.0 ? 15 : t < 30.4 ? 5 : 1, exitA(t, 32.0));
      B(ctx, 'CLAUDE CODE · CODE EXECUTION · WHOLE CODEBASES', t, 30.4, 32.0, true); E(ctx, 'It reads the whole codebase before it writes.', t, 30.8, 32.0, true);
    } else if (t < 38.4) {                           // S07 原来是一张脸 (ink type)
      zoomStage(ctx, 'face_1_full_b100', 1 + 0.03 * (t - 32.0) / 6.4);
      H(ctx, '原来，是一张脸。', t, 32.8, 38.4, true); E(ctx, 'So it was a face.', t, 33.6, 38.4, true);
    } else if (t < 41.6) {                           // S08 不止一个人
      stage(ctx, t < 38.8 ? 'face_120_tok_b70' : t < 39.2 ? 'people_120_tok_b70' : t < 40.0 ? 'people_60_tok2_b80' : t < 40.8 ? 'people_30_tok_b90' : 'people_1_full_b100');
      H(ctx, '不止一个人。', t, 38.8, 40.8); E(ctx, 'Not one. Many.', t, 39.6, 40.8);
    } else if (t < 48.0) {                           // S09 是一座城
      const k = t < 42.0 ? 'people_120_tok_b70' : t < 42.4 ? 'city_120_tok_b55' : t < 42.8 ? 'city_60_tok2_b62' : t < 43.2 ? 'city_30_tok_b70' : t < 43.6 ? 'city_30_c8_b77' : t < 44.0 ? 'city_15_c8_b85' : t < 44.4 ? 'city_5_c32_b92' : t < 44.8 ? 'city_5_full_b96' : t < 46.4 ? 'city_1_full_b100' : t < 46.8 ? 'city_5_c32_b90' : t < 47.2 ? 'city_15_c8_b83' : t < 47.6 ? 'city_60_tok2_b76' : 'city_120_tok_b70';
      stage(ctx, k);
      H(ctx, '再远一些，是一座城。', t, 44.8, 46.4); E(ctx, 'Further out: a city.', t, 45.6, 46.4);
    } else if (t < 57.6) {                           // S10 再高一些 + S11 边界
      const g = t < 48.4 ? 0 : t < 51.2 ? Math.min(13, 1 + Math.floor((t - 48.4) / 0.2)) : 14;
      if (g < 14) stage(ctx, 'earth_qt_g' + String(g).padStart(2, '0')); else zoomStage(ctx, 'earth_qt_g14', 1 + 0.04 * (t - 51.2) / 6.4);
      boundary(ctx, t);
      H(ctx, '再高一些，世界清晰了。', t, 51.2, 54.4); E(ctx, 'Higher still: the world, in focus.', t, 52.0, 54.4);
      B(ctx, 'SAFEGUARDS · BY DESIGN', t, 54.4, 57.6); H(ctx, '能力越大，边界越清。', t, 54.4, 57.6); E(ctx, 'More capable. Clearer boundaries.', t, 55.2, 57.6);
    } else if (t < 70.4) {                           // S12 然后，抬头
      zoomStage(ctx, 'sky_1_full_b100', 1 + 0.06 * (t - 57.6) / 12.8, 1205, 790);
      H(ctx, '然后，抬头。', t, 60.8, 64.0); E(ctx, 'Then, look up.', t, 61.6, 64.0);
      H(ctx, '每个上限，都是起点。', t, 64.0, 70.4); E(ctx, 'Every ceiling, the next floor.', t, 64.8, 70.4);
    } else {                                         // S13 lockup → pixel → ink
      lockup(ctx, t);
      if (t >= 75.2 && t < 76.0) pixel(ctx);
    }
    ceiling(ctx, t);
  };
})();
