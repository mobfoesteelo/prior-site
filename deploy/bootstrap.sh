#!/usr/bin/env bash
# PRIOR · Hetzner VPS bootstrap
# Provision a fresh Ubuntu 22.04+ box, then run this as root:
#
#   curl -fsSL https://raw.githubusercontent.com/<YOUR_GH_USER>/prior-site/main/deploy/bootstrap.sh | bash
#
# OR git clone first and run:
#
#   bash deploy/bootstrap.sh
#
# The script is idempotent — safe to re-run.

set -euo pipefail

# ── config ────────────────────────────────────────────────────────────────
GH_USER="${PRIOR_GH_USER:-}"          # set if cloning via curl-pipe
GH_REPO="${PRIOR_GH_REPO:-prior-site}"
BRANCH="${PRIOR_BRANCH:-main}"
PRIOR_USER="${PRIOR_USER:-prior}"
INSTALL_DIR="/home/${PRIOR_USER}/${GH_REPO}"
ENV_FILE="/home/${PRIOR_USER}/.prior-env"

if [[ "${EUID}" -ne 0 ]]; then
  echo "ERROR: run as root (sudo)"; exit 1
fi

echo ">>> updating apt + installing deps"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq python3 python3-pip python3-venv git curl ca-certificates ufw fail2ban unattended-upgrades

echo ">>> creating user '${PRIOR_USER}' if needed"
if ! id "${PRIOR_USER}" &>/dev/null; then
  useradd -m -s /bin/bash "${PRIOR_USER}"
fi

echo ">>> minimal firewall (22 only)"
ufw default deny incoming || true
ufw default allow outgoing || true
ufw allow OpenSSH || true
yes | ufw enable || true

echo ">>> auto-security-updates"
dpkg-reconfigure -f noninteractive unattended-upgrades || true

# ── pull the repo ─────────────────────────────────────────────────────────
if [[ ! -d "${INSTALL_DIR}/.git" ]]; then
  if [[ -z "${GH_USER}" ]]; then
    echo "ERROR: PRIOR_GH_USER not set. set it (your GitHub username) or git-clone manually."
    exit 1
  fi
  echo ">>> cloning repo"
  sudo -u "${PRIOR_USER}" git clone --branch "${BRANCH}" "https://github.com/${GH_USER}/${GH_REPO}.git" "${INSTALL_DIR}"
else
  echo ">>> repo exists, pulling latest"
  sudo -u "${PRIOR_USER}" git -C "${INSTALL_DIR}" pull --ff-only
fi

# ── python venv + deps ────────────────────────────────────────────────────
echo ">>> python venv"
if [[ ! -d "${INSTALL_DIR}/.venv" ]]; then
  sudo -u "${PRIOR_USER}" python3 -m venv "${INSTALL_DIR}/.venv"
fi
sudo -u "${PRIOR_USER}" "${INSTALL_DIR}/.venv/bin/pip" install --quiet --upgrade pip
sudo -u "${PRIOR_USER}" "${INSTALL_DIR}/.venv/bin/pip" install --quiet -r "${INSTALL_DIR}/scripts/requirements.txt"

# ── env file ──────────────────────────────────────────────────────────────
if [[ ! -f "${ENV_FILE}" ]]; then
  echo ">>> writing template ${ENV_FILE} — fill in your keys then re-run."
  cat > "${ENV_FILE}" <<EOF
# PRIOR runtime env. systemd reads via EnvironmentFile=
# Mode 0600. Owned by ${PRIOR_USER}. Do NOT commit this file.

ANTHROPIC_API_KEY=

X_API_KEY=
X_API_SECRET=
X_ACCESS_TOKEN=
X_ACCESS_TOKEN_SECRET=

