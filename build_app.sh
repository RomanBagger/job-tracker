#!/bin/zsh
# Собирает "Job Tracker.app" (нативное окно). Запуск: ./build_app.sh
set -e
cd "$(dirname "$0")"
ROOT="$(pwd)"
[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt

APP="Job Tracker.app"
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
.venv/bin/python packaging/make_icon.py "$APP/Contents/Resources/AppIcon.icns"
rm -rf "$APP/Contents/Resources/AppIcon.iconset" "$APP/Contents/Resources/AppIcon.png"

cat > "$APP/Contents/MacOS/JobTracker" <<LAUNCH
#!/bin/zsh
cd "$ROOT" || { osascript -e 'display alert "Job Tracker" message "Папка проекта не найдена: $ROOT. Запустите ./build_app.sh заново."'; exit 1; }
mkdir -p data
exec .venv/bin/python -m jobtracker.app >> data/app.log 2>&1
LAUNCH
chmod +x "$APP/Contents/MacOS/JobTracker"

cat > "$APP/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleName</key><string>Job Tracker</string>
  <key>CFBundleDisplayName</key><string>Job Tracker</string>
  <key>CFBundleIdentifier</key><string>local.jobtracker.app</string>
  <key>CFBundleExecutable</key><string>JobTracker</string>
  <key>CFBundleIconFile</key><string>AppIcon</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleShortVersionString</key><string>1.0</string>
  <key>LSMinimumSystemVersion</key><string>12.0</string>
  <key>NSHighResolutionCapable</key><true/>
</dict></plist>
PLIST
touch "$APP"
echo "Готово: $ROOT/$APP"
echo "Перетащите его в Dock или в «Программы» (проект при этом должен остаться на месте)."
