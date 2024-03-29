## Yatube
### Описание 
Cоциальная сеть для публикации постов.
### Основные технологии
Python 3.7  
Django 2.2.19   
Pillow 8.3
### Запуск проекта в dev-режиме 
- Клонируйте проект с помощью git clone или скачайте ZIP-архив.
- Установите и активируйте виртуальное окружение  
``` python -m venv venv ```
- Установите зависимости из файла requirements.txt  
``` pip install -r requirements.txt ```
- Сделайте миграции  
``` python manage.py makemigrations ```  
``` python manage.py migrate ```
- В папке с файлом manage.py выполните команду:  
``` python manage.py runserver ```

### Что могут делать пользователи:

**Залогиненные** пользователи могут:
1. Просматривать, публиковать, удалять и редактировать свои публикации;
2. Просматривать информацию о сообществах;
3. Просматривать и публиковать комментарии от своего имени к публикациям других пользователей *(включая самого себя)*, удалять и редактировать **свои** комментарии;
4. Подписываться на других пользователей и просматривать **свои** подписки.<br/>
***Примечание***: Доступ ко всем операциям записи, обновления и удаления доступны только после аутентификации и получения токена.

**Анонимные** пользователи могут:
1. Просматривать публикации;
2. Просматривать информацию о сообществах;
3. Просматривать комментарии;

### **Набор доступных эндпоинтов**:
* ```posts/``` - Отображение постов и публикаций (_GET, POST_);
* ```posts/{id}``` - Получение, изменение, удаление поста с соответствующим **id** (_GET, PUT, PATCH, DELETE_);
* ```posts/{post_id}/comments/``` - Получение комментариев к посту с соответствующим **post_id** и публикация новых комментариев(_GET, POST_);
* ```posts/{post_id}/comments/{id}``` - Получение, изменение, удаление комментария с соответствующим **id** к посту с соответствующим **post_id** (_GET, PUT, PATCH, DELETE_);
* ```posts/groups/``` - Получение описания зарегестрированных сообществ (_GET_);
* ```posts/groups/{id}/``` - Получение описания сообщества с соответствующим **id** (_GET_);
* ```posts/follow/``` - Получение информации о подписках текущего пользователя, создание новой подписки на пользователя (_GET, POST_).<br/>


### Протестировано с помощью Unittests
**Автор**  
Стацюк В.Н.
