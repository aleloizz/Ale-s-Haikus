#!/usr/bin/env bash
# Safe git-filter-repo purge script
# WARNING: This rewrites history. Make a full backup & inform collaborators.

set -euo pipefail

echo "Ensure you have a backup and all collaborators are informed."
read -p "Continue? (y/N) " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
  echo "Aborted."
  exit 1
fi

# Make a bundle backup of the repo
git bundle create ../repo-backup.bundle --all
echo "Backup created at ../repo-backup.bundle"

# Remove sensitive paths
git filter-repo --invert-paths \
  --path aleshaikus/Ale-s-Haikus/instance/poems.db \
  --path aleshaikus/Ale-s-Haikus/latest.dump \
  --path aleshaikus/Ale-s-Haikus/backup/ \
  --force

echo "History rewritten. Run 'git push --force --all' and 'git push --force --tags' to update remote."