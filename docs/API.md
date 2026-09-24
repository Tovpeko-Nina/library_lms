# HTTP API

Базовый адрес REST API: `/api/v1`. Интерактивная документация доступна по `/docs`, OpenAPI JSON — по `/openapi.json`.

## Аутентификация и ошибки

После `POST /api/v1/auth/login` клиент передаёт JWT в заголовке `Authorization: Bearer <access_token>`.

Коды ответа: `200` — успех; `400` — нарушено предметное правило; `401` — недействительная аутентификация; `403` — недостаточно прав; `404` — сущность не найдена; `422` — ошибка Pydantic-валидации. Ошибки FastAPI имеют вид `{"detail": "описание"}`.

## Служебные адреса

| Метод | Путь | Назначение |
|---|---|---|
| GET | `/health` | доступность приложения и соединения с PostgreSQL |
| GET | `/api/v1/health` | та же проверка через API-префикс |

## Аутентификация

| Метод | Путь | Доступ | Назначение |
|---|---|---|---|
| POST | `/auth/register` | публичный | регистрация читателя |
| POST | `/auth/login` | публичный | получение JWT |
| POST | `/auth/logout` | публичный | информационный stateless-logout |

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"login":"admin","password":"your-local-password"}'
```

## Пользователи

| Метод | Путь | Роли | Назначение |
|---|---|---|---|
| GET/PUT | `/users/me` | авторизованные | получить/изменить профиль |
| PUT | `/users/me/password` | авторизованные | сменить пароль после проверки текущего |
| GET | `/users` | ADMIN, LIBRARIAN | список пользователей |
| GET | `/users/{user_id}` | ADMIN, LIBRARIAN | карточка пользователя |
| POST | `/users/librarian` | ADMIN | создать библиотекаря |
| PUT | `/users/{user_id}/verify` | ADMIN, LIBRARIAN | верифицировать читателя |
| DELETE | `/users/{user_id}` | ADMIN | деактивировать пользователя |
| DELETE | `/users/{user_id}/permanent` | ADMIN | окончательно удалить неиспользуемую деактивированную запись |

## Книги и экземпляры

| Метод | Путь | Роли | Назначение |
|---|---|---|---|
| GET | `/books` | публичный | каталог, фильтры, пагинация |
| GET | `/books/genres` | публичный | жанры |
| GET | `/books/search?q=...` | публичный | поиск |
| GET | `/books/popular` | публичный | популярные издания |
| POST | `/books` | ADMIN, LIBRARIAN | создать издание |
| GET | `/books/{book_id}` | публичный | получить издание |
| PUT/PATCH | `/books/{book_id}` | ADMIN, LIBRARIAN | изменить издание |
| DELETE | `/books/{book_id}` | ADMIN, LIBRARIAN | удалить издание |
| POST/GET | `/books/{book_id}/copies` | запись: сотрудники; чтение: публично | добавить/получить экземпляры |
| PATCH | `/copies/{copy_id}/status` | ADMIN, LIBRARIAN | изменить состояние |
| DELETE | `/copies/{copy_id}` | ADMIN, LIBRARIAN | списать экземпляр |

Параметры каталога: `genre`, `author`, `branch`, `available`, `search`, `page`, `limit`.

## Выдачи, бронирования и штрафы

| Метод | Путь | Роли | Назначение |
|---|---|---|---|
| POST | `/loans/borrow` | ADMIN, LIBRARIAN | оформить выдачу |
| POST | `/loans/return` | ADMIN, LIBRARIAN | оформить возврат |
| POST | `/loans/renew` | авторизованные | продлить выдачу |
| GET | `/loans` | ADMIN, LIBRARIAN | история выдач |
| GET | `/loans/me` | STUDENT, EMPLOYEE | собственные выдачи |
| GET | `/loans/active` | ADMIN, LIBRARIAN | активные выдачи |
| GET | `/loans/overdue` | ADMIN, LIBRARIAN | просрочки |
| POST | `/reservations` | STUDENT, EMPLOYEE | бронь или очередь |
| GET | `/reservations` | ADMIN, LIBRARIAN | активные брони и очередь читателей |
| GET | `/reservations/me` | STUDENT, EMPLOYEE | собственные брони |
| DELETE | `/reservations/{id}` | авторизованные | отменить бронь |
| POST | `/reservations/{id}/fulfill` | ADMIN, LIBRARIAN | оформить бронь как выдачу |
| GET | `/fines/me` | STUDENT, EMPLOYEE | собственные штрафы |
| GET | `/fines` | ADMIN, LIBRARIAN | все штрафы |
| GET | `/fines/unpaid` | ADMIN, LIBRARIAN | неоплаченные штрафы |
| POST | `/fines/pay/{fine_id}` | читатель, LIBRARIAN | отметить оплату |
| GET | `/fines/calculate/{loan_id}` | ADMIN, LIBRARIAN | сумма по выдаче |

## Уведомления, отчёты и настройки

| Метод | Путь | Роли | Назначение |
|---|---|---|---|
| GET | `/notifications` | авторизованные | уведомления пользователя |
| PATCH | `/notifications/{id}/read` | авторизованные | отметить прочитанным |
| POST | `/notifications/send-overdue` | ADMIN, LIBRARIAN | напоминания о просрочках |
| GET | `/reports/inventory` | ADMIN, LIBRARIAN | состояние фонда |
| GET | `/reports/usage` | ADMIN, LIBRARIAN | использование библиотеки |
| GET | `/reports/popular` | публичный | популярные книги |
| GET | `/reports/borrowing-trends` | ADMIN, LIBRARIAN | выдачи по месяцам |
| GET | `/reports/overdue` | ADMIN, LIBRARIAN | отчёт о просрочках |
| GET | `/reports/branch/{branch}` | ADMIN, LIBRARIAN | фонд филиала |
| GET | `/settings` | публичный | правила выдачи |
| PUT | `/settings` | ADMIN | изменить правила |

Точные тела запросов и проверяемые поля представлены в OpenAPI UI `/docs`.
