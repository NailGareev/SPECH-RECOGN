import sqlite3

# Подключение к базе данных
def connect_db():
    conn = sqlite3.connect('chatbot.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS jokes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        joke TEXT NOT NULL)''')
    conn.commit()
    return conn, cursor

# Добавление новой шутки
def add_joke():
    joke = input("Введите новую шутку: ").strip()
    if joke:
        conn, cursor = connect_db()
        cursor.execute("INSERT INTO jokes (joke) VALUES (?)", (joke,))
        conn.commit()
        conn.close()
        print("✅ Шутка добавлена!")
    else:
        print("⚠️ Шутка не может быть пустой!")

# Удаление шутки по ID
def delete_joke():
    view_jokes()
    try:
        joke_id = int(input("Введите ID шутки, которую хотите удалить: ").strip())
        conn, cursor = connect_db()
        cursor.execute("DELETE FROM jokes WHERE id = ?", (joke_id,))
        if cursor.rowcount > 0:
            print("✅ Шутка удалена!")
        else:
            print("⚠️ Шутка с таким ID не найдена!")
        conn.commit()
        conn.close()
    except ValueError:
        print("⚠️ Некорректный ID!")

# Просмотр всех шуток
def view_jokes():
    conn, cursor = connect_db()
    cursor.execute("SELECT id, joke FROM jokes")
    jokes = cursor.fetchall()
    conn.close()
    print("\n📋 Список шуток:")
    if jokes:
        for joke_id, joke in jokes:
            print(f"[{joke_id}] {joke}")
    else:
        print("⚠️ В базе данных пока нет шуток!")

# Главное меню
def main_menu():
    while True:
        print("\n=== Управление шутками ===")
        print("1. Добавить шутку")
        print("2. Удалить шутку")
        print("3. Просмотреть все шутки")
        print("4. Выйти")

        choice = input("Выберите действие: ").strip()
        if choice == "1":
            add_joke()
        elif choice == "2":
            delete_joke()
        elif choice == "3":
            view_jokes()
        elif choice == "4":
            print("👋 Выход из программы. До свидания!")
            break
        else:
            print("⚠️ Некорректный ввод. Попробуйте снова.")

# Запуск программы
if __name__ == "__main__":
    main_menu()
