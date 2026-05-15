# История изменений

## Текущее

- Репозиторий и GitHub Pages переведены на русский как основной язык.
- Добавлены отдельные Instagram и Facebook/Meta rule-set'ы для стабильности iOS-приложения.
- DNS переключен на plain/system вместо DoH-over-IP, чтобы избежать падений DNS tunnel в Shadowrocket на macOS/iOS.
- Telegram домены идут через `Proxy` с `force-remote-dns`.
- Telegram IP-сети вынесены в `rules/telegram-ips.list`.
- Основной `RULE-SET` профиль остается рекомендуемым файлом для импорта.

## Первый релиз

- RoscomVPN routing sources конвертируются в Shadowrocket-compatible конфиги.
- Опубликованы expanded и process-rule отладочные варианты.
- Добавлен workflow для периодической пересборки на GitHub Actions.
