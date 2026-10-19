// A stand-in Clipzing API with FICTIONAL data, so a local production build of the real frontend renders real
// screens for ads. Nothing here touches the real backend or real users.
//   node mockapi.mjs [--port 8787] [--media <dir with thumbs/*.jpg and clips/*.mp4>]
// Every request is logged to mockapi.log; unknown GETs return {} so you can see which shape a screen still needs.
import fs from 'fs'
import http from 'http'
import path from 'path'
import { fileURLToPath } from 'url'

const HERE = path.dirname(fileURLToPath(import.meta.url))
const arg = (k, d) => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : d }
const PORT = Number(arg('--port', 8787))
const MEDIA = arg('--media', path.join(HERE, 'media'))
const BASE = `http://127.0.0.1:${PORT}`
const LOG = fs.createWriteStream(path.join(HERE, 'mockapi.log'), { flags: 'a' })

const now = Date.now()
const iso = (msAgo) => new Date(now - msAgo).toISOString()
const H = 3600e3, DAY = 24 * H

// ── fictional world ─────────────────────────────────────────────────────────
const SHOW = 'The Long Table'
const TITLES = [
  ['Why consistency beats talent', 94], ['The 3am editing confession', 91], ['Guest roasts my mic setup', 88],
  ['Nobody tells you this about growth', 86], ['I quit my job for this podcast', 83], ['Reacting to my first episode', 79],
  ['The one question every guest dodges', 74], ['How we hit 100 episodes', 71], ['My worst interview ever', 66],
]
const thumbs = fs.existsSync(path.join(MEDIA, 'thumbs')) ? fs.readdirSync(path.join(MEDIA, 'thumbs')).sort() : []
const clipsMp4 = fs.existsSync(path.join(MEDIA, 'clips')) ? fs.readdirSync(path.join(MEDIA, 'clips')).sort() : []
const media = (kind, list, i) => (list.length ? `${BASE}/media/${kind}/${list[i % list.length]}` : null)

const JOB_ID = '7b1e2c4a-0000-4000-8000-000000000112'
function highlight(i) {
  const [title, score] = TITLES[i % TITLES.length]
  const start = 120 + i * 431
  return {
    id: `h-${i}`, job: JOB_ID, title, description: `${title}. A moment from ${SHOW}, episode 112.`,
    time_range: `${Math.floor(start / 60)}:${String(start % 60).padStart(2, '0')}`, start_time: start, end_time: start + 38 + i * 3,
    duration_seconds: 38 + i * 3, tags: ['podcast', 'creator', 'growth'], clip_generated: true, virality_score: score,
    virality_reasoning: { summary: 'Strong opening line, one clear point, a payoff at the end.' },
  }
}
function clip(i) {
  const h = highlight(i)
  return {
    id: `c1a0${String(i).padStart(4, '0')}-0000-4000-8000-000000000000`, share_token: `s${i}`, highlight: h,
    duration: h.duration_seconds, file_size: 18_000_000, resolution_width: 1080, resolution_height: 1920, watermark_applied: false,
    download_url: media('clips', clipsMp4, i), preview_url: media('clips', clipsMp4, i), thumbnail_url: media('thumbs', thumbs, i),
    is_rerendering: false, rerender_started_at: null, caption_style: { preset: ['ivo', 'pepper', 'selene', 'sol', 'nyx'][i % 5] },
    topic_tags: ['podcasting', 'growth'], suggested_hashtags: ['#podcast', '#creator', '#shorts'],
    expires_at: new Date(now + 40 * H).toISOString(), created_at: iso(2 * H + i * 60e3), updated_at: iso(H),
    title: h.title, virality_score: h.virality_score,
  }
}
const CLIPS = TITLES.map((_, i) => clip(i))
const JOB = {
  id: JOB_ID, status: 'completed', progress: 100, video_title: `${SHOW} · Ep. 112: Building in public`,
  youtube_url: 'https://www.youtube.com/watch?v=Ep112LongTb', youtube_video_id: 'Ep112LongTb', original_filename: null,
  video_duration: 6840, video_thumbnail_url: media('thumbs', thumbs, 0), clips_count: CLIPS.length,
  highlights: CLIPS.map((c) => ({ ...c.highlight, clip: { ...c, highlight: undefined } })),
  created_at: iso(3 * H), updated_at: iso(2 * H), rendering_started_at: iso(2.9 * H), completed_at: iso(2 * H),
  error_message: null, error_code: null, is_retryable: false, retry_count: 0, clip_style: 'highlights',
}
const PLAN = 'pro'
const PLAN_FEATURES = { shorts_per_month: 500, processing_minutes_per_month: 1500, max_connected_accounts: 3, brand_kits_max: 1, broll_enabled: true, hook_voiceover_enabled: true, youtube_auto_shorts_channels: 1, retention_hours: 48, mcp_enabled: true }
const USER = {
  id: 4242, email: 'maya@example.com', plan: PLAN, plan_features: PLAN_FEATURES,
  subscription_status: { active: true, plan: PLAN, status: 'active', current_period_end: new Date(now + 20 * DAY).toISOString(), cancel_at_period_end: false, billing_interval: 'month' },
  is_subscribed: true, is_quota_exempt: false, access: { status: 'active', can_use_app: true, plan: PLAN },
  email_verified: true, onboarding_completed: true, date_joined: iso(80 * DAY), referral_code: 'MAYA42', referral_bonus_credits: 0,
  first_name: 'Maya', username: 'maya',
}
const page = (results) => ({ count: results.length, next: null, previous: null, results })
const acct = (id, platform, disp) => ({ id, platform, platform_display: disp, platform_username: 'thelongtable', platform_display_name: SHOW,
  status: 'connected', status_display: 'Connected', connected_at: iso(30 * DAY), last_used_at: iso(DAY), is_token_valid: true })
