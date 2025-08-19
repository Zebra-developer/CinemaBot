# main.py
import os
import asyncio
import httpx
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

load_dotenv()

# Настроёув токена бота, АПИ, прокси
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN not set in .env")

TMDB_TOKEN = os.getenv("TMDB_TOKEN")
if not TMDB_TOKEN:
    raise RuntimeError("TMDB_TOKEN not set in .env")

# Настройки прокси
proxi = os.getenv("PROXY")
if not proxi:
    raise RuntimeError("PROXY not set in .env")


# FSM: состояния пользователя
class SearchMovieState(StatesGroup):
    waiting_for_query = State()


# Главное меню (вызываем из разных мест)
def get_main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔍 Поиск фильма", callback_data="menu_search"),
            InlineKeyboardButton(text="🎬 Афиша", callback_data="menu_poster")
        ],
            
        [
            InlineKeyboardButton(text="О разработчике", callback_data="developer")
        ]
    ])


# Кнопка возврата в главное меню
def back_keyboard():
    # Кнопка возврата
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ В меню", callback_data="back_to_menu")]]
    )


async def info_developer(callback: CallbackQuery):
    text = '''
Разработчик: Zebra_Developer.
Моя визитка:
https://my-business-card-4qs2.onrender.com
Связь со мной: 
mail - parkerpitergoy@gmail.com
    '''
    await callback.message.answer(text=text, reply_markup=back_keyboard())


async def search_movie(query: str):
    """Поиск фильма через TMDb API"""
    url = "https://api.themoviedb.org/3/search/movie"
    headers = {
        "Authorization": f"Bearer {TMDB_TOKEN}",
        "Accept": "application/json"
    }
    params = {"query": query, "language": "ru-RU", "page": 1}

    try:
        async with httpx.AsyncClient(proxy=proxi, timeout=10) as client:
            r = await client.get(url, headers=headers, params=params)
            r.raise_for_status()
            data = r.json()
            return data.get("results", [])
    except Exception as e:
        print("Ошибка при запросе к TMDb:", e)
        return []


async def get_now_playing():
    """Получаем список фильмов, которые сейчас идут в кино"""
    url = "https://api.themoviedb.org/3/movie/now_playing"
    headers = {"Authorization": f"Bearer {TMDB_TOKEN}"}
    params = {"language": "ru-RU", "page": 1}

    try:
        async with httpx.AsyncClient(proxy=proxi, timeout=10) as client:
            r = await client.get(url, headers=headers, params=params)
            r.raise_for_status()
            return r.json().get("results", [])
    except Exception as e:
        print("Ошибка при запросе к TMDb:", e)
        return []


async def cmd_start(message: Message):
    await message.answer(
        "👋 Привет! Я — Кинотеатр.\nВыбери действие ниже:",
        reply_markup=get_main_menu()
    )


# Режим поиска по кнопке
async def menu_callback(callback: CallbackQuery, state: FSMContext):
    if callback.data == "menu_search":
        await callback.message.answer("Напишите название фильма:", reply_markup=back_keyboard())
        await state.set_state(SearchMovieState.waiting_for_query)
    elif callback.data == "menu_poster":
        await show_poster_list(callback)
    elif callback.data == "back_to_menu":
        await callback.message.answer("📌 Главное меню", reply_markup=get_main_menu())


# Обработка сообщения с названием фильма
async def process_movie_query(message: Message, state: FSMContext):
    query = message.text.strip()
    if not query:
        await message.answer("Напиши: /search <название фильма>", reply_markup=back_keyboard()) 
        return

    movies = await search_movie(query)
    if not movies:
        await message.answer("Ничего не найдено.", reply_markup=back_keyboard())
        await state.clear()
        return

    for movie in movies[:3]:
        title = movie.get("title")
        year = movie.get("release_date", "")[:4]
        overview = movie.get("overview", "Описание отсутствует.")
        poster_path = movie.get("poster_path")
        reply_text = f"💠 {title} ({year})"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Подробнее", callback_data=f"details_{movie['id']}")]
        ])

        if poster_path:
            photo_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
            await message.answer_photo(photo=photo_url, caption=reply_text, reply_markup=keyboard)
        else:
            await message.answer(reply_text, reply_markup=keyboard)
        
    await state.clear()  # выходим из режима поиска


async def details_callback(callback: CallbackQuery):
    """Обработчик кнопки 'Подробнее'"""
    movie_id = callback.data.split("_")[1]
    url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    headers = {"Authorization": f"Bearer {TMDB_TOKEN}"}
    params = {"language": "ru-RU"}

    try:
        async with httpx.AsyncClient(proxy=proxi, timeout=10) as client:
            r = await client.get(url, headers=headers, params=params)
            r.raise_for_status()
            movie = r.json()

        title = movie.get("title")
        year = movie.get("release_date", "")[:4]
        overview = movie.get("overview", "Описание отсутствует.")
        poster_path = movie.get("poster_path")
        reply_text = f"💠 {title} ({year})\n\n{overview}"

        if poster_path:
            photo_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
            await callback.message.answer_photo(photo=photo_url, caption=reply_text, reply_markup=back_keyboard())
        else:
            await callback.message.answer(reply_text, reply_markup=back_keyboard())

    except Exception as e:
        await callback.message.answer("Ошибка при получении деталей фильма.")
        print(e)


async def show_poster_list(callback: CallbackQuery):
    """Показ афиши (несколько фильмов + кнопки)"""
    movies = await get_now_playing()

    if not movies:
        await callback.message.answer("Не удалось загрузить афишу 😔", reply_markup=back_keyboard())
        return

    movies = movies[:10]  # берем только 10 фильмов

    media = []

    for movie in movies:
        title = movie.get("title")
        year = movie.get("release_date", "")[:4]
        poster_path = movie.get("poster_path")
        movie_id = movie.get("id")

        reply_text = f"🎬 {title} ({year})"

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Подробнее", callback_data=f"details_{movie_id}")]]
        )

        if poster_path:
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
            media.append(InputMediaPhoto(media=poster_url, caption=reply_text))  
        else:
            # если нет постера просто заглушка
            media.append(InputMediaPhoto(media="https://via.placeholder.com/500x750?text=No+Image", caption=reply_text))
    
    # отправляем альбом
    if media:
        await callback.message.answer_media_group(media)

    # кнопки подробнее для каждого фильма
    buttons = []
    for movie in movies:
        buttons.append([InlineKeyboardButton(text=f"ℹ {movie['title']}", callback_data=f"details_{movie['id']}")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    # объединяем кнопки с кнопкой назад 
    keyboard.inline_keyboard.append(back_keyboard().inline_keyboard[0])

    await callback.message.answer("Выберите фильм для подробностей: ", reply_markup=keyboard)


async def main():
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.message.register(cmd_start, Command(commands=["start", "help"]))
    dp.message.register(process_movie_query, SearchMovieState.waiting_for_query)
    dp.callback_query.register(details_callback, F.data.startswith("details_"))
    dp.callback_query.register(menu_callback, F.data.startswith("menu_"))
    dp.callback_query.register(menu_callback, F.data == "back_to_menu")
    dp.callback_query.register(info_developer, F.data == 'developer')

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())