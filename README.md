# ValutaTrade Hub — finalproject_elizarov_M25-555

CLI-приложение для регистрации пользователей, ведения виртуального портфеля валют (фиат + крипто),
покупки/продажи и просмотра курсов. Курсы хранятся в локальном кеше `data/rates.json` и считаются актуальными
только в пределах TTL.

## Идея проекта
Проект состоит из двух частей:
- Core Service: CLI + бизнес-логика (пользователи, портфели, сделки).
- Parser Service: обновление курсов валют из публичных API и сохранение в `data/rates.json`.

## Технологии
- Poetry: зависимости, сборка пакета, запуск через `poetry run project`.
- Ruff: линтер (PEP8).
- JSON: хранение данных (`users.json`, `portfolios.json`, `rates.json`).
- prettytable: форматированный вывод таблиц в CLI.
- requests: запросы к API в Parser Service.

## Структура проекта
finalproject_elizarov_M25-555/
├── pyproject.toml
├── Makefile
├── .gitignore
├── README.md
├── main.py
├── data/
│   ├── users.json
│   ├── portfolios.json
│   └── rates.json
└── valutatrade_hub/
    ├── __init__.py
    ├── logging_config.py
    ├── decorators.py
    ├── core/
    │   ├── exceptions.py
    │   ├── session.py
    │   ├── utils.py
    │   ├── currencies.py
    │   ├── models.py
    │   └── usecases.py
    ├── infra/
    │   ├── settings.py
    │   └── database.py
    ├── cli/
    │   └── interface.py
    └── parser_service/
        ├── config.py
        ├── api_clients.py
        ├── storage.py
        └── updater.py

## Установка
make install

## Запуск
make project

## Команды CLI (примеры)
1) Регистрация:
project register --username alice --password 1234

2) Вход:
project login --username alice --password 1234

3) Показ портфеля:
project show-portfolio
project show-portfolio --base USD

4) Покупка валюты:
project buy --currency BTC --amount 0.05

5) Продажа валюты:
project sell --currency BTC --amount 0.01

6) Получение курса:
project get-rate --from USD --to BTC

7) Обновление курсов (Parser Service):
project update-rates
project show-rates

## Данные (JSON)
- data/users.json: список пользователей (user_id, username, hashed_password, salt, registration_date)
- data/portfolios.json: портфели (user_id + wallets)
- data/rates.json: кеш курсов + last_refresh + source

## TTL курсов и кеш
- Курсы считаются свежими только в пределах TTL.
- TTL задаётся через переменную окружения VALUTATRADE_RATESTTLSECONDS (или используется значение по умолчанию 300 секунд).
- Если кеш устарел, команда get-rate просит обновить курсы через update-rates.

## Parser Service и ключи API
Parser Service пытается получить курсы из внешних API.
Если ключ для фиатного API не задан, используется безопасная заглушка (чтобы приложение работало на проверке).

Переменные окружения (опционально):
- VALUTATRADE_EXCHANGERATE_API_KEY=...

## Логи
Логи пишутся в файл logs/valutatrade.log (ротация включена).

## Проверка линтера
make lint

## Демо (asciinema или GIF)
Добавить ссылку на демо после записи:
- полный цикл: register → login → buy → sell → show-portfolio → get-rate
- отдельно: update-rates → show-rates
- отдельно: ошибки (недостаточно средств, неизвестная валюта)
