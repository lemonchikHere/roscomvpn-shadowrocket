<p align="center">
  <strong>RoscomVPN Routing for Shadowrocket</strong>
</p>

<p align="center">
  Готовая маршрутизация для Shadowrocket на macOS и iOS, собранная из источников RoscomVPN.
  <br>
  RU/BY и локальные сервисы идут напрямую. YouTube, Telegram, Instagram, GitHub, Discord и остальной внешний трафик идут через выбранный `Proxy`.
</p>

<p align="center">
  <a href="https://raw.githubusercontent.com/lemonchikHere/roscomvpn-shadowrocket/main/roscomvpn-shadowrocket.conf"><strong>Скопировать основной конфиг</strong></a>
  ·
  <a href="https://lemonchikhere.github.io/roscomvpn-shadowrocket/">Красивая страница</a>
  ·
  <a href="#установка">Установка</a>
  ·
  <a href="#если-что-то-не-работает">Если что-то не работает</a>
</p>

---

## Какой файл ставить

Ставь основной легкий профиль:

```text
https://raw.githubusercontent.com/lemonchikHere/roscomvpn-shadowrocket/main/roscomvpn-shadowrocket.conf
```

Не начинай с `roscomvpn-shadowrocket-expanded.conf`, если просто хочешь пользоваться VPN. `expanded` нужен для отладки: он огромный и полностью разворачивает все правила в один файл. Основной конфиг маленький, читабельный и подтягивает `rules/*.list` через `RULE-SET`.

## Что делает конфиг

| Маршрут | Что туда попадает |
| --- | --- |
| `DIRECT` | Приватные сети, RU/BY IP, российские сервисы, банки, Apple, Microsoft, Steam, Epic, Riot, Escape from Tarkov, Faceit, Twitch, Pinterest, torrent-клиенты и локальные домены. |
| `Proxy` | YouTube, Telegram, Instagram, Facebook/Meta, GitHub, Google Play, Twitch ads, Discord и весь остальной трафик, который не совпал с direct-правилами. |
| `REJECT-DROP` | Рекламные категории, Windows telemetry и IPv6 leak guard. |

Telegram покрыт двумя слоями: домены идут через `Proxy` с `force-remote-dns`, а известные Telegram IP-сети идут через `Proxy` с `no-resolve`.

Instagram и Facebook/Meta вынесены отдельными rule-set'ами выше `direct-ips`, чтобы мобильное приложение не разваливалось на CDN и Meta-инфраструктуре.

DNS намеренно обычный/system:

```conf
dns-server = system,77.88.8.8,1.1.1.1,8.8.8.8
fallback-dns-server = system,1.1.1.1,8.8.8.8
```

Так мы избегаем бага Shadowrocket на macOS/iOS, когда DoH-over-IP вроде `https://77.88.8.8/dns-query` закрывается или таймаутится и ломает резолвинг вообще для всех приложений.

## Установка

1. Открой Shadowrocket.
2. Импортируй основной URL выше.
3. Включи режим маршрутизации `Rule`.
4. Выбери свой рабочий сервер/подписку как активный `Proxy`.
5. Удали старые импортированные копии этого конфига, если Shadowrocket продолжает использовать закешированный `.db`.

Важно: репозиторий содержит только маршрутизацию. Тут нет VPN-серверов, подписок, ключей, VLESS/VMess/Reality-конфигов и любых приватных доступов.

## Файлы

| Файл | Для чего |
| --- | --- |
| `roscomvpn-shadowrocket.conf` | Основной импортируемый профиль. Ставь его. |
| `roscomvpn-shadowrocket-expanded.conf` | Полностью развернутый отладочный профиль, примерно 37k правил. |
| `roscomvpn-shadowrocket-with-process.conf` | Отладочный профиль с process rules из upstream. Используй только если твоя версия Shadowrocket принимает `PROCESS-NAME`. |
| `rules/*.list` | Rule-set файлы, которые основной профиль подтягивает по URL. |
| `build_shadowrocket.py` | Генератор, который пересобирает конфиги из upstream-источников. |
| `.github/workflows/update-config.yml` | Автосборка на GitHub Actions. Работает, когда Actions включены у репозитория/аккаунта. |

## Локальная пересборка

```bash
python3 build_shadowrocket.py
python3 -m py_compile build_shadowrocket.py
```

Генератор переписывает только маршрутизацию. Он не трогает твои proxy nodes.

## Автообновление

GitHub workflow настроен на запуск:

- вручную через `workflow_dispatch`
- каждые 6 часов
- после изменения `build_shadowrocket.py` или самого workflow

Если upstream-списки изменились, workflow коммитит обновленные `*.conf` и `rules/*.list`. Если изменений нет, новый коммит не создается.

## Если что-то не работает

| Симптом | Что проверить |
| --- | --- |
| Telegram не грузится | Переимпортируй основной профиль, не `expanded`. Проверь, что есть `rules/telegram-ips.list`, и удали старые закешированные профили. |
| Instagram на iPhone работает нестабильно | Переимпортируй последний основной профиль. В нем есть отдельные Instagram и Facebook/Meta rule-set'ы выше direct IP правил. |
| В логах `dns-query` timeout/closed | Переимпортируй свежий конфиг. Текущий профиль больше не использует DoH-over-IP. |
| YouTube нестабилен | Оставь QUIC rule включенным. Если твой Shadowrocket ругается на правило, закомментируй `AND,((PROTOCOL,UDP),(DST-PORT,443)),REJECT-NO-DROP`. |
| Вообще ничего не идет через VPN | Это routing-only профиль. Нужно выбрать реальный VPN/proxy node как `Proxy`. |
| Российские сервисы идут через VPN | Проверь, что используешь свежий профиль и что `rules/direct-ips.list` не содержит `no-resolve`. |

## Источники

- [hydraponique/roscomvpn-routing](https://github.com/hydraponique/roscomvpn-routing)
- [hydraponique/roscomvpn-geosite](https://github.com/hydraponique/roscomvpn-geosite)
- [hydraponique/roscomvpn-geoip](https://github.com/hydraponique/roscomvpn-geoip)
- [Shadowrocket default config](https://raw.githubusercontent.com/Shadowrocket/config/master/default.conf)
- [blackmatrix7 Shadowrocket rule lists](https://github.com/blackmatrix7/ios_rule_script/tree/master/rule/Shadowrocket)

## Примечание

Это compatibility layer для Shadowrocket. Upstream-списки принадлежат их авторам. Перед использованием в чувствительных окружениях лучше самостоятельно просмотреть сгенерированные правила.
