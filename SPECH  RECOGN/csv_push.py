import aiosqlite
import asyncio
import csv
from pymystem3 import Mystem
import aiofiles
from tqdm import tqdm

# Инициализация Mystem
mystem = Mystem()

# Функция для извлечения корней слов (лемматизация)
def get_lemmas(text):
    lemmatized = mystem.lemmatize(text)
    return " ".join([lemma.strip() for lemma in lemmatized if lemma.strip()])

# Асинхронная функция для загрузки шуток из CSV в базу данных
async def load_jokes_from_csv(file_path, batch_size=100):
    async with aiosqlite.connect('chatbot.db') as conn:
        cursor = await conn.cursor()

        # Убедимся, что таблица шуток имеет нужные столбцы
        await cursor.execute("PRAGMA table_info(jokes)")
        columns_info = await cursor.fetchall()
        columns = [info[1] for info in columns_info]
        if 'root' not in columns:
            await cursor.execute("ALTER TABLE jokes ADD COLUMN root TEXT")

        # Чтение данных из CSV
        async with aiofiles.open(file_path, mode='r', encoding='utf-8') as csv_file:
            content = await csv_file.read()
            reader = csv.DictReader(content.splitlines())

            # Определяем общее количество строк для прогресс-бара
            total_rows = sum(1 for _ in reader)
            csv_file.seek(0)  # Возвращаем указатель файла в начало
            reader = csv.DictReader(content.splitlines())  # Повторно инициализируем reader

            batch = []
            # Используем tqdm для отслеживания процесса
            for row in tqdm(reader, total=total_rows, desc="Загрузка шуток", unit="шутка"):
                joke_id = int(row['ID'])
                joke_text = row['Joke']
                joke_roots = get_lemmas(joke_text)

                # Проверка на существование записи
                await cursor.execute("SELECT id FROM jokes WHERE id = ?", (joke_id,))
                if await cursor.fetchone() is None:
                    batch.append((joke_id, joke_text, joke_roots))

                # Если накоплен пакет записей, вставляем их в базу
                if len(batch) >= batch_size:
                    await cursor.executemany("INSERT OR REPLACE INTO jokes (id, joke, root) VALUES (?, ?, ?)", batch)
                    batch = []  # Очищаем пакет
                    await conn.commit()  # Применяем изменения

            # Вставляем оставшиеся записи
            if batch:
                await cursor.executemany("INSERT OR REPLACE INTO jokes (id, joke, root) VALUES (?, ?, ?)", batch)
                await conn.commit()

# Главная функция для запуска
async def main():
    await load_jokes_from_csv('translated_output.csv')
    print("Данные успешно загружены в базу.")

# Запуск программы
if __name__ == '__main__':
    asyncio.run(main())