# Optional / git-push back so vercel rebuilds:
# Generate a fine-grained PAT with "Contents: write" on the repo.
# Then use HTTPS remote with token auth (see below).
GH_PUSH_TOKEN=
GIT_USER_NAME=prior.agent
GIT_USER_EMAIL=prior-bot@users.noreply.github.com
EOF
  chown "${PRIOR_USER}:${PRIOR_USER}" "${ENV_FILE}"
  chmod 600 "${ENV_FILE}"
  echo
  echo "============================================================="
  echo " ENV FILE CREATED. Edit it now:"
  echo "   sudo nano ${ENV_FILE}"
  echo " Fill in ANTHROPIC_API_KEY + the 4 X_* keys."
  echo " Then re-run this script to install systemd units."
  echo "============================================================="
  exit 0
fi

# ── git push helper script (used by systemd to push log/alerts back) ──────
cat > "${INSTALL_DIR}/deploy/push-data.sh" <<'PUSH_EOF'
#!/usr/bin/env bash
# Commit + push data/* updates so Vercel auto-redeploys
set -euo pipefail
cd "$(dirname "$0")/.."
. /home/${SUDO_USER:-prior}/.prior-env 2>/dev/null || . ~/.prior-env

git config user.name  "${GIT_USER_NAME:-prior.agent}"
git config user.email "${GIT_USER_EMAIL:-prior-bot@users.noreply.github.com}"

if [[ -n "$(git status --porcelain data/)" ]]; then
  git add data/
  git commit -m "prior: data update $(date -u +'%Y-%m-%dT%H:%MZ')" >/dev/null
  if [[ -n "${GH_PUSH_TOKEN:-}" ]]; then
    REMOTE=$(git config --get remote.origin.url | sed "s|https://|https://x-access-token:${GH_PUSH_TOKEN}@|")
    git push "$REMOTE" HEAD:main >/dev/null 2>&1 || echo "[push failed — staying local]"
  else
    git push origin HEAD:main >/dev/null 2>&1 || echo "[push failed — set GH_PUSH_TOKEN in .prior-env]"
  fi
fi
PUSH_EOF
chmod +x "${INSTALL_DIR}/deploy/push-data.sh"
chown "${PRIOR_USER}:${PRIOR_USER}" "${INSTALL_DIR}/deploy/push-data.sh"

# ── install systemd units ─────────────────────────────────────────────────
install_unit() {
  local name="$1"
  cp "${INSTALL_DIR}/deploy/${name}" "/etc/systemd/system/${name}"
  chmod 644 "/etc/systemd/system/${name}"
}

echo ">>> installing systemd units"
install_unit prior-bot.service
install_unit prior-bot.timer
install_unit prior-backrooms.service
install_unit prior-backrooms.timer
install_unit prior-monitor.service
install_unit prior-monitor.timer
install_unit prior-replies.service
install_unit prior-replies.timer

# Substitute the install dir + user + env path into each service file
for unit in prior-bot.service prior-backrooms.service prior-monitor.service prior-replies.service; do
  sed -i "s|__INSTALL_DIR__|${INSTALL_DIR}|g" "/etc/systemd/system/${unit}"
  sed -i "s|__PRIOR_USER__|${PRIOR_USER}|g"   "/etc/systemd/system/${unit}"
  sed -i "s|__ENV_FILE__|${ENV_FILE}|g"       "/etc/systemd/system/${unit}"
done

systemctl daemon-reload

echo ">>> enabling + starting timers"
systemctl enable --now prior-bot.timer
systemctl enable --now prior-backrooms.timer
systemctl enable --now prior-monitor.timer
systemctl enable --now prior-replies.timer

echo
echo "============================================================="
echo " ✓ PRIOR runtime installed."
echo
echo " timers active:"
systemctl list-timers --no-pager 'prior-*' | head -10
echo
echo " logs:"
echo "   journalctl -u prior-bot.service -f"
echo "   journalctl -u prior-backrooms.service -f"
echo "   journalctl -u prior-monitor.service -f"
echo
echo " manual test (does not actually post):"
echo "   sudo -u ${PRIOR_USER} bash -c 'set -a; . ${ENV_FILE}; PRIOR_DRY_RUN=1 ${INSTALL_DIR}/.venv/bin/python ${INSTALL_DIR}/scripts/prior_bot.py'"
echo "============================================================="
