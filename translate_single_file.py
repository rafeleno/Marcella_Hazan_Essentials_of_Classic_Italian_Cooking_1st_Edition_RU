import os
import shutil
from translate_epub_openai import process_file, save_progress, load_progress

# Настройки из основного файла
TEMP_DIR = "temp_epub_translate_openai"
TARGET_FILE = "Haza_9780307958303_epub_c04_r1.htm" # Томатные соусы

def main():
    print(f"=== ПРИНУДИТЕЛЬНЫЙ ПЕРЕВОД ФАЙЛА {TARGET_FILE} ===")
    
    filepath = os.path.join(TEMP_DIR, "OEBPS", TARGET_FILE)
    if not os.path.exists(filepath):
        print(f"Файл {filepath} не найден! Проверьте, распакован ли EPUB.")
        return

    try:
        process_file(filepath)
        print("✅ Файл успешно переведен!")
        
        # Обновляем прогресс (для порядка)
        progress = load_progress()
        if TARGET_FILE not in progress['completed_files']:
            progress['completed_files'].append(TARGET_FILE)
            save_progress(progress)
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main()
