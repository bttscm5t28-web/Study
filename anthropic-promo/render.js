#!/usr/bin/env node
/* Deterministic frame renderer: serves the project dir over HTTP, drives Chromium via Playwright,
   pipes PNG frames into ffmpeg. Usage:
     node render.js --out output/promo.mp4 [--music music/track.wav] [--fps 30] [--from 0 --to 10] [--preview]
     node render.js --stills 0,2.5,5 --dir build/stills      (PNG stills at given times)
*/
const { chromium } = require('playwright');
const http = require('http'); const fs = require('fs'); const path = require('path'); const { spawn } = require('child_process');
const args = process.argv.slice(2); const opt = (k, d) => { const i = args.indexOf('--' + k); return i >= 0 ? (args[i + 1] && !args[i + 1].startsWith('--') ? args[i + 1] : true) : d; };
const ROOT = __dirname;
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.ttf': 'font/ttf', '.jpg': 'image/jpeg', '.png': 'image/png', '.wav': 'audio/wav', '.css': 'text/css' };
const server = http.createServer((req, res) => {
  const u = decodeURIComponent(req.url.split('?')[0]); const p = path.join(ROOT, u === '/' ? 'index.html' : u);
  if (!p.startsWith(ROOT) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': MIME[path.extname(p)] || 'application/octet-stream', 'Cache-Control': 'no-store' }); fs.createReadStream(p).pipe(res);
});
(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r)); const port = server.address().port;
  const browser = await chromium.launch({ args: ['--disable-gpu', '--font-render-hinting=none', '--disable-lcd-text', '--hide-scrollbars'] });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  page.on('pageerror', e => console.error('PAGE ERROR', e.message)); page.on('console', m => { if (m.type() === 'error') console.error('CONSOLE', m.text()); });
  await page.goto(`http://127.0.0.1:${port}/index.html`); await page.waitForFunction(() => window.READY === true, null, { timeout: 120000 });
  const fps = +opt('fps', 30); const total = await page.evaluate(() => window.totalFrames);
  const tl = JSON.parse(fs.readFileSync(path.join(ROOT, 'timeline.json'), 'utf8'));
  const stills = opt('stills', null);
  if (stills) {
    const dir = opt('dir', 'build/stills'); fs.mkdirSync(path.join(ROOT, dir), { recursive: true });
    const times = String(stills).split(',').map(Number);
    for (const t of times) { const i = Math.round(t * 30); await page.evaluate(i => window.renderFrame(i), i); const f = path.join(ROOT, dir, `t${t.toFixed(2).padStart(6, '0')}.png`); await page.screenshot({ path: f, type: 'png' }); console.log('still', f); }
    await browser.close(); server.close(); return;
  }
  const out = opt('out', 'output/promo.mp4'); const music = opt('music', tl.music || 'music/track.wav');
  const from = Math.round(+opt('from', 0) * 30); const to = Math.min(total, Math.round(+opt('to', tl.duration) * 30));
  const preview = !!opt('preview', false); const step = Math.round(30 / fps);
  fs.mkdirSync(path.dirname(path.join(ROOT, out)), { recursive: true });
  const ff = ['-y', '-f', 'image2pipe', '-framerate', String(fps), '-i', '-'];
  const hasMusic = fs.existsSync(path.join(ROOT, music));
  if (hasMusic) ff.push('-ss', (from / 30).toFixed(3), '-i', path.join(ROOT, music));
  ff.push('-c:v', 'libx264', '-preset', preview ? 'veryfast' : 'medium', '-crf', preview ? '23' : '17', '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-level', '4.1', '-movflags', '+faststart', '-r', String(fps));
  if (preview) ff.push('-vf', 'scale=960:-2');
  if (hasMusic) ff.push('-c:a', 'aac', '-b:a', '256k', '-shortest');
  ff.push(path.join(ROOT, out));
  const ffm = spawn('ffmpeg', ff, { stdio: ['pipe', 'inherit', 'inherit'] });
  const t0 = Date.now(); let n = 0;
  for (let i = from; i < to; i += step) {
    const dataUrl = await page.evaluate(i => { window.renderFrame(i); return document.getElementById('c').toDataURL('image/png'); }, i);
    const buf = Buffer.from(dataUrl.slice(dataUrl.indexOf(',') + 1), 'base64');
    if (!ffm.stdin.write(buf)) await new Promise(r => ffm.stdin.once('drain', r));
    n++; if (n % 60 === 0) { const el = (Date.now() - t0) / 1000; process.stdout.write(`\r${i}/${to} frames  ${(n / el).toFixed(1)} fps  eta ${(((to - i) / step) / (n / el)).toFixed(0)}s   `); }
  }
  ffm.stdin.end(); await new Promise(r => ffm.on('close', r)); console.log(`\ndone: ${out} (${n} frames in ${((Date.now() - t0) / 1000).toFixed(0)}s)`);
  await browser.close(); server.close();
})().catch(e => { console.error(e); process.exit(1); });
