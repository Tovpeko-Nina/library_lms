const LMS={
 token:()=>localStorage.getItem('lms_token'),
 async api(path,options={}){const headers={'Content-Type':'application/json',...(options.headers||{})};
if(this.token())headers.Authorization='Bearer '+this.token();
const r=await fetch('/api/v1'+path,{...options,headers});
let d={};
try{d=await r.json()}catch{}if(!r.ok)throw new Error(d.detail||d.message||'Ошибка запроса');
return d},
 toast(msg){const el=document.getElementById('toast');
if(!el)return;
el.textContent=msg;
el.classList.add('show');
setTimeout(()=>el.classList.remove('show'),3000)},
 async initNav(){const token=this.token();
const login=document.getElementById('nav-login'),reg=document.getElementById('nav-register'),out=document.getElementById('nav-logout'),name=document.getElementById('nav-user-name'),dash=document.getElementById('nav-dashboard'),admin=document.getElementById('nav-admin');
if(!token)return;
if(login)login.classList.add('hidden');
if(reg)reg.classList.add('hidden');
if(out)out.classList.remove('hidden');
try{const u=await this.api('/users/me');
const isStaff=['ADMIN','LIBRARIAN'].includes(u.role);
if(dash&&!isStaff){dash.classList.remove('hidden');dash.href='/dashboard';dash.textContent='Кабинет'}
if(admin&&isStaff){admin.classList.add('hidden')}
if(name){name.textContent=u.first_name+' '+u.last_name;
name.onclick=()=>location.href=isStaff?'/admin':'/dashboard';
name.style.cursor='pointer'}}catch{localStorage.removeItem('lms_token')}},
 async login(e){e.preventDefault();
try{const d=await this.api('/auth/login',{method:'POST',body:JSON.stringify({login:document.getElementById('login').value,password:document.getElementById('password').value})});
localStorage.setItem('lms_token',d.access_token);
location.href=['ADMIN','LIBRARIAN'].includes(d.role)?'/admin':'/dashboard'}catch(err){this.toast(err.message)}return false},
 async register(e){e.preventDefault();
const result=document.getElementById('register-result');
try{const d=await this.api('/auth/register',{method:'POST',body:JSON.stringify({login:reg_login.value,email:email.value,password:reg_password.value,first_name:first_name.value,last_name:last_name.value,role:role.value})});
result.classList.remove('hidden');
result.innerHTML='<b>Регистрация выполнена.</b><br>Аккаунт создан и ожидает верификации библиотекарем.<br><small>ID пользователя: '+d.user_id+'</small>';
document.getElementById('register-form').reset()}catch(err){result.classList.remove('hidden');
result.textContent=err.message}return false},
 logout(){localStorage.removeItem('lms_token');
location.href='/login'},
 need(){if(!this.token()){location.href='/login';
return false}return true},
 reserve(bookId){if(!this.need())return;
if(document.getElementById('reservation-modal'))return;
const modal=document.createElement('div');modal.id='reservation-modal';modal.className='modal-backdrop';
modal.innerHTML=`<div class="modal-card modal-card-compact" role="dialog" aria-modal="true" aria-labelledby="reservation-modal-title"><div class="modal-head"><div><div class="eyebrow">БРОНИРОВАНИЕ</div><h2 id="reservation-modal-title">Заказать книгу</h2><p>Если выпуск не важен, оставьте дополнительные поля пустыми.</p></div><button class="modal-close" type="button" aria-label="Закрыть" onclick="LMS.closeReservationForm()">×</button></div><form onsubmit="return LMS.submitReservation(event,'${bookId}')"><div class="form-grid"><label>Год издания <span class="optional">необязательно</span><input id="reserve_year" type="number" min="1000" max="9999" placeholder="Например, 2024"></label><label>Номер издания <span class="optional">необязательно</span><input id="reserve_edition" type="number" min="1" placeholder="Например, 2"></label></div><div class="reservation-hint">Без уточнений система выберет любой доступный экземпляр. Если подходящего выпуска сейчас нет, вы будете добавлены в очередь с указанными предпочтениями.</div><div class="modal-actions"><button class="btn btn-light" type="button" onclick="LMS.closeReservationForm()">Отмена</button><button id="reserve_submit" class="btn btn-primary" type="submit">Подтвердить заказ</button></div></form></div>`;
modal.addEventListener('click',event=>{if(event.target===modal)this.closeReservationForm()});modal.addEventListener('keydown',event=>{if(event.key==='Escape')this.closeReservationForm()});document.body.appendChild(modal);document.body.classList.add('modal-open');document.getElementById('reserve_year').focus()},
 closeReservationForm(){const modal=document.getElementById('reservation-modal');if(modal)modal.remove();document.body.classList.remove('modal-open')},
 async submitReservation(e,bookId){e.preventDefault();const year=document.getElementById('reserve_year').value;const edition=document.getElementById('reserve_edition').value;const button=document.getElementById('reserve_submit');button.disabled=true;button.textContent='Оформляем…';
try{const result=await this.api('/reservations',{method:'POST',body:JSON.stringify({book_id:bookId,publication_year:year?Number(year):null,edition_number:edition?Number(edition):null})});this.closeReservationForm();this.toast(result.queued?`Вы добавлены в очередь. Позиция: ${result.position}`:'Книга забронирована')}catch(error){this.toast(error.message);button.disabled=false;button.textContent='Подтвердить заказ'}return false},
 async renderDashboard(){if(!this.need())return;
try{const u=await this.api('/users/me');
if(['ADMIN','LIBRARIAN'].includes(u.role)){location.replace('/admin');return}
const loans=await this.api('/loans/me');
const fines=await this.api('/fines/me');
const notes=await this.api('/notifications');
const active=loans.filter(x=>!x.return_date);
document.getElementById('dashboard').innerHTML=`<div class="eyebrow">ЛИЧНЫЙ КАБИНЕТ</div><h1>Здравствуйте, ${u.first_name}!</h1><p class="lead">${u.is_verified?'Ваш аккаунт верифицирован.':'Аккаунт ожидает верификации.'}</p><div class="dashboard-grid"><div class="stat"><b>${active.length}</b><span>Активных книг</span></div><div class="stat"><b>${fines.filter(x=>!x.is_paid).length}</b><span>Неоплаченных штрафов</span></div><div class="stat"><b>${notes.filter(x=>!x.is_read).length}</b><span>Непрочитанных уведомлений</span></div></div><div class="panel" style="margin-top:22px"><h2>Быстрые действия</h2><div class="action-grid"><a class="action-card" href="/books"><b>Каталог</b><span>Найти книгу и посмотреть экземпляры</span></a><a class="action-card" href="/my-loans"><b>Мои книги</b><span>Сроки возврата и продление</span></a><a class="action-card" href="/notifications"><b>Уведомления</b><span>Системные сообщения</span></a><a class="action-card" href="/fines"><b>Штрафы</b><span>Проверить и оплатить начисления</span></a><a class="action-card" href="/profile"><b>Профиль</b><span>Личная информация</span></a>${['ADMIN','LIBRARIAN'].includes(u.role)?'<a class="action-card" href="/admin"><b>Управление</b><span>Пользователи, книги и выдачи</span></a>':''}</div></div>`}catch(e){this.toast(e.message)}},
 async renderProfile(){if(!this.need())return;
try{const u=await this.api('/users/me');
document.getElementById('profile-page').innerHTML=`<div class="panel"><form onsubmit="return LMS.saveProfile(event)"><div class="form-grid"><label>Имя<input id="p_first" value="${u.first_name||''}" required></label><label>Фамилия<input id="p_last" value="${u.last_name||''}" required></label><label>Телефон<input id="p_phone" value="${u.phone||''}"></label><label>Адрес<input id="p_address" value="${u.address||''}"></label><label>Факультет<input id="p_faculty" value="${u.faculty||''}"></label><label>Кафедра / отдел<input id="p_department" value="${u.department||''}"></label><label>Группа<input id="p_group" value="${u.group_name||''}"></label><label>Дата выпуска<input id="p_grad" type="date" value="${u.graduation_date||''}"></label></div><div style="margin-top:20px"><button class="btn btn-primary">Сохранить</button></div></form></div><div class="panel"><b>Роль:</b> ${u.role}<br><b>Статус:</b> ${u.is_verified?'Верифицирован':'Ожидает верификации'}<br><b>Дата регистрации:</b> ${u.registration_date||'—'}</div>`}catch(e){this.toast(e.message)}},
 async saveProfile(e){e.preventDefault();
try{await this.api('/users/me',{method:'PUT',body:JSON.stringify({first_name:p_first.value,last_name:p_last.value,phone:p_phone.value,address:p_address.value,faculty:p_faculty.value,department:p_department.value,group_name:p_group.value,graduation_date:p_grad.value||null})});
this.toast('Профиль обновлён')}catch(x){this.toast(x.message)}return false},
 async renderMyLoans(){if(!this.need())return;
try{const rows=await this.api('/loans/me');
document.getElementById('my-loans-page').innerHTML=rows.length?`<div class="list">${rows.map(l=>`<div class="list-item"><div><h3>${l.title}</h3><p>Экземпляр ${l.inventory_number||'—'} · ${l.branch||'—'}</p><p>Выдано: ${l.issue_date} · Вернуть до: <b>${l.due_date}</b></p></div><div>${l.return_date?'<span class="status">Возвращена</span>':`<button class="btn btn-light" onclick="LMS.renew('${l.loan_id}')">Продлить</button>`}</div></div>`).join('')}</div>`:'<div class="empty">У вас пока нет выдач.</div>'}catch(e){this.toast(e.message)}},
 async renew(id){try{const d=await this.api('/loans/renew',{method:'POST',body:JSON.stringify({loan_id:id})});
this.toast('Новый срок: '+d.due_date);
this.renderMyLoans()}catch(e){this.toast(e.message)}},
 async renderNotifications(){if(!this.need())return;
try{const rows=await this.api('/notifications');
document.getElementById('notifications-page').innerHTML=rows.length?`<div class="list">${rows.map(n=>`<div class="list-item"><div><h3>${n.title}</h3><p>${n.message}</p><small class="muted">${n.sent_date}</small></div><span class="status">${n.is_read?'Прочитано':'Новое'}</span></div>`).join('')}</div>`:'<div class="empty">Уведомлений нет.</div>'}catch(e){this.toast(e.message)}},
 async renderFines(){if(!this.need())return;
try{const rows=await this.api('/fines/me');
document.getElementById('fines-page').innerHTML=rows.length?`<div class="table-wrap"><table><thead><tr><th>Дата</th><th>Тип</th><th>Описание</th><th>Сумма</th><th>Статус</th><th></th></tr></thead><tbody>${rows.map(f=>`<tr><td>${f.created_date}</td><td>${f.type}</td><td>${f.description||'—'}</td><td><b>${Number(f.amount).toFixed(2)} ₽</b></td><td>${f.is_paid?'Оплачен':'Не оплачен'}</td><td>${f.is_paid?'':`<button class="btn btn-light" onclick="LMS.payFine('${f.fine_id}')">Оплатить</button>`}</td></tr>`).join('')}</tbody></table></div>`:'<div class="empty">Штрафов нет.</div>'}catch(e){this.toast(e.message)}},
 async payFine(id){try{await this.api('/fines/pay/'+id,{method:'POST'});
this.toast('Штраф отмечен как оплаченный');
this.renderFines()}catch(e){this.toast(e.message)}},
async renderAdminDashboard(){if(!this.need())return;
try{const u=await this.api('/users/me');
if(!['ADMIN','LIBRARIAN'].includes(u.role))throw Error('Доступ только для сотрудников библиотеки');
const [users,loans,inv]=await Promise.all([this.api('/users'),this.api('/loans/active'),this.api('/reports/inventory')]);
const role=u.role==='ADMIN'?'Администратор':'Библиотекарь';
document.getElementById('admin-dashboard').innerHTML=`<div class="admin-welcome"><div><span class="role-badge">${role}</span><h2>Здравствуйте, ${u.first_name}!</h2><p>Система готова к работе. Выберите раздел или проверьте текущие показатели.</p></div><a class="btn btn-glass" href="/profile"><span>Профиль</span><span aria-hidden="true">→</span></a></div><div class="dashboard-grid dashboard-grid-four"><div class="stat stat-accent"><span class="stat-icon">👥</span><b>${users.length}</b><span>Пользователей</span></div><div class="stat"><span class="stat-icon">↗</span><b>${loans.length}</b><span>Активных выдач</span></div><div class="stat"><span class="stat-icon">✓</span><b>${inv.available_books}</b><span>Доступно экземпляров</span></div><div class="stat"><span class="stat-icon">!</span><b>${inv.lost_books}</b><span>Утеряно</span></div></div><div class="panel admin-actions"><div class="panel-heading"><div><span class="eyebrow">БЫСТРЫЙ ДОСТУП</span><h2>Управление библиотекой</h2></div></div><div class="action-grid"><a class="action-card" href="/admin/users"><span class="action-icon">👥</span><b>Пользователи</b><span>Верификация и управление аккаунтами</span><em>Открыть →</em></a><a class="action-card" href="/admin/books"><span class="action-icon">▤</span><b>Книги</b><span>Издания, экземпляры и статусы</span><em>Открыть →</em></a><a class="action-card" href="/admin/loans"><span class="action-icon">↔</span><b>Книговыдача</b><span>Выдать книгу и оформить возврат</span><em>Открыть →</em></a><a class="action-card" href="/reports"><span class="action-icon">▥</span><b>Отчёты</b><span>Инвентарь, просрочки и аналитика</span><em>Открыть →</em></a>${u.role==='ADMIN'?'<a class="action-card" href="/settings"><span class="action-icon">⚙</span><b>Настройки</b><span>Правила выдачи и штрафов</span><em>Открыть →</em></a>':''}</div></div>`}catch(e){const root=document.getElementById('admin-dashboard');if(root)root.innerHTML=`<div class="empty">Не удалось загрузить панель. <button class="btn btn-light" onclick="LMS.renderAdminDashboard()">Повторить</button></div>`;this.toast(e.message)}},
async renderUsers(){if(!this.need())return;
try{const [rows,current]=await Promise.all([this.api('/users'),this.api('/users/me')]);
document.getElementById('users-page').innerHTML=`<div class="toolbar"><button class="btn btn-light" onclick="LMS.renderUsers()">Обновить</button>${current.role==='ADMIN'?'<button class="btn btn-primary" onclick="LMS.createLibrarian()">+ Библиотекарь</button>':''}</div><div class="table-wrap"><table><thead><tr><th>Пользователь</th><th>Роль</th><th>Email</th><th>Верификация</th><th>Активен</th><th></th></tr></thead><tbody>${rows.map(x=>`<tr><td><b>${x.first_name} ${x.last_name}</b><br><small>${x.login}</small></td><td>${x.role}</td><td>${x.email}</td><td>${x.is_verified?'Да':'Нет'}</td><td>${x.is_active?'Да':'Нет'}</td><td>${!x.is_verified&&['STUDENT','EMPLOYEE'].includes(x.role)?`<button class="btn btn-light" onclick="LMS.verify('${x.user_id}')">Верифицировать</button>`:''}${current.role==='ADMIN'&&x.role!=='ADMIN'&&x.is_active?` <button class="btn btn-light danger" onclick="LMS.deactivate('${x.user_id}')">Деактивировать</button>`:''}${current.role==='ADMIN'&&x.role!=='ADMIN'&&!x.is_active?` <button class="btn btn-danger" onclick="LMS.deleteUser('${x.user_id}')">Удалить</button>`:''}</td></tr>`).join('')}</tbody></table></div>`}catch(e){this.toast(e.message)}},
 async verify(id){try{await this.api('/users/'+id+'/verify',{method:'PUT'});
this.toast('Пользователь верифицирован');
this.renderUsers()}catch(e){this.toast(e.message)}},
async deactivate(id){if(!confirm('Деактивировать пользователя?'))return;
try{await this.api('/users/'+id,{method:'DELETE'});
this.toast('Пользователь деактивирован');
this.renderUsers()}catch(e){this.toast(e.message)}},
 async deleteUser(id){if(!confirm('Окончательно удалить пользователя? Это действие нельзя отменить.'))return;
try{await this.api('/users/'+id+'/permanent',{method:'DELETE'});
this.toast('Пользователь удалён');this.renderUsers()}catch(e){this.toast(e.message)}},
 createLibrarian(){
if(document.getElementById('librarian-modal'))return;
const modal=document.createElement('div');
modal.id='librarian-modal';
modal.className='modal-backdrop';
modal.innerHTML=`<div class="modal-card" role="dialog" aria-modal="true" aria-labelledby="librarian-modal-title"><div class="modal-head"><div><div class="eyebrow">НОВЫЙ СОТРУДНИК</div><h2 id="librarian-modal-title">Добавить библиотекаря</h2><p>Создайте учётную запись сотрудника библиотеки.</p></div><button class="modal-close" type="button" aria-label="Закрыть" onclick="LMS.closeLibrarianForm()">×</button></div><form id="librarian-form" onsubmit="return LMS.submitLibrarian(event)"><div class="form-grid"><label>Имя<input id="lib_first_name" name="first_name" required autocomplete="given-name" placeholder="Анна"></label><label>Фамилия<input id="lib_last_name" name="last_name" required autocomplete="family-name" placeholder="Иванова"></label><label>Логин<input id="lib_login" name="login" required minlength="3" maxlength="50" autocomplete="username" placeholder="a.ivanova"></label><label>Email<input id="lib_email" name="email" type="email" required autocomplete="email" placeholder="employee@library.ru"></label></div><label class="modal-password">Временный пароль<input id="lib_password" name="password" type="password" required minlength="6" autocomplete="new-password" placeholder="Минимум 6 символов"><small>Передайте пароль сотруднику безопасным способом.</small></label><div class="modal-actions"><button class="btn btn-light" type="button" onclick="LMS.closeLibrarianForm()">Отмена</button><button id="lib_submit" class="btn btn-primary" type="submit">Создать библиотекаря</button></div></form></div>`;
modal.addEventListener('click',event=>{if(event.target===modal)this.closeLibrarianForm()});
modal.addEventListener('keydown',event=>{if(event.key==='Escape')this.closeLibrarianForm()});
document.body.appendChild(modal);
document.body.classList.add('modal-open');
document.getElementById('lib_first_name').focus()},
 closeLibrarianForm(){const modal=document.getElementById('librarian-modal');if(modal)modal.remove();document.body.classList.remove('modal-open')},
 async submitLibrarian(e){e.preventDefault();
const button=document.getElementById('lib_submit');
const data={login:document.getElementById('lib_login').value.trim(),email:document.getElementById('lib_email').value.trim(),password:document.getElementById('lib_password').value,first_name:document.getElementById('lib_first_name').value.trim(),last_name:document.getElementById('lib_last_name').value.trim()};
button.disabled=true;button.textContent='Создаём…';
try{await this.api('/users/librarian',{method:'POST',body:JSON.stringify(data)});
this.closeLibrarianForm();this.toast('Библиотекарь создан');this.renderUsers()}catch(error){this.toast(error.message);button.disabled=false;button.textContent='Создать библиотекаря'}return false},
 async renderAdminBooks(){if(!this.need())return;
try{const rows=await this.api('/books?limit=100');
document.getElementById('admin-books-page').innerHTML=`<div class="table-wrap"><table><thead><tr><th>Книга</th><th>Автор</th><th>Жанр</th><th>Экземпляры</th><th></th></tr></thead><tbody>${rows.map(b=>`<tr><td><b>${b.title}</b><br><small>${b.isbn||'ISBN не указан'}</small></td><td>${b.author}</td><td>${b.genre||'—'}</td><td>${b.available_copies||0} / ${b.total_copies||0}</td><td><a class="btn btn-light" href="/books/${b.book_id}">Открыть</a> <button class="btn btn-light" onclick="LMS.addCopy('${b.book_id}')">+ Экземпляр</button></td></tr>`).join('')}</tbody></table></div>`}catch(e){this.toast(e.message)}},
 addBookForm(){const title=prompt('Название книги');
if(!title)return;
const author=prompt('Автор');
const genre=prompt('Жанр');
const isbn=prompt('ISBN');
this.createBook({title,author,genre,isbn})},
 async createBook(x){try{await this.api('/books',{method:'POST',body:JSON.stringify(x)});
this.toast('Книга добавлена');
this.renderAdminBooks()}catch(e){this.toast(e.message)}},
async addCopy(book_id){const branch=prompt('Филиал: AVTOZAVODSKAYA / KORCHAGINA / PRYANISHNIKOVA','AVTOZAVODSKAYA');
if(!branch)return;
const yearValue=prompt('Год конкретного издания (обязательное поле, например 2024)','');
if(yearValue===null)return;
const editionValue=prompt('Номер издания (необязательно, например 1)','');
if(!yearValue.trim()){this.toast('Укажите год издания');return}
const publication_year=Number(yearValue);
const edition_number=editionValue&&editionValue.trim()?Number(editionValue):null;
if(!Number.isInteger(publication_year)||publication_year<1000||publication_year>9999){this.toast('Укажите корректный год издания');return}
if(edition_number!==null&&(!Number.isInteger(edition_number)||edition_number<1)){this.toast('Номер издания должен быть положительным целым числом');return}
try{await this.api('/books/'+book_id+'/copies',{method:'POST',body:JSON.stringify({branch,condition:'NEW',publication_year,edition_number})});
this.toast('Экземпляр добавлен');
this.renderAdminBooks()}catch(e){this.toast(e.message)}},
 async renderAdminLoans(){if(!this.need())return;
try{const rows=await this.api('/loans/active');
const users=await this.api('/users?verified=true');
const books=await this.api('/books?available=true&limit=100');
document.getElementById('admin-loans-page').innerHTML=`<div class="panel"><h2>Новая выдача</h2><div class="form-grid"><label>Читатель<select id="loan_user">${users.filter(u=>['STUDENT','EMPLOYEE'].includes(u.role)).map(u=>`<option value="${u.user_id}">${u.first_name} ${u.last_name} — ${u.login}</option>`).join('')}</select></label><label>Книга / экземпляр<select id="loan_copy">${(await Promise.all(books.map(async b=>{const c=await this.api('/books/'+b.book_id+'/copies');return c.filter(x=>x.status==='AVAILABLE').map(x=>({id:x.copy_id,label:b.title+' · '+x.inventory_number+' · '+x.branch}))}))).flat().map(x=>`<option value="${x.id}">${x.label}</option>`).join('')}</select></label></div><button class="btn btn-primary" style="margin-top:15px" onclick="LMS.borrow()">Выдать книгу</button></div><div class="section-head"><h2>Активные выдачи</h2><button class="btn btn-light" onclick="LMS.renderAdminLoans()">Обновить</button></div><div class="table-wrap"><table><thead><tr><th>Книга</th><th>Читатель</th><th>Филиал</th><th>Срок</th><th></th></tr></thead><tbody>${rows.map(l=>`<tr><td>${l.title}</td><td>${l.login}</td><td>${l.branch}</td><td>${l.due_date}</td><td><button class="btn btn-light" onclick="LMS.returnLoan('${l.loan_id}')">Вернуть</button></td></tr>`).join('')}</tbody></table></div>`}catch(e){this.toast(e.message)}},
 async borrow(){try{await this.api('/loans/borrow',{method:'POST',body:JSON.stringify({user_id:loan_user.value,copy_id:loan_copy.value})});
this.toast('Книга выдана');
this.renderAdminLoans()}catch(e){this.toast(e.message)}},
 async returnLoan(id){const mode=prompt('Введите: normal, damaged или lost','normal');
if(!mode)return;
const damaged=mode==='damaged',lost=mode==='lost';
const note=damaged?prompt('Описание повреждения')||'':'';
try{const d=await this.api('/loans/return',{method:'POST',body:JSON.stringify({loan_id:id,lost,damaged,damage_note:note})});
this.toast('Возврат обработан. Штраф: '+Number(d.fine).toFixed(2)+' ₽');
this.renderAdminLoans()}catch(e){this.toast(e.message)}},
 async renderReports(){if(!this.need())return;
try{const [inv,use,pop,trends,over]=await Promise.all([this.api('/reports/inventory'),this.api('/reports/usage'),this.api('/reports/popular'),this.api('/reports/borrowing-trends'),this.api('/reports/overdue')]);
document.getElementById('reports-page').innerHTML=`<div class="stats-grid"><div class="stat"><b>${inv.total_books}</b><span>Всего экземпляров</span></div><div class="stat"><b>${inv.available_books}</b><span>Доступно</span></div><div class="stat"><b>${inv.issued_books}</b><span>Выдано</span></div><div class="stat"><b>${Number(use.total_fines_collected).toFixed(2)} ₽</b><span>Собрано штрафов</span></div></div><div class="panel" style="margin-top:20px"><h2>Популярные книги</h2><div class="table-wrap"><table><thead><tr><th>Книга</th><th>Автор</th><th>Выдач</th></tr></thead><tbody>${pop.length?pop.map(x=>`<tr><td>${x.title}</td><td>${x.author}</td><td>${x.loans}</td></tr>`).join(''):'<tr><td colspan="3">Нет данных</td></tr>'}</tbody></table></div></div><div class="panel"><h2>Тенденции выдачи</h2><div class="table-wrap"><table><thead><tr><th>Месяц</th><th>Выдач</th></tr></thead><tbody>${trends.map(x=>`<tr><td>${x.month}</td><td>${x.loans}</td></tr>`).join('')||'<tr><td colspan="2">Нет данных</td></tr>'}</tbody></table></div></div><div class="panel"><h2>Просрочки</h2><p>${over.length} активных просрочек.</p></div>`}catch(e){this.toast(e.message)}},
 async renderSettings(){if(!this.need())return;
try{const p=await this.api('/settings');
document.getElementById('settings-page').innerHTML=`<div class="panel"><form onsubmit="return LMS.saveSettings(event)"><div class="form-grid"><label>Макс. книг на пользователя<input id="s_books" type="number" min="1" value="${p.maxBooksPerUser}"></label><label>Макс. дней выдачи<input id="s_days" type="number" min="1" value="${p.maxBorrowDays}"></label><label>Макс. продлений<input id="s_renew" type="number" min="0" value="${p.maxRenewCount}"></label><label>Дней на продление<input id="s_renewdays" type="number" min="1" value="${p.renewalDays}"></label><label>Штраф за день<input id="s_rate" type="number" min="0" step="0.01" value="${p.dailyFineRate}"></label><label>Штраф за утерю<input id="s_lost" type="number" min="0" step="0.01" value="${p.lostBookFee}"></label><label>Штраф за повреждение<input id="s_damage" type="number" min="0" step="0.01" value="${p.damagedBookFee}"></label><label>Макс. штраф<input id="s_maxfine" type="number" min="0" step="0.01" value="${p.maxFineAmount}"></label><label>Льготные дни просрочки<input id="s_grace" type="number" min="0" value="${p.overdueGracePeriod}"></label></div><button class="btn btn-primary" style="margin-top:20px">Сохранить настройки</button></form></div>`}catch(e){this.toast(e.message)}},
 async saveSettings(e){e.preventDefault();
try{await this.api('/settings',{method:'PUT',body:JSON.stringify({maxBooksPerUser:+s_books.value,maxBorrowDays:+s_days.value,maxRenewCount:+s_renew.value,verificationRequired:true,dailyFineRate:+s_rate.value,lostBookFee:+s_lost.value,damagedBookFee:+s_damage.value,renewalDays:+s_renewdays.value,maxFineAmount:+s_maxfine.value,overdueGracePeriod:+s_grace.value})});
this.toast('Настройки сохранены')}catch(x){this.toast(x.message)}return false}
};

document.addEventListener('DOMContentLoaded',()=>LMS.initNav());
