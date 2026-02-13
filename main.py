import zipfile
import os
import shutil

# --- НАСТРОЙКИ ---
INPUT_FILE = 'Marcella_Hazan_Essentials_of_Classic_Italian_Cooking_1st_Edition.epub'
OUTPUT_FILE = 'Hazan_RU_Fixed.epub'
TEMP_DIR = 'temp_epub_debug'

# Словарь замен. 
# Я сократил фразы, чтобы повысить шанс совпадения. 
# Чем короче фраза, тем легче её найти, но опаснее заменить лишнее.
TRANSLATIONS = {
    "Introduction": "Введение",
    "Essentials of Classic Italian Cooking": "Основы классической итальянской кухни",
    "Where Italian Cooking Comes From": "Откуда берет начало итальянская кухня",
    "Italian regional cooking": "итальянская региональная кухня",
    "The cooking of Florence": "Кухня Флоренции",
    "la cucina di casa": "la cucina di casa (домашняя кухня)",
    "home cooking": "домашняя кухня",
    "It is a patchwork": "Это лоскутное одеяло",
    # Добавь простые слова для проверки, работает ли скрипт вообще:
    "Chapter": "Глава",
    "Salt": "Соль",
    "Olive oil": "Оливковое масло"
}

def main():
    # 1. Очистка
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR)

    print(f"--- Распаковка {INPUT_FILE} ---")
    try:
        with zipfile.ZipFile(INPUT_FILE, 'r') as z:
            z.extractall(TEMP_DIR)
    except FileNotFoundError:
        print(f"ОШИБКА: Файл {INPUT_FILE} не найден. Положи его рядом со скриптом.")
        return

    # 2. Перебор файлов
    total_replacements = 0
    files_modified = 0

    print("\n--- Начало поиска и замены ---")
    
    for root, dirs, files in os.walk(TEMP_DIR):
        for file in files:
            # Обрабатываем все веб-страницы внутри книги
            if file.endswith(('.html', '.xhtml', '.htm')):
                filepath = os.path.join(root, file)
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                file_replacements = 0

                # Пробуем заменить каждую фразу из словаря
                for eng, ru in TRANSLATIONS.items():
                    if eng in content:
                        count = content.count(eng)
                        content = content.replace(eng, ru)
                        file_replacements += count
                        print(f"  [{file}] Заменено: '{eng}' -> {count} раз")

                if file_replacements > 0:
                    files_modified += 1
                    total_replacements += file_replacements
                    # Перезаписываем файл только если были изменения
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                else:
                    # Если это файл введения, но мы ничего не нашли - покажем кусочек для отладки
                    if "intro" in file.lower() or "chapter" in file.lower():
                        pass 
                        # Можно раскомментировать строку ниже, чтобы увидеть "внутренности" файла
                        # print(f"  [INFO] В файле {file} совпадений не найдено. Начало текста: {content[:100]}...")

    print(f"\n--- Итог ---")
    print(f"Изменено файлов: {files_modified}")
    print(f"Всего замен текста: {total_replacements}")

    if total_replacements == 0:
        print("\n!!! ВНИМАНИЕ: Скрипт не нашел ни одной фразы для замены.")
        print("Вероятно, текст внутри разбит тегами (например: I<b>tal</b>ian).")
    else:
        # 3. Упаковка
        print(f"\n--- Упаковка в {OUTPUT_FILE} ---")
        with zipfile.ZipFile(OUTPUT_FILE, 'w', zipfile.ZIP_DEFLATED) as z:
            # mimetype первым, без сжатия
            if os.path.exists(os.path.join(TEMP_DIR, 'mimetype')):
                z.write(os.path.join(TEMP_DIR, 'mimetype'), 'mimetype', compress_type=zipfile.ZIP_STORED)
            
            for root, dirs, files in os.walk(TEMP_DIR):
                for file in files:
                    if file == 'mimetype': continue
                    filepath = os.path.join(root, file)
                    arcname = os.path.relpath(filepath, TEMP_DIR)
                    z.write(filepath, arcname)
        
        print("Готово! Проверяй файл.")

    # Очистка
    shutil.rmtree(TEMP_DIR)

if __name__ == "__main__":
    main()