#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Исправление регистра заголовков на КАПС (только те, что в оригинале CAPS)
"""

import os
import zipfile
import shutil
from bs4 import BeautifulSoup

ORIGINAL_EPUB = "Marcella_Hazan_Essentials_of_Classic_Italian_Cooking_1st_Edition.epub"
TRANSLATED_EPUB = "Hazan_RU_Final_0.3.epub"
TEMP_ORIGINAL = "temp_fix_caps_orig"
TEMP_TRANSLATED = "temp_fix_caps_trans"
OUTPUT_FILE = "Hazan_RU_Final_0.3.epub"

def fix_header_caps():
    print("🔍 Распаковка оригинала...")
    if os.path.exists(TEMP_ORIGINAL):
        shutil.rmtree(TEMP_ORIGINAL)
    with zipfile.ZipFile(ORIGINAL_EPUB, 'r') as z:
        z.extractall(TEMP_ORIGINAL)
    
    print("🔍 Распаковка перевода...")
    if os.path.exists(TEMP_TRANSLATED):
        shutil.rmtree(TEMP_TRANSLATED)
    with zipfile.ZipFile(TRANSLATED_EPUB, 'r') as z:
        z.extractall(TEMP_TRANSLATED)
    
    # Собираем ID заголовков, которые в оригинале CAPS
    print("\n📋 Поиск заголовков КАПСОМ в оригинале...")
    caps_ids = set()
    
    for root, dirs, files in os.walk(TEMP_ORIGINAL):
        for f in files:
            if f.endswith(('.html', '.htm', '.xhtml')):
                filepath = os.path.join(root, f)
                with open(filepath, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file.read(), 'html.parser')
                
                for tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    for tag in soup.find_all(tag_name):
                        tag_id = tag.get('id')
                        if not tag_id:
                            continue
                        
                        text = tag.get_text(strip=True)
                        if text.isupper() and text.isalpha():
                            caps_ids.add(tag_id)
    
    print(f"   Найдено {len(caps_ids)} заголовков КАПСОМ\n")
    
    shutil.rmtree(TEMP_ORIGINAL)
    
    # Исправляем перевод
    print("🔄 Исправление регистра в переводе...")
    fixed_count = 0
    
    for root, dirs, files in os.walk(TEMP_TRANSLATED):
        for f in files:
            if f.endswith(('.html', '.htm', '.xhtml')):
                filepath = os.path.join(root, f)
                with open(filepath, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file.read(), 'html.parser')
                
                file_changed = False
                
                for tag_id in caps_ids:
                    tag = soup.find(id=tag_id)
                    if not tag:
                        continue
                    
                    # Получаем текст
                    text = tag.get_text(strip=True)
                    
                    # Если уже в верхнем регистре, пропускаем
                    if text.isupper():
                        continue
                    
                    # Преобразуем в КАПС
                    caps_text = text.upper()
                    
                    print(f"  ✅ {text} → {caps_text}")
                    
                    # Заменяем текст (сохраняя HTML структуру внутри)
                    # Если внутри есть теги (span, a и т.д.), обрабатываем текстовые узлы
                    for text_node in tag.find_all(string=True):
                        if text_node.strip():
                            text_node.replace_with(text_node.upper())
                    
                    fixed_count += 1
                    file_changed = True
                
                if file_changed:
                    with open(filepath, 'w', encoding='utf-8') as file:
                        file.write(str(soup))
    
    print(f"\n{'='*70}")
    print(f"✅ Исправлено заголовков: {fixed_count}")
    print(f"{'='*70}\n")
    
    # Пересборка EPUB
    print(f"📦 Сборка {OUTPUT_FILE}...")
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
    
    cwd = os.getcwd()
    os.chdir(TEMP_TRANSLATED)
    os.system(f"zip -0 -X ../{OUTPUT_FILE} mimetype >/dev/null 2>&1")
    os.system(f"zip -r -q ../{OUTPUT_FILE} META-INF OEBPS -x '*.DS_Store'")
    
    if os.path.exists("Haza_9780307958303_epub_opf_r1.opf"):
        os.system(f"zip -r -q ../{OUTPUT_FILE} *.opf *.ncx")
    
    os.chdir(cwd)
    
    shutil.rmtree(TEMP_TRANSLATED)
    
    print(f"🎉 Готово! Файл: {OUTPUT_FILE}")
    print(f"📏 Размер: {os.path.getsize(OUTPUT_FILE) / 1024 / 1024:.1f} MB")

if __name__ == "__main__":
    fix_header_caps()
