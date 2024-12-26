import streamlit as st
import speech_recognition as sr
import aiosqlite
import random
import pyttsx3
import asyncio

#подключение к базе данных и создание таблиц
async def init_db():
    async with aiosqlite.connect('chatbot.db') as conn:
        cursor = await conn.cursor()
        # Создаем таблицу для шуток
        await cursor.execute('''CREATE TABLE IF NOT EXISTS jokes (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    root TEXT NOT NULL)''')
        # Создаем таблицу для истории чата
        await cursor.execute('''CREATE TABLE IF NOT EXISTS chat_history (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    user_message TEXT,
                                    bot_response TEXT)''')
        await conn.commit()

# Добавление шуток в базу
async def populate_jokes():
    async with aiosqlite.connect('chatbot.db') as conn:
        cursor = await conn.cursor()
        await cursor.execute("SELECT COUNT(*) FROM jokes")
        if (await cursor.fetchone())[0] == 0:  # Если база шуток пуста
            jokes = [
                "Почему программисты так любят темные темы? Потому что светлый мир их пугает!",
                "Как называется лучший язык программирования? Тот, который ты знаешь.",
                "Какая основная ошибка программиста? Использование ‘print’ вместо дебаггера!",
                "Почему программисты не могут делить еду? Потому что они не умеют делить массивы."
            ]
            for joke in jokes:
                await cursor.execute("INSERT INTO jokes (root) VALUES (?)", (joke,))
            await conn.commit()

#функция поиска шуток
async def search_joke(user_input):
    async with aiosqlite.connect('chatbot.db') as conn:
        cursor = await conn.cursor()

        # Разбиваем пользовательский ввод на слова
        words = user_input.lower().split()
        found_jokes = []

        # Ищем совпадения по каждому слову в колонке root
        for word in words:
            await cursor.execute("SELECT root FROM jokes WHERE root LIKE ? ORDER BY RANDOM() LIMIT 5", (f"%{word}%",))
            jokes = await cursor.fetchall()
            for joke in jokes:
                if joke[0] not in found_jokes:  # Чтобы избежать повторов
                    found_jokes.append(joke[0])

        # Если совпадения найдены, возвращаем их, иначе случайная шутка
        if found_jokes:
            return random.choice(found_jokes)
        else:
            await cursor.execute("SELECT root FROM jokes ORDER BY RANDOM() LIMIT 1")
            random_joke = await cursor.fetchone()
            return random_joke[0]

# Сохранение истории чата
async def save_chat_history(user_message, bot_response):
    async with aiosqlite.connect('chatbot.db') as conn:
        cursor = await conn.cursor()
        await cursor.execute("INSERT INTO chat_history (user_message, bot_response) VALUES (?, ?)", (user_message, bot_response))
        await conn.commit()

# Загрузка истории чата
async def load_chat_history():
    async with aiosqlite.connect('chatbot.db') as conn:
        cursor = await conn.cursor()
        await cursor.execute("SELECT user_message, bot_response FROM chat_history")
        history = await cursor.fetchall()
        return history

# Озвучивание текста
def speak_text(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

# Функция для распознавания речи
def recognize_speech():
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    LANGUAGE = 'ru-RU'

    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)
        recognizer.pause_threshold = 1.5
        st.info("Говорите...")  # Информационное сообщение пользователю

        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=15)
            st.success("Запись завершена. Распознавание...")
        except Exception as e:
            st.error(f"Ошибка во время записи: {e}")
            return ""

    try:
        text = recognizer.recognize_google(audio, language=LANGUAGE)
        return text
    except sr.UnknownValueError:
        st.warning("Не удалось распознать речь.")
        return ""
    except sr.RequestError:
        st.error("Ошибка сервиса распознавания речи.")
        return ""

# Главная функция
async def main():
    # Инициализация базы данных и заполним шутки
    await init_db()
    await populate_jokes()

    # Состояние чата
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = await load_chat_history()

    # Отображение истории чата
    st.write("---")
    st.write("### История чата")
    for user_message, bot_response in st.session_state.chat_history:
        st.markdown(f"**Вы:** {user_message}")
        st.markdown(f"**Бот:** {bot_response}")
        st.write("---")

    manual_input = st.text_input("Или введите текст вручную:")
    if st.button("Отправить текст") and manual_input:
        bot_response = await search_joke(manual_input)  # Используем новую функцию поиска
        st.session_state.chat_history.append((manual_input, bot_response))
        await save_chat_history(manual_input, bot_response)
        speak_text(bot_response)

    # Кнопка распознавания речи
    if st.button("Начать запись речи"):
        recognized_text = recognize_speech()
        if recognized_text:
            bot_response = await search_joke(recognized_text)  # Используем новую функцию поиска
            st.session_state.chat_history.append((recognized_text, bot_response))
            await save_chat_history(recognized_text, bot_response)
            speak_text(bot_response)

# Запуск
if __name__ == '__main__':
    asyncio.run(main())
