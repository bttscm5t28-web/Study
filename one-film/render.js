// 用无头 Chromium 逐帧渲染 film.html，并直接编码为视频分段。
//   node render.js preview 2.5 10 33 ...   → build/preview/*.png
//   node render.js video                    → build/video.mp4（无声）
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const FPS = 60, DURATION = 66, WORKERS = 4;
const url = 'file://' + path.resolve(__dirname, 'film.html');

async function openPage(browser) {
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  await page.goto(url);
  await page.evaluate(() => window.ready);
  return page;
}

async function preview(times) {
  const browser = await chromium.launch();
  const page = await openPage(browser);
  fs.mkdirSync('build/preview', { recursive: true });
  for (const t of times) {
    await page.evaluate(t => window.render(t), t);
    await page.screenshot({ path: `build/preview/t${String(t.toFixed(2)).padStart(6, '0')}.png` });
  }
  await browser.close();
}

async function segment(browser, idx, f0, f1) {
  const page = await openPage(browser);
  const out = `build/seg${idx}.mp4`;
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'png', '-i', '-',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '12', '-pix_fmt', 'yuv420p', '-tune', 'animation', out]);
  for (let f = f0; f < f1; f++) {
    await page.evaluate(t => window.render(t), f / FPS);
    const buf = await page.screenshot({ type: 'png' });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if ((f - f0) % 300 === 0) console.log(`worker ${idx}: frame ${f}/${f1}`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  return out;
}

async function video() {
  const total = FPS * DURATION, per = Math.ceil(total / WORKERS);
  const browser = await chromium.launch();
  const segs = await Promise.all([...Array(WORKERS).keys()].map(i => segment(browser, i, i * per, Math.min(total, (i + 1) * per))));
  await browser.close();
  fs.writeFileSync('build/segs.txt', segs.map(s => `file '${path.basename(s)}'`).join('\n'));
  await new Promise(r => spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', 'build/segs.txt', '-c', 'copy', 'build/video.mp4'], { stdio: 'inherit' }).on('close', r));
  console.log('wrote build/video.mp4');
}

const [mode, ...rest] = process.argv.slice(2);
(mode === 'preview' ? preview(rest.map(Number)) : video()).catch(e => { console.error(e); process.exit(1); });
