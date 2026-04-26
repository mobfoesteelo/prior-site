# PRIOR · Hetzner VPS handoff

The 24/7 runtime. Replaces GitHub Actions cron entirely.

---

## What runs on the box

Four systemd timers, all installed by `deploy/bootstrap.sh`:

| timer | cadence | script | purpose |
|---|---|---|---|
| `prior-bot.timer` | every 4h at :17 | `scripts/prior_bot.py` | autonomous post (witness + informant) |
| `prior-backrooms.timer` | daily 03:11 UTC | `scripts/generate_backroom.py` | self-conversation archive |
| `prior-monitor.timer` | every 15 min | `scripts/live_monitor.py` | RSS poll → alert post when a cycle pattern fires |
| `prior-replies.timer` | every 30 min | `scripts/replies.py` | engages worthy mentions, filters spam |

Each service runs `deploy/push-data.sh` after — commits `data/*` and pushes to GitHub. Vercel auto-rebuilds the site from the push.

---

## Provisioning steps

### 1. Create the VPS
Hetzner Cloud Console → New Server.
- Location: any (Falkenstein/Helsinki/Ashburn fine)
- Image: **Ubuntu 22.04** (or 24.04)
- Type: **CPX11** (~€4.50/mo, 2 vCPU / 2GB) — enough for everything
- Networking: IPv4 + IPv6 enabled
- SSH key: add yours
- Name: `prior-runtime`

Wait ~30s, copy the IPv4 address.

### 2. SSH in as root
```bash
ssh root@<IPV4>
```

### 3. (Optional) generate a GitHub PAT for push-back
You want the box to push `data/log.json`, `data/alerts.json`, etc. back to GitHub so Vercel rebuilds the site.

- GitHub → Settings → Developer settings → **Fine-grained personal access tokens**
- New token. Repository access: only `prior-site`. Permissions: **Contents: Read and write**.
- Copy the `github_pat_...` token. Save it — you'll paste it into `.prior-env`.

### 4. Run the bootstrap

```bash
# clone first, cleanest path:
apt-get update && apt-get install -y git
git clone https://github.com/<YOUR_GH_USER>/prior-site /tmp/prior-site
bash /tmp/prior-site/deploy/bootstrap.sh
```

(or curl-pipe with `PRIOR_GH_USER=<you>` env first if you prefer.)

The script is **idempotent** — safe to re-run.

On first run it will:
- install python, git, ufw, fail2ban
- create user `prior`
- enable firewall (port 22 only)
- clone the repo to `/home/prior/prior-site`
- create venv + install deps
- write `/home/prior/.prior-env` template
- **then exit** so you can fill in keys

### 5. Fill in the env file

```bash
sudo nano /home/prior/.prior-env
```

Paste in:
```
ANTHROPIC_API_KEY=sk-ant-...

X_API_KEY=...
X_API_SECRET=...
X_ACCESS_TOKEN=...
X_ACCESS_TOKEN_SECRET=...

GH_PUSH_TOKEN=github_pat_...
GIT_USER_NAME=prior.agent
GIT_USER_EMAIL=prior-bot@users.noreply.github.com
```

Save (`Ctrl+O`, `Enter`, `Ctrl+X`). Permissions are 0600 already.

### 6. Re-run bootstrap to install the timers

```bash
bash /tmp/prior-site/deploy/bootstrap.sh
```

This time it skips env creation, installs the systemd units, enables and starts the timers.

### 7. Verify

```bash
# all four timers should be active and have a Next firing time
systemctl list-timers 'prior-*'

# tail the bot logs
journalctl -u prior-bot.service -f
journalctl -u prior-monitor.service -f
journalctl -u prior-replies.service -f
journalctl -u prior-backrooms.service -f
```

### 8. Smoke-test without posting

```bash
sudo -u prior bash -c 'set -a; . /home/prior/.prior-env; PRIOR_DRY_RUN=1 /home/prior/prior-site/.venv/bin/python /home/prior/prior-site/scripts/prior_bot.py'
```

Should print a generated post and exit 0.

---

## Updating the bot later

```bash
ssh prior@<IPV4>
cd ~/prior-site
git pull
sudo systemctl restart prior-bot.timer prior-backrooms.timer prior-monitor.timer prior-replies.timer
```

(restart isn't strictly needed — next firing picks up new code automatically — but it's a clean reset.)

---

## Killing a runaway

```bash
# pause all timers
sudo systemctl stop prior-bot.timer prior-backrooms.timer prior-monitor.timer prior-replies.timer

# resume
sudo systemctl start prior-bot.timer prior-backrooms.timer prior-monitor.timer prior-replies.timer
```

For a single bad post: edit `data/log.json` directly on the box, push, Vercel rebuilds.

---

## Cost ballpark

- Hetzner CPX11: ~€4.50/mo (~$5)
- Anthropic API: ~$2-4/mo at the configured cadence
- X API: free tier covers ~17 posts/day; we're at ~6 base posts + up to 8 replies + up to 4 alerts = 18/day max — **on the edge**. Watch the rate limit. If you hit it, drop `prior-monitor.timer` to every 30 min.

---

## Files added for the runtime

```
deploy/
  bootstrap.sh
  push-data.sh                (created at runtime)
  prior-bot.service
  prior-bot.timer
  prior-backrooms.service
  prior-backrooms.timer
  prior-monitor.service
  prior-monitor.timer
  prior-replies.service
  prior-replies.timer
scripts/
  live_monitor.py             (RSS → alert generator)
  replies.py                  (mentions → reply engine)
```

---

## What stays on GitHub Actions

Nothing scheduled. Both workflows have their `schedule:` blocks commented out. They're kept for **manual fallback** via `workflow_dispatch` in case the VPS is down.

---

## DNS reminder

`priorprotocol.fun` and `www.priorprotocol.fun` need:
- **A record** → `76.76.21.21`
- **CNAME** for `www` → `cname.vercel-dns.com`

(set at your registrar; not the VPS.)

---

## Security notes

- `.prior-env` is mode 0600, owned by `prior` user, never committed
- the X API keys you pasted in chat earlier — **rotate them after the box is up and the new keys are in `.prior-env`.** assume the chat-pasted ones are burned.
- ufw default: deny incoming, allow OpenSSH only. Box has no public web surface.
- `unattended-upgrades` enabled for auto security patches.
