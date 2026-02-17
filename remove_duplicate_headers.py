#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Удаление дублирующихся заголовков из EPUB
Удаляет <p class="center"> если он дублирует предыдущий <h3>
"""

import os
import zipfile
import shutil
from bs4 import BeautifulSoup

EPUB_FILE = "Hazan_RU_Final_0.3.epub"
TEMP_DIR = "temp_remove_duplicates"
OUTPUT_FILE = "Hazan_RU_Final_0.3.epub"

def remove_duplicate_headers():
    print("🔍 Распаковка EPUB...")
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    
    with zipfile.ZipFile(EPUB_FILE, 'r') as z:
        z.extractall(TEMP_DIR)
    
    total_removed = 0
    
    html_files = []
    for root, dirs, files in os.walk(TEMP_DIR):
        for f in files:
            if f.endswith(('.html', '.htm', '.xhtml')):
                html_files.append(os.path.join(root, f))
    
    print(f"📂 Обработка {len(html_files)} файлов...\n")
    
    for filepath in html_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        
        file_changed = False
        removed_in_file = 0
        
        # Ищем все заголовки h3
        h3_tags = soup.find_all('h3')
        
        for h3 in h3_tags:
            # Получаем следующий элемент
            next_elem = h3.find_next_sibling()
            
            if not next_elem:
                continue
            
            # Проверяем: это <p class="center">?
            if next_elem.name == 'p' and 'center' in next_elem.get('class', []):
                h3_text = h3.get_text(strip=True).lower()
                p_text = next_elem.get_text(strip=True).lower()
                
                # Если тексты идентичны (case-insensitive)
                if h3_text == p_text:
                    print(f"  🗑️  Удаляю дубликат: «{next_elem.get_text(strip=True)}»")
                    next_elem.decompose()  # Удаляем элемент
                    removed_in_file += 1
                    file_changed = True
        
        if file_changed:
            total_removed += removed_in_file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(str(soup))
    
    print(f"\n{'='*60}")
    print(f"✅ Удалено дубликатов: {total_removed}")
    print(f"{'='*60}\n")
    
    # Пересборка EPUB
    print(f"📦 Сборка {OUTPUT_FILE}...")
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
    
    cwd = os.getcwd()
    os.chdir(TEMP_DIR)
    os.system(f"zip -0 -X ../{OUTPUT_FILE} mimetype >/dev/null 2>&1")
    os.system(f"zip -r -q ../{OUTPUT_FILE} META-INF OEBPS -x '*.DS_Store'")
    
    if os.path.exists("Haza_9780307958303_epub_opf_r1.opf"):
        os.system(f"zip -r -q ../{OUTPUT_FILE} *.opf *.ncx")
    
    os.chdir(cwd)
    
    # Очистка
    shutil.rmtree(TEMP_DIR)
    
    print(f"🎉 Готово! Файл: {OUTPUT_FILE}")
    print(f"📏 Размер: {os.path.getsize(OUTPUT_FILE) / 1024 / 1024:.1f} MB")

if __name__ == "__main__":
    remove_duplicate_headers()
