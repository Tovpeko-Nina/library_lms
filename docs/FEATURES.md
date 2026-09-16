# Соответствие ТЗ

- USERS: регистрация, вход, профили, роли ADMIN/LIBRARIAN/STUDENT/EMPLOYEE, верификация и деактивация.
- BOOKS: каталог, поиск/фильтры, карточка книги, CRUD для сотрудников.
- BOOK_COPIES: физические экземпляры, филиалы, инвентарные номера и статусы AVAILABLE/ISSUED/RESERVED/LOST/DAMAGED.
- LOANS: выдача, возврат, продление, история, активные и просроченные выдачи.
- FINES: OVERDUE/LOST_BOOK/DAMAGED_BOOK, расчёт, оплата.
- RESERVATIONS + BOOK_QUEUE: бронирование доступного экземпляра и очередь при отсутствии экземпляров.
- NOTIFICATIONS: уведомления, отметка прочитанным, ручная отправка напоминаний о просрочках.
- BORROWING_POLICY: лимит книг, срок, продления, ставка штрафа, штрафы за потерю/повреждение и льготные дни.
- INVENTORY_REPORTS / USAGE_REPORTS: отчёты по фонду, филиалам, популярности, тенденциям, просрочкам и штрафам.
- INVENTORY_LOG / AUDIT_LOG / FTS5: предусмотрены таблицы и инфраструктура для журналов и полнотекстового поиска.

## Web-интерфейс

`/login`, `/register`, `/books`, `/books/{id}`, `/dashboard`, `/my-loans`, `/profile`, `/notifications`, `/fines`, `/admin`, `/admin/users`, `/admin/books`, `/admin/loans`, `/reports`, `/settings`.

REST API доступен по `/api/v1`, документация FastAPI — `/docs`.
