// Shoot frames of a capture entry with a virtual clock (deterministic, transparent when asked).
//   node shoot.mjs zing  <pose|all|a,b,c> <outdir> [--frames 126] [--fps 30] [--size 900] [--t0 0.6]
//   node shoot.mjs footage <scene|all> <outdir> [--frames 150] [--fps 30] [--w 720 --h 1280]
//   node shoot.mjs brand <wordmark|wordmark-white|icon|all> <outdir>
//   node shoot.mjs captions <job.json> <outdir>  [--w 1080 --h 1920]
// Frames land in <outdir>/<name>/0000.png. Run `python3 ../library.py <outdir>` afterwards to make the library.
import fs from 'fs'
import http from 'http'
import os from 'os'
import path from 'path'
import { createRequire } from 'module'
import { fileURLToPath } from 'url'

const HERE = path.dirname(fileURLToPath(import.meta.url))
const FE = process.env.CLIPZING_FE || path.join(os.homedir(), 'shorten', 'shortn-fe')
const FONTS = path.join(HERE, '..', '..', 'assets', 'fonts')
const require = createRequire(path.join(FE, 'package.json'))
const { chromium } = require('playwright-core')

const [entry, which = 'all', outdir = 'frames', ...rest] = process.argv.slice(2)
const opt = Object.fromEntries(rest.reduce((a, x, i, arr) => (x.startsWith('--') ? [...a, [x.slice(2), arr[i + 1]]] : a), []))
const D = {
  zing: { w: 900, h: 900, frames: 126, fps: 30, t0: 0.6, transparent: true },
  footage: { w: 720, h: 1280, frames: 150, fps: 30, t0: 1.0, transparent: false },
  brand: { w: 1500, h: 520, frames: 1, fps: 30, t0: 0, transparent: true },
  captions: { w: 1080, h: 1920, frames: 0, fps: 60, t0: 0, transparent: true },
}[entry]
if (!D) { console.error('entry must be zing | footage | brand | captions'); process.exit(2) }
const W = Number(opt.size || opt.w || D.w), H = Number(opt.size || opt.h || D.h)
const FPS = Number(opt.fps || D.fps), T0 = Number(opt.t0 ?? D.t0)

// static server: the capture dir, the frontend's public/, the bundled fonts, and the job dir (captions)
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.webp': 'image/webp', '.woff2': 'font/woff2', '.ttf': 'font/ttf', '.mp4': 'video/mp4', '.jpg': 'image/jpeg' }
const JOB_DIR = entry === 'captions' ? path.dirname(path.resolve(which)) : HERE
const server = http.createServer((req, res) => {
  const u = decodeURIComponent(new URL(req.url, 'http://x').pathname)
  const cands = u.startsWith('/_fonts/') ? [path.join(FONTS, u.slice(8))] : u.startsWith('/_job/') ? [path.join(JOB_DIR, u.slice(6))] : [path.join(HERE, u), path.join(FE, 'public', u)]
  const f = cands.find((p) => fs.existsSync(p) && fs.statSync(p).isFile())
  if (!f) { res.writeHead(404); return res.end() }
  res.writeHead(200, { 'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream' }); fs.createReadStream(f).pipe(res)
}).listen(0)
const PORT = server.address().port

const browser = await chromium.launch({ channel: 'chrome' })
async function open(hash) {
  const p = await browser.newPage({ viewport: { width: W, height: H } })
  p.on('pageerror', (e) => console.error('page error:', e.message))
  if (D.transparent) {
    const cdp = await p.context().newCDPSession(p)
    await cdp.send('Emulation.setDefaultBackgroundColorOverride', { color: { r: 0, g: 0, b: 0, a: 0 } })
  }
  await p.goto(`http://127.0.0.1:${PORT}/harness.html?e=${entry}&w=${W}&h=${H}#${hash}`)
  await p.waitForFunction(() => window.__READY && window.__setT, null, { timeout: 120000 })
  return p
}
let names = which.split(',')
if (entry === 'captions') names = [path.basename(which, '.json')]
else if (which === 'all') {
  const p = await open(entry === 'brand' ? 'wordmark' : '')
  names = entry === 'brand' ? ['wordmark', 'wordmark-white', 'icon'] : await p.evaluate(() => window.__POSES)
  await p.close()
}
for (const name of names) {
  const p = await open(entry === 'captions' ? `/_job/${path.basename(which)}` : name)
  const n = entry === 'captions' ? await p.evaluate(() => window.__N) : Number(opt.frames || D.frames)
  const dir = path.join(outdir, name); fs.mkdirSync(dir, { recursive: true })
  for (let k = 0; k < Math.round(T0 * FPS); k++) await p.evaluate((t) => window.__frame(t), k / FPS)   // the rig's fade-in plays out
  const clip = entry === 'brand' ? await (await p.$('#mark')).boundingBox() : undefined
  for (let i = 0; i < n; i++) {
    await p.evaluate((t) => window.__frame(t), T0 + i / FPS)
    await p.screenshot({ path: path.join(dir, `${String(i).padStart(4, '0')}.png`), omitBackground: D.transparent, clip })
  }
  fs.writeFileSync(path.join(dir, 'meta.json'), JSON.stringify({ entry, name, fps: FPS, frames: n, loop: entry === 'zing' || entry === 'footage', size: [W, H] }))
  await p.close(); console.log(entry, name, n)
}
await browser.close(); server.close()
