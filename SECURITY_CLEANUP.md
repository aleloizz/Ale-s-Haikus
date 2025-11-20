# Implemebtazioni di sicurezza consigliate da hexstrike

Sensitive files detected (remove from repo and purge history):
- [`aleshaikus/Ale-s-Haikus/instance/poems.db`](aleshaikus/Ale-s-Haikus/instance/poems.db:1)
- [`aleshaikus/Ale-s-Haikus/latest.dump`](aleshaikus/Ale-s-Haikus/latest.dump:1)
- [`aleshaikus/Ale-s-Haikus/backup/`](aleshaikus/Ale-s-Haikus/backup/:1)
- [`aleshaikus/Ale-s-Haikus/backup/app_old.py`](aleshaikus/Ale-s-Haikus/backup/app_old.py:10)

Recommended .gitignore (put this at repo root `aleshaikus/Ale-s-Haikus/.gitignore`):

```text
# Ignore instance DB and dumps
instance/*.db
*.dump
latest.dump

# Ignore backups and generated artifacts
backup/

# Environment files and secrets
.env
*.env

# Python artifacts
__pycache__/
*.py[cod]

# OS and editor files
.DS_Store
*.swp
```

Quick history-clean steps (example):
```bash
git rm --cached aleshaikus/Ale-s-Haikus/instance/poems.db
git rm --cached aleshaikus/Ale-s-Haikus/latest.dump
git commit -m "Remove sensitive artifacts"
# Use BFG or git filter-repo to purge from history:
# bfg --delete-files '*.dump' --delete-files 'poems.db'
```

Action items to complete immediately:
- Remove files from repo and purge history (BFG/git-filter-repo).
- Add the .gitignore rules above.
- Rotate secrets and remove fallback SECRET_KEYs in code: see [`aleshaikus/Ale-s-Haikus/config/app_config.py`](aleshaikus/Ale-s-Haikus/config/app_config.py:7) and [`aleshaikus/Ale-s-Haikus/backup/app_old.py`](aleshaikus/Ale-s-Haikus/backup/app_old.py:10).
- Verify no other credentials exist (search .env, config, backups).

If you want, I can prepare the exact `.gitignore` file in the repo and a safe git-filter-repo command sequence to purge history next.