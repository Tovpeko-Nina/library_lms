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
if(dash)dash.classList.remove('hidden');
if(admin&&['ADMIN','LIBRARIAN'].includes(u.role))admin.classList.remove('hidden');
if(name){name.textContent=u.first_name+' '+u.last_name;
name.onclick=()=>location.href='/dashboard';
name.style.cursor='pointer'}}catch{localStorage.removeItem('lms_token')}},
 async login(e){e.preventDefault();
try{const d=await this.api('/auth/login',{method:'POST',body:JSON.stringify({login:document.getElementById('login').value,password:document.getElementById('password').value})});
localStorage.setItem('lms_token',d.access_token);
location.href='/dashboard'}catch(err){this.toast(err.message)}return false},
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
 async reserve(bookId){if(!this.need())return;
try{await this.api('/reservations',{method:'POST',body:JSON.stringify({book_id:bookId})});
this.toast('Книга забронирована')}catch(e){this.toast(e.message)}},
 async renderDashboard(){if(!this.need())return;
try{const u=await this.api('/users/me');
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
document.getElementById('admin-dashboard').innerHTML=`<div class="dashboard-grid"><div class="stat"><b>${users.length}</b><span>Пользователей</span></div><div class="stat"><b>${loans.length}</b><span>Активных выдач</span></div><div class="stat"><b>${inv.lost_books}</b><span>Утерянных экземпляров</span></div></div><div class="panel" style="margin-top:20px"><div class="action-grid"><a class="action-card" href="/admin/users"><b>Пользователи</b><span>Верификация и управление аккаунтами</span></a><a class="action-card" href="/admin/books"><b>Книги</b><span>Издания, экземпляры и статусы</span></a><a class="action-card" href="/admin/loans"><b>Книговыдача</b><span>Выдать и обработать возврат</span></a><a class="action-card" href="/reports"><b>Отчёты</b><span>Инвентарь и аналитика</span></a>${u.role==='ADMIN'?'<a class="action-card" href="/settings"><b>Настройки</b><span>Правила книговыдачи</span></a>':''}</div></div>`}catch(e){this.toast(e.message)}},
 async renderUsers(){if(!this.need())return;
try{const rows=await this.api('/users');
document.getElementById('users-page').innerHTML=`<div class="toolbar"><button class="btn btn-light" onclick="LMS.renderUsers()">Обновить</button><button class="btn btn-primary" onclick="LMS.createLibrarian()">+ Библиотекарь</button></div><div class="table-wrap"><table><thead><tr><th>Пользователь</th><th>Роль</th><th>Email</th><th>Верификация</th><th>Активен</th><th></th></tr></thead><tbody>${rows.map(x=>`<tr><td><b>${x.first_name} ${x.last_name}</b><br><small>${x.login}</small></td><td>${x.role}</td><td>${x.email}</td><td>${x.is_verified?'Да':'Нет'}</td><td>${x.is_active?'Да':'Нет'}</td><td>${!x.is_verified&&['STUDENT','EMPLOYEE'].includes(x.role)?`<button class="btn btn-light" onclick="LMS.verify('${x.user_id}')">Верифицировать</button>`:''}${x.role!=='ADMIN'&&x.is_active?` <button class="btn btn-light danger" onclick="LMS.deactivate('${x.user_id}')">Деактивировать</button>`:''}</td></tr>`).join('')}</tbody></table></div>`}catch(e){this.toast(e.message)}},
 async verify(id){try{await this.api('/users/'+id+'/verify',{method:'PUT'});
this.toast('Пользователь верифицирован');
this.renderUsers()}catch(e){this.toast(e.message)}},
 async deactivate(id){if(!confirm('Деактивировать пользователя?'))return;
try{await this.api('/users/'+id,{method:'DELETE'});
this.toast('Пользователь деактивирован');
this.renderUsers()}catch(e){this.toast(e.message)}},
 async createLibrarian(){const login=prompt('Логин библиотекаря');
if(!login)return;
const email=prompt('Email');
const password=prompt('Пароль');
const first_name=prompt('Имя');
const last_name=prompt('Фамилия');
if(!email||!password||!first_name||!last_name)return;
try{await this.api('/users/librarian',{method:'POST',body:JSON.stringify({login,email,password,first_name,last_name})});
this.toast('Библиотекарь создан');
this.renderUsers()}catch(e){this.toast(e.message)}},
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
try{await this.api('/books/'+book_id+'/copies',{method:'POST',body:JSON.stringify({branch,condition:'NEW'})});
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
