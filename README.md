# $PRIOR — the bot that was early

Autonomous X-posting AI agent + coin launch site.

Site: static HTML/CSS/JS (Vercel).
Bot: Python — generates in-character posts via Claude API, posts to X, appends to `api/log.json` which powers the site's live feed.

---

## Quick start

### 1. Deploy site to Vercel

```bash
cd C:\Users\Steelo\prior-site
npx vercel --prod --yes
```

Takes ~30 seconds. You get a `*.vercel.app` URL. Point a domain at it from the Vercel dashboard when ready.

### 2. Get the 5 secrets you need

| Secret | Where |
|---|---|
| `ANTHROPIC_API_KEY` | console.anthropic.com → API Keys |
| `X_API_KEY` | developer.x.com → your app → Keys & Tokens → API Key |
| `X_API_SECRET` | same panel → API Key Secret |
| `X_ACCESS_TOKEN` | same panel → Access Token |
| `X_ACCESS_TOKEN_SECRET` | same panel → Access Token Secret |

**X dev account notes**
- Create a new account at x.com (handle: `@prior_agent` or similar).
- Sign up for the Developer portal (Free tier works for ~17 posts/day, plenty for 6/day schedule).
- Create an app. On the app → Settings → User authentication: enable **Read + Write** permissions. **Save before generating the access token.**
- Generate API Key + Secret and Access Token + Secret.

### 3. Create a GitHub repo and add secrets

```bash
cd C:\Users\Steelo\prior-site
git init
git add .
git commit -m "prior: initial"
gh repo create prior-site --private --source=. --push
```

Then add secrets at `Settings → Secrets and variables → Actions → New repository secret` — one for each of the five keys above.

### 4. Test the bot locally (dry run)

```bash
pip install -r scripts/requirements.txt
set ANTHROPIC_API_KEY=sk-ant-...
set PRIOR_DRY_RUN=1
python scripts/prior_bot.py
```

Should print a generated post. No actual X post. `api/log.json` will update.

### 5. Flip live

In `.github/workflows/prior-bot.yml`, the schedule runs every 4 hours. Push once and it's live.

Manual run anytime: GitHub → Actions tab → **prior.agent** → Run workflow.

### 6. When you mint the coin

Find-replace `TBA_CONTRACT_ADDRESS_HERE` in `index.html` (2 occurrences) with your pump.fun CA, then:

```bash
npx vercel --prod --yes
```

Pump.fun buttons auto-link to `https://pump.fun/coin/<CA>`.

---

## File map

```
prior-site/
├── index.html           # site
├── style.css
├── script.js
├── vercel.json
├── api/
│   └── log.json         # the live feed — bot appends here
├── scripts/
│   ├── prior_bot.py     # the bot
│   └── requirements.txt
├── .github/workflows/
│   └── prior-bot.yml    # cron: every 4 hours
└── assets/
```

---

## Voice knobs

Edit `scripts/prior_bot.py`:

- `SYSTEM_PROMPT` — the character's identity / constraints
- `USER_PROMPTS` — rotating mood categories (receipt / observation / archive / question / echo / pulse)
- `PRIOR_MODEL` env var — override model (default `claude-sonnet-4-5`)

Tweak and redeploy by pushing a commit.

---

## If Claude or X API is down

The site's feed falls back to the hardcoded posts in `index.html`. No outage visible to visitors.

---

## Disclaimer

$PRIOR is a meme coin. No intrinsic value. The bot is an AI persona, not financial advice.
