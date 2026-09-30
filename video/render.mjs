// Renders scene.html frame-by-frame with headless Chromium and pipes the
// frames into ffmpeg.  Usage:
//   node render.mjs stills 0.5 4 7.5 ...   → out/still-<t>.png   (storyboard)
//   node render.mjs video [fps]            → out/picture.mp4     (silent picture)
import { chromium } from 'playwright-core';
import { spawn, execSync } from 'node:child_process';
import { mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const here = path.dirname(fileURLToPath(import.meta.url));
const out = path.join(here, 'out');
mkdirSync(out, { recursive: true });
const FFMPEG = process.env.FFMPEG ||
  execSync(`python3 -c "import imageio_ffmpeg as f; print(f.get_ffmpeg_exe())"`).toString().trim();
const CHROME = process.env.CHROME || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';

const [mode = 'video', ...rest] = process.argv.slice(2);
const browser = await chromium.launch({ executablePath: CHROME, args: ['--force-color-profile=srgb', '--font-render-hinting=none'] });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
await page.goto('file://' + path.join(here, 'scene.html'));
await page.evaluate(() => window.ready);
const duration = await page.evaluate(() => window.DURATION);

const shot = async t => {
  await page.evaluate(t => window.render(t), t);
  return page.screenshot({ type: 'png', animations: 'disabled' });
};

if (mode === 'stills') {
  const { writeFileSync } = await import('node:fs');
  for (const t of rest.map(Number)) writeFileSync(path.join(out, `still-${t.toFixed(2)}.png`), await shot(t));
} else {
  const fps = Number(rest[0] || 60);
  const frames = Math.round(duration * fps);
  const ff = spawn(FFMPEG, ['-y', '-f', 'image2pipe', '-framerate', String(fps), '-i', '-',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '14', '-pix_fmt', 'yuv420p',
    '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709',
    path.join(out, 'picture.mp4')], { stdio: ['pipe', 'ignore', 'inherit'] });
  for (let i = 0; i < frames; i++) {
    const buf = await shot(i / fps);
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % fps === 0) process.stdout.write(`\r${(i / fps).toFixed(0)}s / ${duration}s`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  console.log('\npicture done');
}
await browser.close();
