#!/usr/bin/env bash
# One-shot local-dev setup for the Django Portfolio.
# Idempotent: safe to re-run.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

VENV_DIR="$REPO_ROOT/.venv"
PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "==> Using Python: $($PYTHON_BIN --version) at $(command -v "$PYTHON_BIN")"

# 1. Virtualenv
if [[ ! -d "$VENV_DIR" ]]; then
  echo "==> Creating virtualenv at $VENV_DIR"
  "$PYTHON_BIN" -m venv "$VENV_DIR"
else
  echo "==> Reusing existing virtualenv at $VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip wheel >/dev/null

# 2. Python deps
REQ_FILE="requirements-dev.txt"
if [[ ! -f "$REQ_FILE" ]]; then
  REQ_FILE="requirements.txt"
fi
echo "==> Installing Python dependencies from $REQ_FILE"
pip install -r "$REQ_FILE"

# 3. .env for local dev (only if missing)
if [[ ! -f "$REPO_ROOT/.env" ]]; then
  echo "==> Creating .env with local-dev defaults (SQLite + LocMem cache)"
  cat > "$REPO_ROOT/.env" <<'EOF'
APP_SECRET=dev-insecure-secret-change-me
DJANGO_SETTINGS_MODULE=portfolio.settings.dev

# GitHub (optional for local run)
GITHUB_API=https://api.github.com
GITHUB_TOKEN=

# Leetcode (optional)
LEETCODE_GRAPHQL_API=https://leetcode.com/graphql
LEETCODE_REST_API=https://alfa-leetcode-api.onrender.com/
LEETCODE_USERNAME=

# HuggingFace (optional)
HF_TOKEN=

# Local-dev placeholders (dev.py swaps these out for SQLite + LocMem)
MYSQL_DB_NAME=portfolio_db
MYSQL_DB_USER=root
MYSQL_DB_HOST=127.0.0.1
MYSQL_DB_PASS=

MEMCACHED_SERVERS=127.0.0.1:11211
MEMCACHED_USERNAME=
MEMCAHCED_USERNAME=
MEMCACHED_PASSWORD=
EOF
else
  echo "==> .env already exists, leaving it alone"
fi

# 4. Tailwind (theme app) - install node deps
THEME_DIR="$REPO_ROOT/theme/static_src"
if [[ -f "$THEME_DIR/package.json" ]]; then
  echo "==> Installing Tailwind/Node dependencies"
  pushd "$THEME_DIR" >/dev/null
  if [[ ! -d node_modules ]]; then
    npm install
  else
    echo "    node_modules already present, skipping"
  fi
  popd >/dev/null
else
  echo "==> No theme/static_src/package.json found, skipping npm step"
fi

# 5. Database migrations
export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-portfolio.settings.dev}"
echo "==> Running migrations (DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE)"
python manage.py makemigrations
python manage.py migrate --noinput

# 6. Static + messages
echo "==> collectstatic"
python manage.py collectstatic --noinput || true

if command -v msgfmt >/dev/null 2>&1; then
  echo "==> compilemessages"
  python manage.py compilemessages || true
else
  echo "==> Skipping compilemessages (msgfmt not installed; existing .mo files will be used as-is)"
fi

# 7. Helpful hints
cat <<'NEXT'

✅ Setup complete.

To run the dev server:

    source .venv/bin/activate
    export DJANGO_SETTINGS_MODULE=portfolio.settings.dev
    python manage.py runserver

Or, in two terminals:

    # Terminal A - Tailwind watcher
    source .venv/bin/activate
    python manage.py tailwind start

    # Terminal B - Django
    source .venv/bin/activate
    export DJANGO_SETTINGS_MODULE=portfolio.settings.dev
    python manage.py runserver

Visit http://127.0.0.1:8000/
Admin (after creating a superuser): http://127.0.0.1:8000/settings/admin/dashboard/

    python manage.py createsuperuser

NEXT