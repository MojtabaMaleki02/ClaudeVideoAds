// Official marks (simple-icons, CC0 paths) as app-icon tiles in each brand's own colours. Transparent PNG, 512 px.
import fs from 'fs'; import path from 'path'; import os from 'os'
import { createRequire } from 'module'
const require = createRequire(path.join(os.homedir(), 'shorten/shortn-fe/package.json'))
const { chromium } = require('playwright-core')
const D = path.dirname(new URL(import.meta.url).pathname)
const d = (n) => fs.readFileSync(path.join(D, n + '.svg'), 'utf8').match(/ d="([^"]+)"/)[1]
const tile = (bg, inner) => `<div class="t" style="background:${bg}">${inner}</div>`
const svg = (p, fill, extra = '') => `<svg viewBox="0 0 24 24" style="${extra}"><path d="${p}" fill="${fill}"/></svg>`
const T = {
  youtube: tile('#ffffff', `<div style="position:absolute;left:42%;top:40%;width:20%;height:22%;background:#fff"></div>` + svg(d('youtube'), '#FF0000')),
  youtubeshorts: tile('#ffffff', svg(d('youtubeshorts'), '#FF0000')),
  tiktok: tile('#000000', svg(d('tiktok'), '#25F4EE', 'transform:translate(-2.6%,-2.2%)') + svg(d('tiktok'), '#FE2C55', 'transform:translate(2.6%,2.2%)') + svg(d('tiktok'), '#ffffff')),
  instagram: tile('radial-gradient(circle at 30% 107%, #fdf497 0%, #fdf497 5%, #fd5949 45%, #d6249f 60%, #285AEB 90%)', svg(d('instagram'), '#ffffff')),
}
const b = await chromium.launch({ channel: 'chrome' })
for (const [n, html] of Object.entries(T)) {
  const p = await b.newPage({ viewport: { width: 512, height: 512 } })
  await p.setContent(`<style>html,body{margin:0;background:transparent}.t{position:relative;width:512px;height:512px;border-radius:115px;overflow:hidden}
  .t svg{position:absolute;left:18%;top:18%;width:64%;height:64%}</style>${html}`)
  await p.screenshot({ path: path.join(D, `${n}.png`), omitBackground: true }); await p.close(); console.log(n)
}
await b.close()
