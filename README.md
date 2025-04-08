# Secrets_service

**Secrets_service** — это простой API-сервис на FastAPI для хранения, получения, удаления "секретов" (одноразовых зашифрованных сообщений). Проект работает через Docker и использует PostgreSQL в качестве базы данных.
В качестве шифрования секрета используется библиотека **cryptography** (алгоритм **Fernet**), а для генерации ответного уникального ключа используется **uuid**.

---

## 🚀 Быстрый старт (через Docker)

1. Убедись, что у тебя установлен Docker и Docker Compose.
2. Клонируй проект (если ещё не сделал).
3. В корне проекта выполни:

```bash
docker-compose up --build
```
4. Готово!

Каждую минуту внутри приложения запускается планировщик AppSchedule, который: Проверяет все сохранённые секреты в базе данных и
удаляет те, у которых истёк срок действия (истекают по времени, указанному при создании или установленному по умолчанию);

Использует настройки из .env, в частности:
```bash
-TIME_TO_SAVE_SECONDS_DEFAULT=300  # значение по умолчанию, если клиент не задал время хранения.
```
Очистка работает автоматически в фоне на стороне сервера.

