// Clipzing's REAL caption engine (tscaps runtime + the 38 templates in public/caption-engine), rendered word by word
// for an ad's own voice-over, on a transparent canvas. The ad shows the product's captions, not imitations.
// URL: harness.html?e=captions&w=1080&h=1920#<job.json url>
//   job.json: { "template": "pepper", "words": [{"text","start","end"}...], "duration": 4.2,
//               "config": { typography, position, controls } (optional overrides), "fps": 60 }
import { useLayoutEffect, useRef, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { flushSync } from 'react-dom'
import { CaptionRenderer, type SubtitleFrame } from '@/lib/captions/tscaps/vendor/runtime'
import type { CaptionManifest, CaptionStyleConfig } from '@/lib/captions/tscaps/vendor/types'

const q = new URLSearchParams(location.search)
const W = Number(q.get('w') || 1080), H = Number(q.get('h') || 1920)
let FRAMES: (SubtitleFrame | null)[] = []
let FPS = 60

function Canvas({ t }: { t: number }) {
  const ref = useRef<HTMLCanvasElement>(null)
  useLayoutEffect(() => {
    const c = ref.current; if (!c) return
    const ctx = c.getContext('2d')!; ctx.clearRect(0, 0, W, H)
    FRAMES[Math.min(FRAMES.length - 1, Math.max(0, Math.round(t * FPS)))]?.draw(ctx, 0, 0, W, H)
  })
  return <canvas ref={ref} width={W} height={H} style={{ width: W, height: H }} />
}
function App() {
  const [s, setS] = useState({ t: 0, n: 0 })
  ;(window as unknown as { __setT: (x: number) => void }).__setT = (x: number) => flushSync(() => setS((p) => ({ t: x, n: p.n + 1 })))
  return <Canvas key={s.n === 0 ? 'boot' : 'live'} t={s.t} />
}
async function prepare() {
  const job = await (await fetch(decodeURIComponent(location.hash.slice(1)))).json()
  FPS = job.fps || 60
  const manifest = (await (await fetch('/caption-engine/templates.json')).json()) as CaptionManifest
  const config = { template: job.template, ...(job.config || {}) } as CaptionStyleConfig
  const r = await CaptionRenderer.create({ manifest, config, words: job.words, width: W, height: H, durationSeconds: job.duration + 0.2, assetBase: '/caption-engine' })
  const n = Math.ceil(job.duration * FPS) + 1
  const ts = Array.from({ length: n }, (_, k) => k / FPS)
  for (let j = 0; j < ts.length; j += 6) FRAMES.push(...((await r.getFrames(ts.slice(j, j + 6))) as (SubtitleFrame | null)[]))
  ;(window as unknown as { __N: number }).__N = n
}
createRoot(document.getElementById('root')!).render(<App />)
prepare().then(
  () => { (window as unknown as { __READY: boolean }).__READY = true },
  (e) => { console.error('captions failed', e); FRAMES = []; (window as unknown as { __READY: boolean }).__READY = true },
)
