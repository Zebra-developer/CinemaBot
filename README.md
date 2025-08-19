# 🎬 Telegram Cinema Bot

Простой Telegram-бот на [aiogram 3](https://docs.aiogram.dev/), который позволяет искать фильмы и смотреть афишу.

## 📌 Возможности
- Поиск фильмов по названию
- Отображение афиши (10 постеров сразу)
- Кнопки для каждого фильма ("Подробнее")
- Кнопка "Назад" для возврата в меню
- Использование Прокси 

## 🚀 Установка и запуск
1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/USERNAME/cinema_bot.git
   cd cinema_bot

2.Создайте и активируйте виртуальное окружение:

	```bash
	
 	python -m venv .venv
	source .venv/bin/activate   # Linux / MacOS
	.venv\Scripts\activate      # Windows PowerShell


3. Установите зависимости:
	```bash
 	pip install -r requirements.txt


4. Создайте файл .env и добавьте туда свой токен Telegram API:
  	 ```bash
    BOT_TOKEN=ваш_токен


6. Запустите бота:
   ```bash
   python main.py


