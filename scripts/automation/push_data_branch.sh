#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <commit-message>" >&2
  exit 2
fi

commit_message="$1"

# Ensure git identity
if ! git config --local user.email >/dev/null; then
  git config --local user.email "action@github.com"
fi
if ! git config --local user.name >/dev/null; then
  git config --local user.name "GitHub Action"
fi

if [ -z "$(git status --porcelain data/)" ]; then
  echo "No changes to commit"
  exit 0
fi

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

mkdir -p "$tmp_dir/data"
rsync -a data/ "$tmp_dir/data/"

# Clean working tree changes so we can switch branches
if git ls-files --error-unmatch data >/dev/null 2>&1; then
  git checkout -- data/
fi
git clean -fd data/

if git show-ref --verify --quiet refs/remotes/origin/data; then
  git fetch origin data:data
  git checkout data
else
  echo "Remote data branch not found, creating from main"
  git checkout -b data
fi

rm -rf data
mv "$tmp_dir/data" data

git add data/

if git diff --cached --quiet; then
  echo "No changes to commit on data branch"
  exit 0
fi

git commit -m "$commit_message"
git push --force origin data

echo "Successfully pushed to data branch"
