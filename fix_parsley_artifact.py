#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Исправление артефакта в заголовке ПЕТРУШКА
"""

import os
import zipfile
import shutil
from bs4 import BeautifulSoup, NavigableString

EPUB_FILE = "Hazan_RU_Final_0.3.epub"
TEMP_DIR = "temp_fix_parsley"
OUTPUT_FILE = "Hazan_RU_Final_0.3.epub"

def fix_parsley_header():
    print("🔍 Распаковка EPUB...")
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    
    with zipfile.ZipFile(EPUB_FILE, 'r') as z:
        z.extractall(TEMP_DIR)
    
    print("🔄 Исправление заголовка ПЕТРУШКА...\n")
    
    for root, dirs, files in os.walk(TEMP_DIR):
        for f in files:
            if f.endswith(('.html', '.htm', '.xhtml')):
                filepath = os.path.join(root, f)
                with open(filepath, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file.read(), 'html.parser')
                
                # Ищем заголовок с id='c01-s28'
                tag = soup.find(id='c01-s28')
                if not tag:
                    continue
                
                print(f"  Найден в файле: {os.path.basename(filepath)}")
                print(f"  Текущий текст: {tag.get_text(strip=True)}")
                
                # Находим <span> внутри
                span = tag.find('span')
                if span:
                    # Сохраняем ссылку <a> если есть
                    link = span.find('a')
                    
                    # Очищаем содержимое span
                    span.clear()
                    
                    # Добавляем новый текст
                    span.append('ПЕТРУШКА С ПЛОСКИМИ ЛИСТЬЯМИ')
                    
                    # Возвращаем ссылку
                    if link:
                        span.append(link)
                    
                    print(f"  Новый текст: {tag.get_text(strip=True)}")
                    print(f"  ✅ Исправлено!\n")
                    
                    with open(filepath, 'w', encoding='utf-8') as file:
                        file.write(str(soup))
    
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
    
    shutil.rmtree(TEMP_DIR)
    
    print(f"🎉 Готово! Файл: {OUTPUT_FILE}")
    print(f"📏 Размер: {os.path.getsize(OUTPUT_FILE) / 1024 / 1024:.1f} MB")

if __name__ == "__main__":
    fix_parsley_header()
