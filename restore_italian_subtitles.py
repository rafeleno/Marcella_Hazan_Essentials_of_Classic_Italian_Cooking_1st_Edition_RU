#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Восстановление итальянских подзаголовков в переводе
"""

import os
import zipfile
import shutil
from bs4 import BeautifulSoup

ORIGINAL_EPUB = "Marcella_Hazan_Essentials_of_Classic_Italian_Cooking_1st_Edition.epub"
TRANSLATED_EPUB = "Hazan_RU_Final_0.3.epub"
TEMP_ORIGINAL = "temp_original_subtitles"
TEMP_TRANSLATED = "temp_translated_subtitles"
OUTPUT_FILE = "Hazan_RU_Final_0.3.epub"

def restore_italian_subtitles():
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
    
    # Шаг 1: Собираем все подзаголовки из оригинала (с ID)
    print("\n📋 Сбор подзаголовков из оригинала...")
    original_subtitles = {}  # {h3_id: italian_subtitle_html}
    
    for root, dirs, files in os.walk(TEMP_ORIGINAL):
        for f in files:
            if f.endswith(('.html', '.htm', '.xhtml')):
                filepath = os.path.join(root, f)
                with open(filepath, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file.read(), 'html.parser')
                
                h3_tags = soup.find_all('h3')
                for h3 in h3_tags:
                    h3_id = h3.get('id')
                    if not h3_id:
                        continue
                    
                    next_elem = h3.find_next_sibling()
                    if not next_elem:
                        continue
                    
                    # Это подзаголовок?
                    if next_elem.name == 'p' and 'center' in next_elem.get('class', []):
                        style = next_elem.get('style', '')
                        if 'margin-top: 0' in style or 'margin-top:0' in style:
                            # Сохраняем весь HTML подзаголовка
                            original_subtitles[h3_id] = str(next_elem)
    
    print(f"   Найдено {len(original_subtitles)} подзаголовков с ID\n")
    
    # Шаг 2: Применяем подзаголовки к переводу
    print("🔄 Восстановление подзаголовков в переводе...")
    restored_count = 0
    removed_duplicates = 0
    
    for root, dirs, files in os.walk(TEMP_TRANSLATED):
        for f in files:
            if f.endswith(('.html', '.htm', '.xhtml')):
                filepath = os.path.join(root, f)
                with open(filepath, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file.read(), 'html.parser')
                
                file_changed = False
                
                # Ищем h3 с ID из нашего списка
                for h3_id, italian_subtitle_html in original_subtitles.items():
                    h3 = soup.find('h3', id=h3_id)
                    if not h3:
                        continue
                    
                    # Проверяем следующий элемент
                    next_elem = h3.find_next_sibling()
                    
                    # Если есть русский дубликат — удаляем его
                    if next_elem and next_elem.name == 'p' and 'center' in next_elem.get('class', []):
                        style = next_elem.get('style', '')
                        if 'margin-top: 0' in style or 'margin-top:0' in style:
                            # Проверяем: это дубликат (русский текст)?
                            h3_text = h3.get_text(strip=True).lower()
                            p_text = next_elem.get_text(strip=True).lower()
                            
                            if h3_text == p_text:
                                print(f"  🗑️  Удаляю русский дубликат: {next_elem.get_text(strip=True)}")
                                next_elem.decompose()
                                removed_duplicates += 1
                                file_changed = True
                    
                    # Добавляем итальянский подзаголовок
                    italian_subtitle = BeautifulSoup(italian_subtitle_html, 'html.parser').find()
                    if italian_subtitle:
                        h3.insert_after(italian_subtitle)
                        print(f"  ✅ Добавлен подзаголовок: {italian_subtitle.get_text(strip=True)}")
                        restored_count += 1
                        file_changed = True
                
                if file_changed:
                    with open(filepath, 'w', encoding='utf-8') as file:
                        file.write(str(soup))
    
    print(f"\n{'='*70}")
    print(f"✅ Удалено русских дубликатов: {removed_duplicates}")
    print(f"✅ Восстановлено итальянских подзаголовков: {restored_count}")
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
    
    # Очистка
    shutil.rmtree(TEMP_ORIGINAL)
    shutil.rmtree(TEMP_TRANSLATED)
    
    print(f"🎉 Готово! Файл: {OUTPUT_FILE}")
    print(f"📏 Размер: {os.path.getsize(OUTPUT_FILE) / 1024 / 1024:.1f} MB")

if __name__ == "__main__":
    restore_italian_subtitles()
