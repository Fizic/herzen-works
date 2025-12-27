# Django REST Framework: Микросервисы для аналитики голосований

## Описание проекта

Реализация микросервисов на Django REST Framework для анализа результатов голосований и предоставления статистики. Проект включает в себя основное приложение для голосований и микросервисы для аналитики.

## Структура проекта

```
mysite/
├── manage.py
├── mysite/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── polls/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── templates/
│   │   └── polls/
│   │       ├── base.html
│   │       ├── index.html
│   │       ├── detail.html
│   │       ├── results.html
│   │       └── search.html
│   └── static/
│       └── polls/
│           └── style.css
└── analytics/
    ├── models.py
    ├── views.py
    ├── serializers.py
    └── urls.py
```

## Реализованные микросервисы

### 1. Статистика по голосованиям
- **Endpoint**: `/analytics/api/questions/stats/`
- **Функциональность**:
  - Общее количество голосований
  - Общее количество голосов
  - Статистика по периодам (неделя, месяц)

### 2. Детальная статистика голосования
- **Endpoint**: `/analytics/api/questions/{id}/detailed_stats/`
- **Функциональность**:
  - Количество голосов на каждый вариант ответа
  - Процентное соотношение голосов
  - Детальная информация о голосовании

### 3. Фильтрация и сортировка данных
- **Endpoint**: `/analytics/api/questions/`
- **Параметры**:
  - `start_date` - фильтрация по дате начала
  - `end_date` - фильтрация по дате окончания
  - `sort_by` - сортировка (date, popularity, title)
  - `order` - порядок сортировки (asc, desc)

### 4. Генерация диаграмм
- **Endpoint**: `/analytics/api/questions/{id}/chart/`
- **Параметры**:
  - `type=bar` - столбчатая диаграмма (matplotlib)
  - `type=pie` - круговая диаграмма (plotly)
- **Возвращает**: Base64-кодированное изображение или HTML

### 5. Экспорт данных
- **CSV Export**: `/analytics/api/questions/export_csv/`
- **JSON Export**: `/analytics/api/questions/export_json/`

## Функциональность страницы поиска

### Поиск голосований
- Поиск по тексту вопроса и вариантам ответов
- Фильтрация по датам
- Сортировка по различным параметрам
- Динамическое отображение результатов

### Динамическая статистика
- Выбор голосования из списка результатов
- Отображение детальной статистики
- Генерация диаграмм по запросу
- Интерактивные элементы управления

## Технологии

- **Django 4.2.25** - основной фреймворк
- **Django REST Framework 3.16.1** - для создания API
- **Matplotlib 3.9.4** - для генерации столбчатых диаграмм
- **Plotly 6.3.1** - для генерации интерактивных диаграмм
- **SQLite** - база данных

## Установка и запуск

1. Создайте виртуальное окружение:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Установите зависимости:
```bash
pip install django djangorestframework matplotlib plotly
```

3. Выполните миграции:
```bash
python manage.py makemigrations
python manage.py migrate
```

4. Создайте тестовые данные:
```bash
python create_test_data.py
```

5. Запустите сервер:
```bash
python manage.py runserver
```

## API Endpoints

### Основные endpoints
- `GET /` - главная страница с списком голосований
- `GET /search/` - страница поиска и аналитики
- `GET /polls/{id}/` - детальная страница голосования
- `POST /polls/{id}/vote/` - голосование

### Analytics API
- `GET /analytics/api/questions/` - список голосований с фильтрацией
- `GET /analytics/api/questions/stats/` - общая статистика
- `GET /analytics/api/questions/{id}/detailed_stats/` - детальная статистика
- `GET /analytics/api/questions/{id}/chart/?type=bar` - столбчатая диаграмма
- `GET /analytics/api/questions/{id}/chart/?type=pie` - круговая диаграмма
- `GET /analytics/api/questions/export_csv/` - экспорт в CSV
- `GET /analytics/api/questions/export_json/` - экспорт в JSON

### Search API
- `GET /search/api/?q=query&start_date=2024-01-01&end_date=2024-12-31&sort_by=popularity` - поиск голосований

## Особенности реализации

### Анонимность
- Все голосования являются анонимными
- Авторизация не требуется для просмотра статистики
- API доступно без аутентификации

### Динамическое взаимодействие
- JavaScript для AJAX-запросов к API
- Динамическое обновление контента без перезагрузки страницы
- Интерактивные диаграммы с помощью Plotly

### Масштабируемость
- Модульная архитектура с отдельными приложениями
- RESTful API для легкой интеграции
- Возможность добавления новых микросервисов

## Примеры использования

### Получение статистики
```bash
curl http://127.0.0.1:8000/analytics/api/questions/stats/
```

### Поиск голосований
```bash
curl "http://127.0.0.1:8000/search/api/?q=python&sort_by=popularity"
```

### Экспорт данных
```bash
curl http://127.0.0.1:8000/analytics/api/questions/export_csv/ > polls.csv
```

## Заключение

Проект демонстрирует создание микросервисов на Django REST Framework для аналитики данных. Реализованы все требуемые функции: статистика, фильтрация, сортировка, генерация диаграмм и экспорт данных. Интерфейс позволяет интерактивно работать с данными через веб-страницу поиска.
