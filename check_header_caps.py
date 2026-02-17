#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка регистра заголовков в оригинале и переводе
"""

import os
import zipfile
import shutil
from bs4 import BeautifulSoup

ORIGINAL_EPUB = "Marcella_Hazan_Essentials_of_Classic_Italian_Cooking_1st_Edition.epub"
TRANSLATED_EPUB = "Hazan_RU_Final_0.3.epub"
TEMP_ORIGINAL = "temp_check_caps_orig"
TEMP_TRANSLATED = "temp_check_caps_trans"

def check_header_caps():
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
    
    # Собираем заголовки из оригинала
    print("\n📋 Анализ заголовков в оригинале...")
    original_headers = {}  # {id: {'text': text, 'is_caps': bool, 'tag': tag}}
    
    for root, dirs, files in os.walk(TEMP_ORIGINAL):
        for f in files:
            if f.endswith(('.html', '.htm', '.xhtml')):
                filepath = os.path.join(root, f)
                with open(filepath, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file.read(), 'html.parser')
                
                # Ищем все заголовки h1-h6
                for tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    for tag in soup.find_all(tag_name):
                        tag_id = tag.get('id')
                        if not tag_id:
                            continue
                        
                        text = tag.get_text(strip=True)
                        # Проверяем: весь текст в верхнем регистре?
                        is_caps = text.isupper() and text.isalpha()
                        
                        original_headers[tag_id] = {
                            'text': text,
                            'is_caps': is_caps,
                            'tag': tag_name
                        }
    
    print(f"   Найдено {len(original_headers)} заголовков с ID\n")
    
    # Проверяем перевод
    print("📋 Проверка перевода...")
    mismatches = []
    
    for root, dirs, files in os.walk(TEMP_TRANSLATED):
        for f in files:
            if f.endswith(('.html', '.htm', '.xhtml')):
                filepath = os.path.join(root, f)
                with open(filepath, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file.read(), 'html.parser')
                
                for tag_id, orig_data in original_headers.items():
                    tag = soup.find(id=tag_id)
                    if not tag:
                        continue
                    
                    ru_text = tag.get_text(strip=True)
                    ru_is_caps = ru_text.isupper()
                    
                    # Если в оригинале CAPS, а в переводе нет
                    if orig_data['is_caps'] and not ru_is_caps:
                        mismatches.append({
                            'id': tag_id,
                            'original': orig_data['text'],
                            'translated': ru_text,
                            'tag': orig_data['tag']
                        })
    
    shutil.rmtree(TEMP_ORIGINAL)
    shutil.rmtree(TEMP_TRANSLATED)
    
    # Отчет
    print(f"{'='*70}")
    print(f"📊 РЕЗУЛЬТАТЫ:")
    print(f"{'='*70}\n")
    
    # Статистика по оригиналу
    caps_count = sum(1 for h in original_headers.values() if h['is_caps'])
    print(f"В оригинале:")
    print(f"  Всего заголовков: {len(original_headers)}")
    print(f"  Заголовков КАПСОМ: {caps_count}")
    print(f"  Заголовков обычным текстом: {len(original_headers) - caps_count}\n")
    
    if mismatches:
        print(f"⚠️  НЕСООТВЕТСТВИЯ (в оригинале CAPS, в переводе нет): {len(mismatches)}\n")
        
        for i, m in enumerate(mismatches[:20], 1):
            print(f"{i:2d}. <{m['tag']} id='{m['id']}'>")
            print(f"    Оригинал:  {m['original']}")
            print(f"    Перевод:   {m['translated']}")
            print()
        
        if len(mismatches) > 20:
            print(f"   ... и еще {len(mismatches) - 20} несоответствий")
    else:
        print("✅ Все заголовки в правильном регистре!")

if __name__ == "__main__":
    check_header_caps()
