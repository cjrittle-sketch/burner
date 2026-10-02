#!/usr/bin/env bash
# burner web installer.
#   curl -fsSL https://useburner.si/install.sh | bash
#
# Fetches burner into $BURNER_DIR (default: $HOME/burner) and runs its local
# install.sh. If the directory is already a git checkout, it is updated with
# `git pull --ff-only` instead; if it was created by this installer (marker
# file .burner-web-install), it is refreshed in place. config.env, .venv/ and
# other local state are never deleted. No sudo. Safe to re-run.
set -u

TARBALL_URL="https://github.com/useburner/burner/archive/refs/heads/master.tar.gz"
DEST="${BURNER_DIR:-$HOME/burner}"
MARKER=".burner-web-install"

die() { echo "burner: ERROR: $*" >&2; exit 1; }
info() { echo "burner: $*"; }

[ -n "${HOME:-}" ] || [ -n "${BURNER_DIR:-}" ] || die "neither HOME nor BURNER_DIR is set."
command -v tar >/dev/null 2>&1 || die "tar not found. Install tar and re-run."

fetch() {
  # fetch URL OUTFILE
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL -o "$2" "$1"
  elif command -v wget >/dev/null 2>&1; then
    wget -q -O "$2" "$1"
  else
    die "need curl or wget to download burner."
  fi
}

if [ -e "$DEST" ] && [ ! -d "$DEST" ]; then
  die "$DEST exists and is not a directory. Move it aside or set BURNER_DIR."
fi

if [ -d "$DEST/.git" ]; then
  command -v git >/dev/null 2>&1 || die "$DEST is a git checkout but git is not installed."
  info "updating existing checkout in $DEST (git pull --ff-only)..."
  git -C "$DEST" pull --ff-only \
    || die "git pull --ff-only failed in $DEST. Resolve local changes there and re-run."
elif [ -d "$DEST" ] && [ ! -f "$DEST/$MARKER" ] && [ -n "$(ls -A "$DEST" 2>/dev/null)" ]; then
  die "$DEST exists and is not a git checkout. Move it aside, or set BURNER_DIR to another path, and re-run."
else
  TMPDIR_B="$(mktemp -d 2>/dev/null || mktemp -d -t burner)" || die "cannot create a temp dir."
  trap 'rm -rf "$TMPDIR_B"' EXIT
  info "downloading burner..."
  fetch "$TARBALL_URL" "$TMPDIR_B/burner.tar.gz" || die "download failed: $TARBALL_URL"
  tar -xzf "$TMPDIR_B/burner.tar.gz" -C "$TMPDIR_B" || die "could not extract the burner tarball."
  SRC="$TMPDIR_B/burner-master"
  [ -f "$SRC/install.sh" ] || die "unexpected tarball layout (no burner-master/install.sh)."
  mkdir -p "$DEST" || die "cannot create $DEST"
  # Copy contents (including dotfiles) into DEST.
  (cd "$SRC" && tar -cf - .) | (cd "$DEST" && tar -xf -) || die "could not copy files into $DEST"
  : > "$DEST/$MARKER" || die "cannot write $DEST/$MARKER"
  # GitHub tarballs carry their commit id; `burner version` reports it.
  python3 -c 'import sys, tarfile; print(tarfile.open(sys.argv[1]).pax_headers.get("comment", ""))' \
    "$TMPDIR_B/burner.tar.gz" > "$DEST/.burner-version" 2>/dev/null || rm -f "$DEST/.burner-version"
  info "extracted to $DEST"
fi

[ -f "$DEST/install.sh" ] || die "$DEST/install.sh not found."
info "running $DEST/install.sh..."
bash "$DEST/install.sh" || die "$DEST/install.sh failed (see output above)."

cat <<EOF

burner is ready in $DEST

Add it to your PATH (put both lines in your shell rc to keep them):

  export BURNER_WORKSPACE="$DEST"
  export PATH="$DEST/bin:\$PATH"

Next step: pair the phone (a human, once, about 10 minutes):

  burner setup

Agent guide: https://useburner.si/skill.md
EOF
