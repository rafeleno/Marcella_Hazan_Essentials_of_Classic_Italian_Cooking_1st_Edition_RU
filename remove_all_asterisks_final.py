#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Агрессивное удаление ВСЕХ астерисков из EPUB
"""

import os
import zipfile
import shutil
from bs4 import BeautifulSoup

EPUB_FILE = "Hazan_RU_Final_0.3_cleaned.epub"
TEMP_DIR = "temp_remove_all_asterisks"
OUTPUT_FILE = "Hazan_RU_Final_0.3.epub"  # Перезаписываем оригинал

def remove_all_asterisks():
    print("🔍 Распаковка EPUB...")
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    
    with zipfile.ZipFile(EPUB_FILE, 'r') as z:
        z.extractall(TEMP_DIR)
    
    total_removed = 0
    
    # Находим HTML файлы
    html_files = []
    for root, dirs, files in os.walk(TEMP_DIR):
        for f in files:
            if f.endswith(('.html', '.htm', '.xhtml')):
                html_files.append(os.path.join(root, f))
    
    print(f"📂 Обработка {len(html_files)} файлов...\n")
    
    for filepath in html_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Считаем астериски ДО удаления
        before = content.count('*')
        
        # ПРОСТО УДАЛЯЕМ ВСЕ АСТЕРИСКИ
        content = content.replace('*', '')
        
        # Считаем сколько удалили
        removed = before - content.count('*')
        if removed > 0:
            total_removed += removed
            print(f"  ✂️  {os.path.basename(filepath)}: удалено {removed} астерисков")
        
        # Сохраняем
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    
    print(f"\n{'='*60}")
    print(f"✅ Всего удалено астерисков: {total_removed}")
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
    
    # Проверка
    print(f"\n🔍 Финальная проверка...")
    with zipfile.ZipFile(OUTPUT_FILE, 'r') as z:
        z.extractall("temp_verify")
    
    asterisk_count = 0
    for root, dirs, files in os.walk("temp_verify"):
        for f in files:
            if f.endswith(('.html', '.htm', '.xhtml')):
                with open(os.path.join(root, f), 'r', encoding='utf-8') as file:
                    asterisk_count += file.read().count('*')
    
    shutil.rmtree("temp_verify")
    
    if asterisk_count == 0:
        print("✅ Астерисков не осталось!")
    else:
        print(f"⚠️  Осталось {asterisk_count} астерисков (возможно в атрибутах HTML)")

if __name__ == "__main__":
    remove_all_asterisks()
