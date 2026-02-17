#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ПРИНУДИТЕЛЬНАЯ замена подзаголовков на итальянские
Удаляет ВСЕ существующие подзаголовки и добавляет только итальянские
"""

import os
import zipfile
import shutil
from bs4 import BeautifulSoup

ORIGINAL_EPUB = "Marcella_Hazan_Essentials_of_Classic_Italian_Cooking_1st_Edition.epub"
TRANSLATED_EPUB = "Hazan_RU_Final_0.3.epub"
TEMP_ORIGINAL = "temp_original_force"
TEMP_TRANSLATED = "temp_translated_force"
OUTPUT_FILE = "Hazan_RU_Final_0.3.epub"

def force_replace_subtitles():
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
    
    # Шаг 1: Собираем итальянские подзаголовки из оригинала
    print("\n📋 Сбор итальянских подзаголовков...")
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
                            original_subtitles[h3_id] = str(next_elem)
    
    print(f"   Найдено {len(original_subtitles)} итальянских подзаголовков\n")
    
    # Шаг 2: ПРИНУДИТЕЛЬНАЯ замена в переводе
    print("🔄 Принудительная замена подзаголовков...")
    replaced_count = 0
    removed_old = 0
    
    for root, dirs, files in os.walk(TEMP_TRANSLATED):
        for f in files:
            if f.endswith(('.html', '.htm', '.xhtml')):
                filepath = os.path.join(root, f)
                with open(filepath, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file.read(), 'html.parser')
                
                file_changed = False
                
                # Для каждого h3 с ID из списка
                for h3_id, italian_subtitle_html in original_subtitles.items():
                    h3 = soup.find('h3', id=h3_id)
                    if not h3:
                        continue
                    
                    # УДАЛЯЕМ ВСЕ следующие <p class="center" margin-top:0>
                    # (может быть несколько дубликатов!)
                    while True:
                        next_elem = h3.find_next_sibling()
                        if not next_elem:
                            break
                        
                        # Это подзаголовок?
                        if next_elem.name == 'p' and 'center' in next_elem.get('class', []):
                            style = next_elem.get('style', '')
                            if 'margin-top: 0' in style or 'margin-top:0' in style:
                                old_text = next_elem.get_text(strip=True)
                                print(f"  🗑️  Удаляю старый подзаголовок: {old_text}")
                                next_elem.decompose()
                                removed_old += 1
                                file_changed = True
                            else:
                                break  # Это уже не подзаголовок
                        else:
                            break  # Следующий элемент не <p class="center">
                    
                    # Добавляем ТОЛЬКО итальянский подзаголовок
                    italian_subtitle = BeautifulSoup(italian_subtitle_html, 'html.parser').find()
                    if italian_subtitle:
                        h3.insert_after(italian_subtitle)
                        italian_text = italian_subtitle.get_text(strip=True)
                        if italian_text:  # Не выводим пустые
                            print(f"  ✅ Добавлен: {italian_text}")
                        replaced_count += 1
                        file_changed = True
                
                if file_changed:
                    with open(filepath, 'w', encoding='utf-8') as file:
                        file.write(str(soup))
    
    print(f"\n{'='*70}")
    print(f"🗑️  Удалено старых подзаголовков: {removed_old}")
    print(f"✅ Добавлено итальянских подзаголовков: {replaced_count}")
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
    force_replace_subtitles()
