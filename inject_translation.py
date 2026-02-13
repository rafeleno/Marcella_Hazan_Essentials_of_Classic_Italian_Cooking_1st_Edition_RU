import zipfile
import os
import shutil

INPUT_EPUB = "Marcella_Hazan_Essentials_of_Classic_Italian_Cooking_1st_Edition.epub"
OUTPUT_EPUB = "Hazan_RU_Final_0.2.epub"
TEMP_DIR = "temp_epub_final_1_0"

print(f"🔄 Создание {OUTPUT_EPUB} на основе оригинала...")
if os.path.exists(OUTPUT_EPUB):
    os.remove(OUTPUT_EPUB)
shutil.copy2(INPUT_EPUB, OUTPUT_EPUB)

print(f"💉 Внедрение переведенных файлов из {TEMP_DIR}...")

# Собираем список файлов для замены
files_to_replace = {}
for root, dirs, files in os.walk(TEMP_DIR):
    for file in files:
        if file.endswith('.htm') or file.endswith('.html') or file.endswith('.css'):
            full_path = os.path.join(root, file)
            # Вычисляем путь внутри архива (относительно TEMP_DIR)
            arcname = os.path.relpath(full_path, TEMP_DIR)
            files_to_replace[arcname] = full_path

# Мы не можем просто так обновить файл в zip через zipfile (это append, а не replace, и читалки могут запутаться с дубликатами).
# Поэтому правильный способ:
# 1. Распаковать оригинал (или прочитать его в память)
# 2. Перезаписать нужные файлы
# 3. Собрать новый архив

# Но есть способ проще:
# Создать новый ZipFile на запись, и копировать из оригинала всё, кроме заменяемых.
# А заменяемые брать из TEMP_DIR.

temp_output = OUTPUT_EPUB + ".tmp"
with zipfile.ZipFile(INPUT_EPUB, 'r') as zin:
    with zipfile.ZipFile(temp_output, 'w', zipfile.ZIP_DEFLATED) as zout:
        # Копируем mimetype первым (без сжатия)
        try:
            mimetype = zin.read("mimetype")
            zout.writestr("mimetype", mimetype, compress_type=zipfile.ZIP_STORED)
        except KeyError:
            pass # Если нет mimetype, ну и ладно (хотя должен быть)

        # Проходим по всем файлам оригинала
        for item in zin.infolist():
            if item.filename == "mimetype":
                continue
                
            # Если файл есть в списке замен - берем наш
            if item.filename in files_to_replace:
                # print(f"  Замена: {item.filename}")
                zout.write(files_to_replace[item.filename], item.filename)
                del files_to_replace[item.filename] # Удаляем из списка, чтобы знать, что обработали
            else:
                # Иначе копируем из оригинала
                data = zin.read(item.filename)
                zout.writestr(item, data)

        # Если остались файлы в files_to_replace (новые?), добавляем их
        for arcname, filepath in files_to_replace.items():
            # print(f"  Добавление нового: {arcname}")
            zout.write(filepath, arcname)

# Заменяем файл
shutil.move(temp_output, OUTPUT_EPUB)
print(f"✅ УСПЕШНО! Файл сохранен как: {OUTPUT_EPUB}")
