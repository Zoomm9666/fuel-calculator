<<<<<<< HEAD
# fuel-calculator
Приложение для расчета расхода топлива в симуляторах X-plane11,12 MSFS2020,2024
=======
# ✈️ Fuel Calculator

Приложение для расчета расхода топлива и параметров полета летательного аппарата.

## 🚀 Быстрый старт (локально)

### Требования
- Python 3.8+
- pip

### Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/ваш-юзер/fuel-calculator.git
cd fuel-calculator
```

2. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Запустите приложение:
```bash
streamlit run app.py
```

Приложение откроется по адресу: **http://localhost:8501**

---

## ☁️ Размещение на Streamlit Cloud

### Шаг 1: Подготовка GitHub репозитория

1. Создайте аккаунт на [GitHub](https://github.com) (если его нет)

2. Создайте новый репозиторий:
   - Нажмите "New repository"
   - Назовите его (например, `fuel-calculator`)
   - Нажмите "Create repository"

3. Загрузите файлы проекта (можно через GitHub Desktop или командную строку):
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/ваш-юзер/fuel-calculator.git
git push -u origin main
```

### Шаг 2: Размещение на Streamlit Cloud

1. Перейдите на [share.streamlit.io](https://share.streamlit.io/)

2. Нажмите кнопку **"Deploy an app"**

3. Заполните форму:
   - **GitHub repo**: `ваш-юзер/fuel-calculator`
   - **Branch**: `main`
   - **Main file path**: `app.py`

4. Нажмите **"Deploy!"**

5. Дождитесь завершения развертывания (1-2 минуты)

### Шаг 3: Ваше приложение готово! 🎉

Ваше приложение будет доступно по адресу:
```
https://share.streamlit.io/ваш-юзер/fuel-calculator/app.py
```

---

## 📋 Структура проекта

```
fuel-calculator/
├── app.py                 # Основное приложение Streamlit
├── utils.py              # Вспомогательные функции
├── requirements.txt      # Зависимости Python
├── aircraft_db.json      # База данных самолетов
├── airports.csv          # База данных аэропортов
├── .streamlit/
│   └── config.toml      # Конфигурация Streamlit
├── Dockerfile           # Для развертывания в Docker
└── README.md            # Этот файл
```

---

## 🔧 Требования

- `streamlit` - для веб-интерфейса
- `pandas` - для работы с данными
- `requests` - для HTTP запросов

---

## 📝 Функциональность

- 📍 Расчет расстояния между аэропортами
- 🛢️ Калькуляция расхода топлива
- 🌤️ Получение данных о погоде (METAR, TAF)
- 💨 Информация о ветре на различных эшелонах
- ✈️ Интеграция с базой данных самолетов

---

## 🐳 Docker

Для запуска в контейнере:

```bash
docker build -t fuel-calculator .
docker run -p 8501:8501 fuel-calculator
```

---

## 📞 Поддержка

Если возникли проблемы:
- Проверьте версии пакетов в `requirements.txt`
- Убедитесь, что репозиторий на GitHub содержит все файлы
- Проверьте логи в Streamlit Cloud

---

## 📄 Лицензия

MIT

---

**Создано:** апрель 2026
**Статус:** ✅ Готово к развертыванию
>>>>>>> b5e6942 (Первый коммит)
