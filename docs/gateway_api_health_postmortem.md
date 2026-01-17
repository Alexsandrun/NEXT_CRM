# Postmortem: 404 на /api/health в gateway

## Заголовок
Gateway возвращал 404 для `/api/health` вместо корректного ответа core.

## Окружение
Локально через docker compose: `gateway` (nginx) опубликован на `localhost:8088`, `core` слушает `:8000`.

## Симптом
`curl http://localhost:8088/api/health` отдавал `HTTP 404 {"detail":"Not Found"}`, хотя `core` на `/health` отвечал успешно.

## Шаги воспроизведения
1. Поднять сервисы:
   - docker compose up -d --build core content gateway
2. Проверить шлюз:
   - curl -v http://localhost:8088/api/health
3. Проверить core напрямую:
   - docker compose exec core python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/health').read())"

## Корневая причина
Nginx проксировал путь с префиксом `/api/` в core без удаления префикса, поэтому core получал `/api/health`,
а в приложении маршруты зарегистрированы как `/health`.

Дополнительно: использование `proxy_pass` с переменными усложняло поведение формирования upstream URI.

## Что исправлено
Обновлён конфиг gateway (dev.conf):
- Добавлен rewrite, чтобы удалить префикс `/api/` перед проксированием:
  - rewrite ^/api/?(.*)$ /$1 break;
- Упрощён proxy_pass на core (явный `http://core:8000`), чтобы прокси отправлял переписанный URI.

Перезапуск:
- docker compose exec gateway nginx -t
- docker compose restart gateway

## Проверка исправления
- curl http://localhost:8088/api/health
Ожидаемо: HTTP 200 и JSON от core, например:
{"status":"ok","service":"core","env":"dev","log_mode":"normal"}

## Рекомендации / follow-up
- Добавить проверку в CI: поднять core+gateway и дернуть `/api/health` и `/api/openapi.json`.
- Опционально: добавить алиас `/api/health` на стороне core для совместимости.