const ACCOUNTS = [acct('a1', 'youtube', 'YouTube'), acct('a2', 'tiktok', 'TikTok')]
const POSTS = CLIPS.slice(0, 6).map((c, i) => ({
  id: `p${i}`, clip: c.id, clip_title: c.title, clip_thumbnail_url: c.thumbnail_url, platform: i % 3 === 2 ? 'tiktok' : 'youtube',
  account: i % 3 === 2 ? 'a2' : 'a1', status: i < 2 ? 'published' : 'scheduled', title: c.title, caption: c.title, hashtags: ['#podcast', '#shorts'],
  scheduled_for: new Date(now + (i - 1) * DAY + (i % 2 ? 6 : 2) * H).toISOString(), published_at: i < 2 ? iso(DAY - i * H) : null,
  created_at: iso(2 * DAY), error_message: null, platform_post_url: null,
}))

const ROUTES = [
  [/^\/auth\/users\/me\/?$/, () => USER],
  [/^\/auth\/users\/plan\/?$/, () => ({ plan: PLAN, features: PLAN_FEATURES })],
  [/^\/auth\/users\/sync\/?$/, () => USER],
  [/^\/auth\/defaults\/?$/, () => ({ caption_preset_id: 'ivo', schedule_template: 'daily', schedule_timezone: 'Europe/Amsterdam', preferred_times: ['09:00', '18:00'], custom_interval_days: null, auto_schedule_enabled: false, outro: { enabled: false, default_outro_name: null }, hook_enabled: true, hook_voice: 'nova', hook_mode: 'pre_moment', hook_accent_color: '#A855F7', hook_speed: 1, hook_delivery: 'natural', clip_style: 'highlights', pro_edit_enabled: false, pro_edit_intensity: 'standard', narration_voice: 'nova', narration_delivery: 'natural', title_emojis: false })],
  [/^\/auth\/api-keys\/?$/, () => []],
  [/^\/usage\/?$/, () => ({
    month: new Date(now).toISOString().slice(0, 7), plan: PLAN,
    shorts: { used: 108, limit: 500, remaining: 392, unlimited: false },
    processing_minutes: { used: 312, limit: 1500, remaining: 1188, unlimited: false },
    max_video_duration_seconds: 7200, submissions_made: 9,
    videos: { used: 9, limit: 50, remaining: 41, unit: 'processing_minutes' }, clips: { generated: 214 },
    entitlements: { broll: true, hook_voiceover: true, outro: true, auto_shorts_channels: 1, caption_preset_ids_allowed: null },
  })],
  [/^\/billing\/plans\/?$/, () => []],
  [/^\/billing\/subscription\/?$/, () => USER.subscription_status],
  [/^\/videos\/jobs\/[^/]+\/highlights\/?$/, () => JOB.highlights],
  [/^\/videos\/jobs\/[^/]+\/status\/?$/, () => ({ status: 'completed', progress: 100 })],
  [/^\/videos\/jobs\/[^/]+\/?$/, () => JOB],
  [/^\/videos\/jobs\/?$/, () => page([JOB])],
  [/^\/videos\/clips\/filter-options\/?$/, () => ({ jobs: [{ id: JOB_ID, title: JOB.video_title }], tags: ['podcasting', 'growth'], caption_presets: ['ivo', 'pepper'] })],
  [/^\/videos\/clips\/trash\/?$/, () => page([])],
  [/^\/videos\/clips\/[^/]+\/variants\/?$/, () => []],
  [/^\/videos\/clips\/([^/]+)\/editor-bundle\/?$/, (m) => {
    const c = CLIPS.find((x) => x.id === m[1]) || CLIPS[0]
    return { clip: c, edl: null, agent_broll_suggestions: null, framing_pending: false,
      assets: { source: { id: 'src1', proxy_url: media('clips', clipsMp4, 0), status: 'ready', duration_s: 5 }, broll: [], music: [], images: [], brand_logo: null,
        final: { url: c.preview_url, duration_s: c.duration }, window: { url: c.preview_url, src_start: 0, src_end: 5, width: 720, height: 1280, status: 'ready' } } }
  }],
  [/^\/videos\/clips\/[^/]+\/caption-words\/?$/, () => {
    const line = 'Consistency beats talent every single time, and nobody wants to hear that'.split(' ')
    return { words: line.map((text, i) => ({ text, start: 0.3 + i * 0.36, end: 0.3 + i * 0.36 + 0.32, tags: i === 1 ? ['emphasis'] : [] })), subtitles_version: 1, time_base: 'content', hook: null }
  }],
  [/^\/videos\/clips\/([^/]+)\/(source|preview)-proxy\/?$/, (m) => ({ status: 'ready', proxy_url: media('clips', clipsMp4, 0), duration_seconds: 5, job_id: JOB_ID, clip_id: m[1], sprite: null })],
  [/^\/videos\/clips\/([^/]+)\/?$/, (m) => CLIPS.find((c) => c.id === m[1]) || CLIPS[0]],
  [/^\/videos\/clips\/?$/, () => page(CLIPS)],
  [/^\/social\/accounts\/?$/, () => ACCOUNTS],
  [/^\/social\/scheduled-posts\/?$/, (m, q) => page(POSTS.filter((x) => !q.get('status') || q.get('status').split(',').includes(x.status)))],
  [/^\/social\/presets\/?$/, () => []],
  [/^\/social\/posting\/smart-timing\/templates\/?$/, () => []],
  [/^\/gamification\/profile\/?$/, () => ({
    rank: { tier: 'specialist', tier_display: 'Specialist', cumulative_score: 2140, next_tier_threshold: 2500 },
    streak: { weekly: 8, daily: 3, longest_weekly: 12, longest_daily: 9, multiplier: 1.2, freezes_remaining: 1, active_today: true },
    score: { score: 81, breakdown: { consistency: 28, volume: 24, quality: 29 } },
    achievements: { earned: 14, total: 40, has_new: false }, stats: { total_videos: 9, total_clips: 214 },
  })],
  [/^\/gamification\/achievements\/recent-unlocks\/?$/, () => []],
  [/^\/gamification\/achievements\/?$/, () => [
    ['First clip', 'Make your first clip', 'creation', 'gold', 1, 1], ['Weekly rhythm', 'Post 4 weeks in a row', 'streaks', 'silver', 4, 8],
    ['Hundred club', 'Make 100 clips', 'clips', 'platinum', 100, 214], ['Two platforms', 'Post to YouTube and TikTok', 'multiplatform', 'gold', 2, 2],
    ['On the calendar', 'Schedule 10 posts', 'publishing', 'silver', 10, 10], ['Top score', 'Make a clip that scores 90+', 'quality', 'gold', 1, 1],
    ['Marathon', 'Process 10 hours of video', 'creation', 'bronze', 600, 312], ['Explorer', 'Try 5 caption styles', 'exploration', 'locked', 5, 3],
  ].map(([name, description, category, tier, threshold, cur], i) => ({ id: `ach${i}`, name, description, category, tier, icon: ['🎬', '🔥', '💯', '🌍', '📅', '⭐', '⏱️', '🎨'][i],
    threshold, current_value: cur, progress: Math.min(1, cur / threshold), rarity_pct: 12 + i * 7, unlocked_at: cur >= threshold ? iso((i + 1) * DAY) : null,
    is_new: false, secret: false, points: 50 + i * 25 }))],
  [/^\/gamification\/streak\/?$/, () => ({ current: 8, longest: 12, weekly: 8 })],
  [/^\/gamification\/notifications\/unread-count\/?$/, () => ({ count: 0 })],
  [/^\/gamification\/notifications\/?$/, () => page([])],
  [/^\/gamification\/leaderboard\/?$/, () => ({ cohort_id: 1, week: '2026-W42', current_user_rank: 2, cohort_size: 30, resets_at: new Date(now + 3 * DAY).toISOString(),
    entries: ['nova', 'maya', 'rivvo', 'kaito', 'lumen'].map((n, i) => ({ rank: i + 1, user_id: i === 1 ? 4242 : 100 + i, display_name: n, username: n, score: 980 - i * 90, is_current_user: i === 1, tier: 'specialist', rank_tier: ['expert', 'specialist', 'specialist', 'creator', 'creator'][i] })) })],
  [/^\/copilot\/starters\/?$/, () => ({ starters: ['Give my last three clips punchier titles', 'Schedule my five best clips across next week', 'Add B-roll where he talks about the factory'] })],
  [/^\/copilot\/conversations\/?$/, () => ({ conversations: [] })],
  [/^\/autopilot\/profiles\/?$/, () => []],
  [/^\/autopilot\/routes\/?$/, () => [{ id: 1, subscription: 1, channel_id: 'UCLongTable', channel_title: SHOW, profile: null, spec_overrides: {},
    youtube_account_ids: ['a1'], destination_account_ids: ['a1', 'a2'], schedule_template: 'daily', custom_interval_days: null, timezone: 'Europe/Amsterdam',
    preferred_times: ['09:00', '18:00'], upload_window_mode: 'all', upload_window_hours: null, videos_since_at: iso(14 * DAY), enabled: true, review_mode: true,
    shorts_cap: 8, footage_minutes_cap: null, created_at: iso(14 * DAY) }]],
  [/^\/autopilot\/reviews\/health\/?$/, () => ({ pending: 0 })],
  [/^\/autopilot\/reviews\/?$/, () => page([])],
  [/^\/channel-subscriptions\/status\/?$/, () => ({ enabled: true, channels_used: 1, channels_limit: 1 })],
  [/^\/channel-subscriptions\/config\/?$/, () => ({})],
  [/^\/channel-subscriptions\/?$/, () => []],
  [/^\/brand-kit\/?$/, () => [{ id: 'bk1', name: SHOW, is_default: true, archived_at: null, logo_url: null, logo_position: 'top_right', logo_size: 'small',
    logo_opacity: 0.9, primary_color: '#A855F7', secondary_color: '#0F0F23', accent_color: '#FACC15', extracted_colors: ['#A855F7', '#0F0F23', '#FACC15'],
    font_id: 'montserrat', watermark_text: '@thelongtable', vocabulary: { 'Long Table': 'Long Table' }, brand_voice: 'Warm, curious, direct.', created_at: iso(20 * DAY), updated_at: iso(DAY) }]],
  [/^\/outros\/settings\/?$/, () => ({ enabled: false })],
  [/^\/outros\/?$/, () => []],
  [/^\/referral\/stats\/?$/, () => ({ referrals: 0, earnings: 0 })],
  [/^\/system\/(status|health)\/?$/, () => ({ status: 'ok' })],
  [/^\/health\/?$/, () => ({ status: 'ok' })],
]
// Optional per-screen overrides: screens/fixtures/*.json { "path regex": json }
const OVERRIDES = []
const fx = path.join(HERE, 'fixtures')
if (fs.existsSync(fx)) for (const f of fs.readdirSync(fx).filter((x) => x.endsWith('.json'))) {
  for (const [k, v] of Object.entries(JSON.parse(fs.readFileSync(path.join(fx, f), 'utf8')))) OVERRIDES.push([new RegExp(k), () => v])
}

