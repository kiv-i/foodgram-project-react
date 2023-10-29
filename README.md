# Foodgram

### О проекте

Foodgram "Продуктовый помощник" — сайт, на котором пользователи могут 
публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться 
на публикации других авторов. Пользователям сайта также доступен сервис 
«Список покупок». Он позволяет создавать список продуктов, которые нужно купить для 
приготовления выбранных блюд, его можно скачать в виде .txt файла.

Это проект, который состоит из backend-приложения на Django 
и frontend-приложения на React. Проект запускается на сервере в контейнерах
Docker. Есть возможность deploy проекта с помощью GitHub Action (main.yml).

### Использованные технологии

* [Python 3.9](https://www.python.org/)
* [React](https://react.dev/)
* [Django 3.2](https://www.djangoproject.com/)
* [Django REST framework 3.12](https://www.django-rest-framework.org/)
* [Djoser 2.1](https://djoser.readthedocs.io/en/latest/getting_started.html)
* [Docker Compose V2](https://docs.docker.com/compose/)
* [Gunicorn 20.1](https://docs.gunicorn.org/en/stable/)
* [Nginx 1.22.1](https://nginx.org/ru/docs/)
* [PostgreSQL 13.10](https://www.postgresql.org/docs/)

### Примечания по запуску

Перед запуском проекта на сервер, в папку с будущим проектом, скопировать 
файл "docker-compose.production.yml" и файл с переменными окружения ".env", 
пример такого файла ".env.example".

После запуска проекта создать superuser для доступа к "https://your_domain/admin/":
```
cd "папка с проектом"
sudo docker compose -f docker-compose.production.yml exec backend python manage.py createsuperuser
```
И заполнить базу данных ингредиентами:
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py load_ingredients
```

### Примеры использования

Приложение доступно по адресу: https://your_domain/

Доступно API: https://your_domain/api/

Для пользования API необходимо получить токен авторизации.

Подробная документация с примерами запросов API доступна по адресу: https://your_domain/api/docs/

### Авторы

* [Константин Иванов](https://github.com/kiv-i)


https://fooodgram.duckdns.org/
