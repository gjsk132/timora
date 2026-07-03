#!/bin/bash
# Timora release helper.
#
# Tags the current commit, pushes the tag, builds a clean distributable zip
# (tracked files only — no venv, no personal data.json), then creates a GitHub
# Release and uploads the zip as an asset.
#
# Usage:
#   GITHUB_TOKEN=ghp_xxx ./release.sh <version> [notes-file]
#
#   version     e.g. 1.1.0  or  v1.1.0
#   notes-file  optional markdown file for the release body
#
# Requires: a GitHub Personal Access Token with the "repo" scope in $GITHUB_TOKEN
#           (or $GH_TOKEN). git and python3 must be available.
set -euo pipefail

# ---- args & env ----
VERSION="${1:-}"
if [ -z "$VERSION" ]; then
  echo "usage: GITHUB_TOKEN=ghp_xxx ./release.sh <version> [notes-file]" >&2
  exit 1
fi
case "$VERSION" in v*) ;; *) VERSION="v$VERSION" ;; esac

NOTES_FILE="${2:-}"
TOKEN="${GITHUB_TOKEN:-${GH_TOKEN:-}}"
if [ -z "$TOKEN" ]; then
  echo "error: set GITHUB_TOKEN (or GH_TOKEN) to a PAT with the 'repo' scope." >&2
  exit 1
fi
REPO="${TIMORA_REPO:-gjsk132/timora}"

cd "$(dirname "${BASH_SOURCE[0]}")"

# ---- warn on uncommitted changes ----
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "warning: you have uncommitted changes; the tag will point at the last commit." >&2
fi

# ---- tag (create if missing) + push ----
if git rev-parse -q --verify "refs/tags/$VERSION" >/dev/null; then
  echo "tag $VERSION already exists locally — reusing it."
else
  git tag -a "$VERSION" -m "Timora $VERSION"
  echo "created tag $VERSION"
fi
git push origin "$VERSION"

# ---- build clean asset ----
ASSET="/tmp/Timora-$VERSION.zip"
ASSET_NAME="Timora-$VERSION.zip"
git archive --prefix=timora/ --format=zip -o "$ASSET" "$VERSION"
echo "built asset: $ASSET ($(du -h "$ASSET" | cut -f1))"

# ---- default release notes ----
if [ -z "$NOTES_FILE" ]; then
  NOTES_FILE="$(mktemp)"
  cat > "$NOTES_FILE" <<EOF
# Timora $VERSION

macOS menu bar time tracker (English / 한국어).

## Install
1. Download **$ASSET_NAME** below and unzip it.
2. Double-click **install.command** (if macOS warns: right-click → Open → Open).
3. Double-click **Timora.app** — a book icon appears in the menu bar.

> macOS 10.13+ · needs Python 3 (\`xcode-select --install\` if prompted).
EOF
fi

# ---- create release + upload asset via REST API ----
GITHUB_TOKEN="$TOKEN" REPO="$REPO" VERSION="$VERSION" \
ASSET="$ASSET" ASSET_NAME="$ASSET_NAME" NOTES_FILE="$NOTES_FILE" \
python3 - <<'PY'
import os, json, urllib.request, urllib.error

TOKEN = os.environ["GITHUB_TOKEN"]
REPO = os.environ["REPO"]
VERSION = os.environ["VERSION"]
ASSET = os.environ["ASSET"]
ASSET_NAME = os.environ["ASSET_NAME"]

with open(os.environ["NOTES_FILE"], encoding="utf-8") as f:
    body = f.read()

def req(url, data=None, headers=None, method=None):
    h = {"Authorization": f"token {TOKEN}",
         "Accept": "application/vnd.github+json",
         "User-Agent": "timora-release"}
    if headers:
        h.update(headers)
    r = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")

payload = json.dumps({
    "tag_name": VERSION, "name": f"Timora {VERSION}",
    "body": body, "draft": False, "prerelease": False,
}).encode()
status, rel = req(f"https://api.github.com/repos/{REPO}/releases",
                  data=payload, headers={"Content-Type": "application/json"},
                  method="POST")
if status not in (200, 201):
    msg = json.dumps(rel)
    if "already_exists" in msg:
        print(f"error: a release for {VERSION} already exists. "
              f"Delete it first, or bump the version.")
    else:
        print("error creating release:", status, msg[:400])
    raise SystemExit(1)

rel_id = rel["id"]
with open(ASSET, "rb") as f:
    blob = f.read()
up = f"https://uploads.github.com/repos/{REPO}/releases/{rel_id}/assets?name={ASSET_NAME}"
status, asset = req(up, data=blob,
                    headers={"Content-Type": "application/zip"}, method="POST")
if status not in (200, 201):
    print("error uploading asset:", status, json.dumps(asset)[:400])
    raise SystemExit(1)

print("released:", rel["html_url"])
print("download:", asset["browser_download_url"])
PY

echo "done."
