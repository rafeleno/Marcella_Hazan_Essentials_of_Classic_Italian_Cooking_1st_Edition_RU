import zipfile
import os

TEMP_DIR = "temp_epub_translate_openai"
OUTPUT_EPUB = "Hazan_RU_OpenAI_TEST_5_repacked.epub"

print(f"📦 Сборка финального EPUB из {TEMP_DIR}...")
if os.path.exists(OUTPUT_EPUB):
    os.remove(OUTPUT_EPUB)

with zipfile.ZipFile(OUTPUT_EPUB, 'w', zipfile.ZIP_DEFLATED) as epub:
    # 1. Mimetype первым, без сжатия
    mimetype_path = os.path.join(TEMP_DIR, 'mimetype')
    if os.path.exists(mimetype_path):
        epub.write(mimetype_path, 'mimetype', compress_type=zipfile.ZIP_STORED)
    else:
        print("⚠️ Внимание: файл mimetype не найден!")

    # 2. Остальные файлы
    for root, dirs, files in os.walk(TEMP_DIR):
        for file in sorted(files): # Сортируем файлы для детерминизма (как в старом скрипте?)
            if file == 'mimetype': continue
            # Исключаем лишние системные файлы
            if file.startswith('.'): continue
            
            path = os.path.join(root, file)
            arcname = os.path.relpath(path, TEMP_DIR)
            epub.write(path, arcname)

print(f"✅ УСПЕШНО! Файл сохранен как: {OUTPUT_EPUB}")
