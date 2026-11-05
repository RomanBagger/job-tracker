# Подключение Gmail через Google Cloud (один раз, ~10 минут)

Приложение читает почту через Gmail API с правом **только на чтение** (`gmail.readonly`): отправлять и удалять письма оно не может.
Нужны два файла в папке проекта: `credentials.json` (доступ к Gmail) и `.env` (ключ Anthropic).

## 1. Проект и Gmail API
1. Откройте <https://console.cloud.google.com> и войдите в тот Google-аккаунт, чью почту будете читать.
2. Вверху нажмите на выбор проекта → **New project** → имя `job-tracker` → **Create**. Убедитесь, что проект выбран.
3. Меню **APIs & Services → Library** → найдите **Gmail API** → **Enable**.

## 2. Экран согласия (OAuth consent screen)
1. **APIs & Services → OAuth consent screen** (в новом интерфейсе: **Google Auth Platform**).
2. Тип пользователей **External**, название `job-tracker`, ваш email в «User support» и «Developer contact» → Save.
3. **Audience → Test users → Add users** → впишите **свой Gmail** → **Save**.
   Без этого вход закончится ошибкой `403 access_denied` («приложение не прошло проверку Google»).
4. Рекомендуется нажать **Publish app** (статус *In production*). Проверка Google для личного использования не нужна.
   Пока статус *Testing*, токен живёт всего 7 дней и придётся заново входить раз в неделю.

## 3. Ключ OAuth
1. **APIs & Services → Credentials → Create credentials → OAuth client ID**.
2. Тип приложения **Desktop app**, имя любое → **Create**.
3. Нажмите **Download JSON** и сохраните файл как **`credentials.json`** в корне проекта (рядом с `run.sh`).

## 4. Ключ Anthropic
1. <https://console.anthropic.com> → **Billing**: пополнить баланс ($5–10 хватит надолго).
2. **Settings → API Keys → Create Key**, скопируйте ключ (`sk-ant-...`, показывается один раз).
3. Скопируйте `.env.example` в `.env` и вставьте ключ:
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   BACKFILL_MONTHS=3
   ```
   `BACKFILL_MONTHS` — за сколько месяцев читать почту при первом запуске (для пробы 3, для полной истории 24).

## 5. Первый вход
Откройте приложение **Job Tracker** и нажмите **«Обновить таблицу (почта)»**. Откроется браузер с окном Google:
1. Выберите свой аккаунт.
2. Если видите «Google hasn’t verified this app» — нажмите **Advanced → Go to job-tracker (unsafe)**. Это ваше собственное приложение, предупреждение нормально.
3. Разрешите доступ на чтение почты.

После этого создаётся `token.json`, и вход больше не нужен.

## Частые проблемы
| Симптом | Что делать |
|---|---|
| `403 access_denied` при входе | Вашего email нет в **Test users** (шаг 2.3) или приложение не опубликовано. |
| Снова просит войти через неделю | Приложение в статусе *Testing*: нажмите **Publish app** и удалите `token.json`. |
| `credentials.json` not found | Файл лежит не в корне проекта или назван иначе (скачивается как `client_secret_…json`). |
| `invalid_grant` / токен не обновляется | Удалите `token.json` и войдите заново. |
| Ошибка Anthropic 401/credit | Проверьте ключ в `.env` и баланс в консоли Anthropic. |
