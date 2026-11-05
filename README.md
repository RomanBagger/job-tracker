# Job Tracker

Приложение для Mac: читает вашу Gmail-почту, находит письма о вакансиях (DevOps / Platform / SRE и любые другие),
определяет компанию и этап (отклик → HR → Tech → Final → отказ / оффер), ставит каждой компании рейтинг S–D
и показывает всё в окне приложения и в файле `job_search.xlsx`.

Всё хранится у вас на компьютере. Почта только читается (права `gmail.readonly`).

---

## Для человека: установка за 15 минут

### Что понадобится
| Что | Зачем | Цена |
|---|---|---|
| Mac | приложение собирается под macOS | — |
| Python 3 | запуск (проверьте в Терминале: `python3 --version`; нет — установите с python.org) | бесплатно |
| Gmail-аккаунт | откуда читать письма | бесплатно |
| Google Cloud | разрешение на чтение почты (один раз) | бесплатно |
| Ключ Anthropic (Claude API) | разбор писем и рейтинг компаний | платно, хватит $5–10 |

### Шаги
**1. Скачайте и соберите**
```
git clone https://github.com/RomanBagger/job-tracker.git
cd job-tracker
./build_app.sh
```
Появится приложение **Job Tracker.app**.

**2. Ключ Anthropic**
1. <https://console.anthropic.com> → Billing → пополните на $5–10.
2. Settings → API Keys → Create Key → скопируйте ключ (`sk-ant-...`).
3. В папке проекта выполните `cp .env.example .env` и вставьте ключ в `.env`.

**3. Доступ к Gmail (Google Cloud)** — подробно с пояснениями: **[SETUP_GOOGLE.md](SETUP_GOOGLE.md)**. Коротко:
1. <https://console.cloud.google.com> → создайте проект → включите **Gmail API**.
2. OAuth consent screen: тип External, добавьте **свой Gmail в Test users**, затем нажмите **Publish app**.
3. Credentials → Create credentials → OAuth client ID → **Desktop app** → скачайте JSON.
4. Положите файл в папку проекта под именем **`credentials.json`**.

**4. Запуск**
Откройте **Job Tracker.app** (можно перетащить в Dock) → нажмите **«Обновить таблицу (почта)»**.
Откроется браузер с входом в Google. Если появится «Google hasn't verified this app» — **Advanced → Go to job-tracker (unsafe)** и разрешите доступ.
Подождите: первый проход по почте занимает несколько минут.

### Кнопки
- **Обновить таблицу (почта)** — читает новые письма, обновляет таблицу.
- **Обновить рейтинг компаний** — переоценивает все компании (долго и платно).
- **Открыть Excel** — открывает `job_search.xlsx`.

### Если что-то не работает
| Симптом | Решение |
|---|---|
| `403 access_denied` при входе в Google | Ваш email не добавлен в **Test users** или приложение не опубликовано (шаг 3.2) |
| Просит войти каждую неделю | Не нажали **Publish app**; после публикации удалите `token.json` и войдите заново |
| `credentials.json not found` | Файл не в корне проекта или называется `client_secret_….json` — переименуйте |
| Ошибка Anthropic 401 / credit | Проверьте ключ в `.env` и баланс |

Автозапуск по расписанию и ручные оценки компаний — внизу, в разделе «Дополнительно».

---

## Для агента (Claude Code)

Человек скачал репозиторий и хочет установить приложение с вашей помощью. Скажите ему вставить в Claude Code:

> Склонируй https://github.com/RomanBagger/job-tracker, прочитай CLAUDE.md и помоги мне установить приложение по шагам.

Инструкция для агента лежит в **[CLAUDE.md](CLAUDE.md)**: что проверить, что сделать самому, а что только пользователь может сделать в браузере.

---

## Дополнительно

**Автозапуск (cron)**, `crontab -e`:
```
0 8 * * 1  /путь/к/job-tracker/run.sh            # письма — по понедельникам
0 9 1 * *  /путь/к/job-tracker/run.sh --rerate   # рейтинг компаний старше 30 дней — 1-го числа
```
Лог: `data/sync.log`. Mac должен быть включён.

**Ручные оценки компаний** — файл `tier_overrides.json`:
`{"Google": {"tier": "S", "category": "product", "rationale": "..."}}`. Такие компании не переоцениваются автоматически.

**Настройки** в `.env`: `BACKFILL_MONTHS` (за сколько месяцев читать почту при первом запуске, по умолчанию 24; для пробы поставьте 3).

**Как устроено:** `jobtracker/gmail.py` (чтение Gmail) → `classify.py` (разбор писем Claude Haiku) → `tiers.py` (рейтинг Claude Sonnet + веб-поиск) → SQLite `data/jobs.db` → `report.py` (xlsx) · `app.py` + `ui.html` (окно).

**Что не публикуется (в `.gitignore`):** `.env`, `credentials.json`, `token.json`, `data/`, `job_search.xlsx`.
