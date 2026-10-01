window.drawFilm = function (ctx, t) {
  const im = F.images.earth;
  ctx.fillStyle = '#0a0a0c'; ctx.fillRect(0, 0, F.W, F.H);
  const lv = t / 5; // 0..1 over 5 s
  const g = F.lerp(3, 0, F.p(lv, 0.7, 1.0));
  F.quadtree(ctx, im, { level: lv, depthMax: 5, gutter: g, levels: lv < 0.5 ? 6 : 0, sat: 1 });
  if (lv > 0.9) F.drawCover(ctx, im, 0, 0, F.W, F.H, 1, 0.5, 0.5, F.p(lv, 0.9, 1));
  F.text(ctx, 'level ' + lv.toFixed(2), { x: 40, y: 60, size: 24, fam: 'sans', color: '#888' });
};
