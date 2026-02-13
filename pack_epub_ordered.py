import zipfile
import os
import re

TEMP_DIR = "temp_epub_translate_openai"
OUTPUT_EPUB = "Hazan_RU_OpenAI_TEST_5_ordered.epub"
OPF_FILE = "Haza_9780307958303_epub_opf_r1.opf"

print(f"📦 Сборка УПОРЯДОЧЕННОГО EPUB из {TEMP_DIR}...")
if os.path.exists(OUTPUT_EPUB):
    os.remove(OUTPUT_EPUB)

def get_ordered_files_from_opf(opf_path):
    """Считывает порядок файлов из manifest/spine в OPF"""
    files = []
    try:
        with open(opf_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 1. Находим spine (порядок чтения)
        spine_items = re.findall(r'<itemref idref="([^"]+)"', content)
        
        # 2. Находим manifest (пути к файлам)
        manifest_items = {}
        for match in re.finditer(r'<item href="([^"]+)" id="([^"]+)"', content):
            manifest_items[match.group(2)] = match.group(1) # id -> href
            
        # 3. Собираем файлы по spine
        processed_ids = set()
        for item_id in spine_items:
            if item_id in manifest_items:
                files.append(manifest_items[item_id])
                processed_ids.add(item_id)
                
        # 4. Добавляем остальные файлы из manifest (css, images, ncx...), которых нет в spine
        for item_id, href in manifest_items.items():
            if item_id not in processed_ids:
                files.append(href)
                
    except Exception as e:
        print(f"Ошибка парсинга OPF: {e}")
        
    return files

with zipfile.ZipFile(OUTPUT_EPUB, 'w', zipfile.ZIP_DEFLATED) as epub:
    # 1. Mimetype (первый, без сжатия)
    mimetype_path = os.path.join(TEMP_DIR, 'mimetype')
    if os.path.exists(mimetype_path):
        epub.write(mimetype_path, 'mimetype', compress_type=zipfile.ZIP_STORED)
        
    # 2. META-INF (обязательно второй)
    container_path = os.path.join(TEMP_DIR, 'META-INF', 'container.xml')
    if os.path.exists(container_path):
        epub.write(container_path, 'META-INF/container.xml')
        
    # 3. OPF файл (обязательно)
    opf_full_path = os.path.join(TEMP_DIR, OPF_FILE)
    if os.path.exists(opf_full_path):
        epid_abspath = os.path.abspath(opf_full_path)
        # Получаем список файлов в порядке чтения
        ordered_files = get_ordered_files_from_opf(opf_full_path)
        
        # Записываем сам OPF
        epub.write(opf_full_path, OPF_FILE)
        
        # 4. Записываем файлы по порядку
        added_files = {'mimetype', 'META-INF/container.xml', OPF_FILE}
        
        for rel_path in ordered_files:
            full_path = os.path.join(TEMP_DIR, rel_path)
            if os.path.exists(full_path):
                epub.write(full_path, rel_path)
                added_files.add(rel_path)
            else:
                print(f"⚠️ Файл из OPF не найден: {rel_path} (ищем в {full_path})")
                
        # 5. Добавляем всё, что забыли (на всякий случай)
        for root, dirs, files in os.walk(TEMP_DIR):
            for file in files:
                if file.startswith('.'): continue
                path = os.path.join(root, file)
                arcname = os.path.relpath(path, TEMP_DIR)
                
                if arcname not in added_files:
                    # print(f"  Добавляю остаток: {arcname}")
                    epub.write(path, arcname)

print(f"✅ УСПЕШНО! Файл сохранен как: {OUTPUT_EPUB}")
