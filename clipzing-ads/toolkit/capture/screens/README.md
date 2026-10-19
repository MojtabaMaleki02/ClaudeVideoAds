# Real Clipzing screens, fictional data

The real frontend (a production build) runs locally against `mockapi.mjs`, a stand-in API serving a fictional
podcast ("The Long Table", ep. 112, nine clips, Zing's footage as thumbnails). A TEST user signs into the Clerk
**development** instance with a sign-in ticket. Each dashboard route is screenshotted at 1440×900 @2× and 390×844 @3×.
Nothing touches production or real users. The product's stock-photo caption backdrop is swapped for Zing's podcast.

Output already in the library: `library/screens/{desktop,mobile}-{dashboard,videos,job,calendar,autopilot,accounts,
brand-kit,preferences,achievements,billing,editor}.png`. Re-shoot after UI changes.

## Steps (≈ 15 min, most of it the build)
```bash
S=<scratch dir>
git -C ~/shorten worktree add --detach $S/fe-wt HEAD             # never build in the user's own tree / .next
cd $S/fe-wt/shortn-fe && cp ~/shorten/shortn-fe/.env.local .env.local
# in .env.local: NEXT_PUBLIC_API_URL=http://127.0.0.1:8787/api/v1, NEXT_PUBLIC_POSTHOG_KEY= (empty),
#                NEXT_PUBLIC_CLERK_SIGN_IN_FORCE_REDIRECT_URL= and ..._SIGN_UP_... = (empty)
npm ci && npx next build
npx next start -p 3111                                            # NOT -H 127.0.0.1: middleware proxies to localhost
node <skill>/toolkit/capture/screens/mockapi.mjs &                # :8787, logs every request to mockapi.log
node <skill>/toolkit/capture/screens/shoot_screens.mjs --app http://localhost:3111 --env $S/fe-wt/shortn-fe/.env.local --out $S/screens
# copy $S/screens/{desktop,mobile}/*.png → library/screens/<label>-<name>.png ; then remove the worktree:
git -C ~/shorten worktree remove --force $S/fe-wt
```

## When a screen shows "Something went wrong"
Run with `DEBUG=1` to print the page's console errors, and read `mockapi.log`: `UNKNOWN` lines are endpoints with no
fixture. Find the response type in `shortn-fe/lib/api.ts` / `types/index.ts` / `hooks/queries/*` and add a route
to `mockapi.mjs`, or put a per-screen override in `fixtures/*.json` (`{"<path regex>": <json>}`).
Shapes learned so far: lists are paginated `{count, next, previous, results}`; usage meters are `{used, limit,
remaining, unlimited}` with `entitlements.auto_shorts_channels` gating Autopilot; social accounts need
`status: 'connected'`; leaderboard entries need `rank_tier`; scheduled posts use `scheduled_for` and the API
filters by `?status=`.

## Rules
- Fictional data only: a fictional show, fictional names (maya, nova, rivvo), the example.com email, Zing's footage.
- Only the Clerk DEVELOPMENT keys (`sk_test_…`); the script refuses others. The test user is
  `maya+clerk_test@example.com` (created once, reused). Sign-in tickets are single-use: one per browser context.
- Never capture the user's real account or production pages behind a login.
