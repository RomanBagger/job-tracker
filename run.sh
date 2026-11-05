#!/bin/zsh
# Ежедневный запуск: ./run.sh  (cron вызывает его же)
cd "$(dirname "$0")"
[ -d .venv ] || { python3 -m venv .venv && .venv/bin/pip install -q -r requirements.txt; }
.venv/bin/python -m jobtracker.sync "$@" >> data/sync.log 2>&1
