#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
НАДЕЖНЫЙ алгоритм приведения заголовков к КАПСУ
Проверяет: все ли БУКВЫ в верхнем регистре (игнорируя пробелы, дефисы, цифры)
"""

import os
import zipfile
import shutil
import re
from bs4 import BeautifulSoup

ORIGINAL_EPUB = "Marcella_Hazan_Essentials_of_Classic_Italian_Cooking_1st_Edition.epub"
TRANSLATED_EPUB = "Hazan_RU_Final_0.3.epub"
TEMP_ORIGINAL = "temp_caps_reliable_orig"
TEMP_TRANSLATED = "temp_caps_reliable_trans"
OUTPUT_FILE = "Hazan_RU_Final_0.3.epub"

def is_all_caps(text):
    """
    Проверяет, все ли БУКВЫ в тексте заглавные
    Игнорирует пробелы, дефисы, цифры, знаки препинания
    """
    # Извлекаем только буквы
    letters = re.findall(r'[a-zA-Z]', text)
    if not letters:
        return False
    
    # Проверяем: все ли буквы заглавные?
    return all(c.isupper() for c in letters)

def fix_all_caps_headers():
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
    
    # Собираем ID заголовков КАПСОМ в оригинале
    print("\n📋 Поиск ВСЕХ заголовков КАПСОМ в оригинале...")
    caps_headers = {}  # {id: original_text}
    
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
                        
                        # Используем надежную проверку
                        if is_all_caps(text):
                            caps_headers[tag_id] = text
    
    print(f"   Найдено {len(caps_headers)} заголовков КАПСОМ\n")
    
    # Показываем первые 10 для проверки
    print("📋 Примеры найденных заголовков КАПСОМ:")
    for i, (tag_id, text) in enumerate(list(caps_headers.items())[:10], 1):
        print(f"   {i}. {text}")
    print()
    
    shutil.rmtree(TEMP_ORIGINAL)
    
    # Специальные переводы (исправления)
    special_translations = {
        'c01-s28': 'ПЕТРУШКА С ПЛОСКИМИ ЛИСТЬЯМИ'  # FLAT-LEAF PARSLEY
    }
    
    # Исправляем перевод
    print("🔄 Приведение к КАПСУ в переводе...")
    fixed_count = 0
    
    for root, dirs, files in os.walk(TEMP_TRANSLATED):
        for f in files:
            if f.endswith(('.html', '.htm', '.xhtml')):
                filepath = os.path.join(root, f)
                with open(filepath, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file.read(), 'html.parser')
                
                file_changed = False
                
                for tag_id in caps_headers.keys():
                    tag = soup.find(id=tag_id)
                    if not tag:
                        continue
                    
                    # Получаем текущий текст
                    current_text = tag.get_text(strip=True)
                    
                    # Если есть специальный перевод
                    if tag_id in special_translations:
                        new_text = special_translations[tag_id]
                        print(f"  🔧 Специальное исправление: {current_text} → {new_text}")
                    else:
                        # Просто приводим к КАПСУ
                        new_text = current_text.upper()
                        
                        # Пропускаем если уже в капсе
                        if current_text == new_text:
                            continue
                        
                        print(f"  ✅ {current_text} → {new_text}")
                    
                    # Заменяем текст во всех текстовых узлах
                    for text_node in tag.find_all(string=True):
                        if text_node.strip():
                            if tag_id in special_translations:
                                # Для специальных переводов заменяем весь текст
                                text_node.replace_with(new_text)
                                break  # Заменили, выходим
                            else:
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
    fix_all_caps_headers()
