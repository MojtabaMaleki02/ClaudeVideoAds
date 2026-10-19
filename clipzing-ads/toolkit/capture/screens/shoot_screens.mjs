// Real Clipzing screens with fictional data: sign a TEST user into a local production build (pointed at
// mockapi.mjs) and screenshot dashboard routes at 2× (desktop) and 3× (mobile).
//
//   node shoot_screens.mjs --app http://127.0.0.1:3111 --env <shortn-fe worktree>/.env.local --out <dir> [--only dashboard,calendar]
//
// Needs the Clerk DEVELOPMENT instance keys in that .env.local (never the production keys). The test user is
// maya+clerk_test@example.com in the dev instance; it is created once and reused. Keys are read, never printed.
import fs from 'fs'
import os from 'os'
import path from 'path'
import { createRequire } from 'module'

const arg = (k, d) => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : d }
const APP = arg('--app', 'http://127.0.0.1:3111')
const OUT = arg('--out', 'screens')
const ONLY = arg('--only', '')
const FE = process.env.CLIPZING_FE || path.join(os.homedir(), 'shorten', 'shortn-fe')
const ENV = Object.fromEntries(fs.readFileSync(arg('--env', path.join(FE, '.env.local')), 'utf8').split('\n')
  .map((l) => l.match(/^\s*([A-Z0-9_]+)\s*=\s*"?([^"\n]*)"?/)).filter(Boolean).map((m) => [m[1], m[2]]))
const SK = ENV.CLERK_SECRET_KEY
if (!SK || !SK.startsWith('sk_test_')) { console.error('Need a Clerk DEVELOPMENT secret key (sk_test_…) in the env file.'); process.exit(2) }
const require = createRequire(path.join(FE, 'package.json'))
const { chromium } = require('playwright-core')

const clerk = async (method, p, body) => {
  const r = await fetch(`https://api.clerk.com/v1${p}`, { method, headers: { Authorization: `Bearer ${SK}`, 'Content-Type': 'application/json' }, body: body ? JSON.stringify(body) : undefined })
  if (!r.ok) throw new Error(`clerk ${method} ${p}: ${r.status} ${await r.text()}`)
  return r.json()
}
const EMAIL = 'maya+clerk_test@example.com'
let [user] = await clerk('GET', `/users?email_address=${encodeURIComponent(EMAIL)}`)
if (!user) user = await clerk('POST', '/users', { email_address: [EMAIL], first_name: 'Maya', skip_password_requirement: true })
const { token: testing } = await clerk('POST', '/testing_tokens')

const SCREENS = [
  ['dashboard', '/dashboard'], ['videos', '/dashboard/jobs'], ['job', '/dashboard/jobs/7b1e2c4a-0000-4000-8000-000000000112'],
  ['calendar', '/dashboard/calendar'], ['autopilot', '/dashboard/autopilot'], ['accounts', '/dashboard/social'],
  ['brand-kit', '/dashboard/brand-kit'], ['preferences', '/dashboard/defaults'], ['achievements', '/dashboard/achievements'],
  ['billing', '/dashboard/billing'], ['editor', '/editor/c1a00000-0000-4000-8000-000000000000'],
].filter(([n]) => !ONLY || ONLY.split(',').includes(n))

const browser = await chromium.launch({ channel: 'chrome' })
for (const [label, vp, dpr] of [['desktop', { width: 1440, height: 900 }, 2], ['mobile', { width: 390, height: 844 }, 3]]) {
  const ctx = await browser.newContext({ viewport: vp, deviceScaleFactor: dpr, colorScheme: 'dark', reducedMotion: 'reduce' })
  // Clerk bot protection: the testing token on every Frontend API call (what @clerk/testing does)
  await ctx.route(/clerk\.accounts\.dev\/v1\//, async (route) => {
    const u = new URL(route.request().url()); u.searchParams.set('__clerk_testing_token', testing)
    const resp = await route.fetch({ url: u.toString() })
    let body = await resp.text()
    try { const j = JSON.parse(body); if (j.response) j.response.captcha_bypass = true; if (j.client) j.client.captcha_bypass = true; body = JSON.stringify(j) } catch {}
    await route.fulfill({ response: resp, body })
  })
  // the product's caption preview uses a stock photo of a real person: show Zing's podcast instead
  const MEDIA = path.join(path.dirname(new URL(import.meta.url).pathname), 'media')
  await ctx.route(/\/preview-bg\.mp4(\?|$)/, (r) => r.fulfill({ path: path.join(MEDIA, 'clips', 'closeup.mp4'), contentType: 'video/mp4' }))
  await ctx.route(/\/caption-preview-backdrop\.jpg(\?|$)/, (r) => r.fulfill({ path: path.join(MEDIA, 'thumbs', '00.jpg'), contentType: 'image/jpeg' }))
  await ctx.addInitScript(() => { try { localStorage.setItem('v2_editor_onboarding_seen', '1') } catch {} })
  const { token: ticket } = await clerk('POST', '/sign_in_tokens', { user_id: user.id, expires_in_seconds: 900 })   // single-use: one per context
  const page = await ctx.newPage()
  page.on('console', (m) => { if (m.type() === 'error' && process.env.DEBUG) console.error(label, 'console:', m.text().slice(0, 300)) })
  page.on('pageerror', (e) => console.error(label, 'page error:', e.message.slice(0, 160)))
  await page.goto(`${APP}/login?__clerk_ticket=${ticket}`, { waitUntil: 'domcontentloaded', timeout: 60000 }).catch((e) => console.error('login nav:', e.message.split('\n')[0]))
  const ok = await page.waitForURL(/\/dashboard/, { timeout: 60000 }).then(() => true, () => false)
  if (!ok) { await page.screenshot({ path: path.join(OUT, `login-${label}.png`) }); console.error(label, 'not signed in; see', path.join(OUT, `login-${label}.png`), page.url()) }
  const dir = path.join(OUT, label); fs.mkdirSync(dir, { recursive: true })
  for (const [name, route] of SCREENS) {
    await page.goto(APP + route, { waitUntil: 'networkidle' }).catch(() => {})
    await page.waitForTimeout(1800)
    // hide dev-only chrome and toasts so the frame is clean
    await page.addStyleTag({ content: '[data-sonner-toaster],nextjs-portal,#__next-build-watcher{display:none!important}' }).catch(() => {})
    await page.screenshot({ path: path.join(dir, `${name}.png`) })
    console.log(label, name)
  }
  await ctx.close()
}
await browser.close()
