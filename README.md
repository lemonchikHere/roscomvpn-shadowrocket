# RoscomVPN Routing for Shadowrocket

Shadowrocket-совместимая сборка RoscomVPN DEFAULT routing для macOS/iOS.

Готовая маршрутизация под Shadowrocket на macOS, собранная из:

- `hydraponique/roscomvpn-routing` DEFAULT-профиля для Mihomo
- `hydraponique/roscomvpn-geosite` текстовых geosite-источников
- `hydraponique/roscomvpn-geoip` текстового `direct.txt`/`private.txt`
- небольшого Shadowrocket-аддона для Discord, потому что в RoscomVPN DEFAULT Discord задан через Windows process rules

## Файлы

- `roscomvpn-shadowrocket.conf` - основной импортируемый профиль через `RULE-SET`. Ставь его первым.
- `roscomvpn-shadowrocket-expanded.conf` - тот же профиль, но развернутый в один большой файл для отладки.
- `roscomvpn-shadowrocket-with-process.conf` - вариант с `PROCESS-NAME`/`PROCESS-NAME-REGEX` из апстрима. Используй только если твоя версия Shadowrocket принимает process rules.
- `rules/*.list` - разложенные rule-set файлы для проверки/хостинга.
- `build_shadowrocket.py` - генератор. Перезапускай его, чтобы подтянуть свежие списки.

## Быстрые ссылки

- Основной конфиг: `https://raw.githubusercontent.com/lemonchikHere/roscomvpn-shadowrocket/main/roscomvpn-shadowrocket.conf`
- Развернутый конфиг: `https://raw.githubusercontent.com/lemonchikHere/roscomvpn-shadowrocket/main/roscomvpn-shadowrocket-expanded.conf`
- Вариант с process rules: `https://raw.githubusercontent.com/lemonchikHere/roscomvpn-shadowrocket/main/roscomvpn-shadowrocket-with-process.conf`

## Автообновление

GitHub Actions запускает `build_shadowrocket.py` каждые 6 часов и вручную через `workflow_dispatch`.
Если upstream-списки реально изменились, action коммитит обновленные `*.conf` и `rules/*.list`.
Если изменений нет, коммит не создается.

## Логика

- `DIRECT`: приватные сети, RU/BY IP, RU/банковские/локальные домены, Apple, Microsoft, Steam/Epic/Riot/EFT/FaceIT, Twitch, Pinterest, torrent-клиенты/домены.
- `PROXY`: YouTube, Telegram, GitHub, Google Play, Twitch ads, Discord domain addon, весь остальной интернет.
- `BLOCK`: рекламные категории, Windows telemetry, весь IPv6 как в апстриме против утечек.
- QUIC/HTTP3 UDP 443 блокируется правилом `AND,((PROTOCOL,UDP),(DST-PORT,443)),REJECT-NO-DROP`, чтобы YouTube и Google чаще откатывались на TCP.

## Как поставить в Shadowrocket на Mac

1. Открой Shadowrocket.
2. `Config` -> импорт из файла/iCloud Drive.
3. Выбери `roscomvpn-shadowrocket.conf`.
4. Включи режим `Rule`.
5. Убедись, что твой рабочий VPN/proxy node выбран как основной `PROXY`.

Важно: этот файл не содержит сам VPN-узел/подписку. Это только маршрутизация. Если Shadowrocket при импорте создал отдельный пустой профиль без нод, добавь туда свою подписку/сервер или перенеси секции `[General]` и `[Rule]` в уже рабочий профиль.

Если после импорта Shadowrocket ругается на правило QUIC, открой конфиг и закомментируй строку:

```conf
AND,((PROTOCOL,UDP),(DST-PORT,443)),REJECT-NO-DROP
```

## Обновление

```bash
python3 build_shadowrocket.py
```

Генератор не трогает твои proxy nodes. Он собирает только маршрутизацию.