http.createServer((req, res) => {
  const u = new URL(req.url, BASE)
  const cors = { 'Access-Control-Allow-Origin': req.headers.origin || '*', 'Access-Control-Allow-Credentials': 'true', 'Access-Control-Allow-Headers': '*', 'Access-Control-Allow-Methods': 'GET,POST,PATCH,PUT,DELETE,OPTIONS' }
  if (req.method === 'OPTIONS') { res.writeHead(204, cors); return res.end() }
  if (u.pathname.startsWith('/media/')) {
    const f = path.join(MEDIA, u.pathname.slice(7))
    if (!fs.existsSync(f)) { res.writeHead(404, cors); return res.end() }
    res.writeHead(200, { ...cors, 'Content-Type': f.endsWith('.mp4') ? 'video/mp4' : 'image/jpeg' }); return fs.createReadStream(f).pipe(res)
  }
  const p = u.pathname.replace(/^\/api\/v1/, '')
  const hit = [...OVERRIDES, ...ROUTES].find(([re]) => re.test(p))
  const body = hit ? hit[1](p.match(hit[0]), u.searchParams) : req.method === 'GET' ? {} : { ok: true }
  LOG.write(`${req.method} ${p} ${hit ? 'fixture' : 'UNKNOWN'}\n`)
  res.writeHead(200, { ...cors, 'Content-Type': 'application/json' }); res.end(JSON.stringify(body))
}).listen(PORT, '127.0.0.1', () => console.log(`stand-in API on ${BASE}`))
