#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Поиск дублирующихся заголовков в EPUB
"""

import os
import zipfile
import shutil
from bs4 import BeautifulSoup

EPUB_FILE = "Hazan_RU_Final_0.3.epub"
TEMP_DIR = "temp_find_duplicate_headers"

def find_duplicate_headers():
    print("🔍 Распаковка EPUB...")
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    
    with zipfile.ZipFile(EPUB_FILE, 'r') as z:
        z.extractall(TEMP_DIR)
    
    duplicates = []
    
    html_files = []
    for root, dirs, files in os.walk(TEMP_DIR):
        for f in files:
            if f.endswith(('.html', '.htm', '.xhtml')):
                html_files.append(os.path.join(root, f))
    
    print(f"📂 Проверка {len(html_files)} файлов...\n")
    
    for filepath in html_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        
        # Ищем все заголовки
        headers = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p'])
        
        for i in range(len(headers) - 1):
            current = headers[i]
            next_header = headers[i + 1]
            
            current_text = current.get_text(strip=True)
            next_text = next_header.get_text(strip=True)
            
            # Проверяем на дубликаты (case-insensitive)
            if current_text and next_text:
                if current_text.lower().strip() == next_text.lower().strip():
                    duplicates.append({
                        'file': os.path.basename(filepath),
                        'first_tag': current.name,
                        'first_text': current_text,
                        'first_class': current.get('class', []),
                        'second_tag': next_header.name,
                        'second_text': next_text,
                        'second_class': next_header.get('class', []),
                        'html_first': str(current)[:200],
                        'html_second': str(next_header)[:200]
                    })
    
    shutil.rmtree(TEMP_DIR)
    
    print(f"{'='*60}")
    print(f"📊 НАЙДЕНО ДУБЛИКАТОВ: {len(duplicates)}")
    print(f"{'='*60}\n")
    
    if duplicates:
        # Показываем первые 10 примеров
        for i, dup in enumerate(duplicates[:10], 1):
            print(f"{i}. Файл: {dup['file']}")
            print(f"   Первый:  <{dup['first_tag']} class='{dup['first_class']}'> {dup['first_text']}")
            print(f"   Второй:  <{dup['second_tag']} class='{dup['second_class']}'> {dup['second_text']}")
            print(f"   HTML первого: {dup['html_first']}")
            print(f"   HTML второго: {dup['html_second']}")
            print()
        
        if len(duplicates) > 10:
            print(f"   ... и еще {len(duplicates) - 10} дубликатов\n")
        
        # Статистика по тегам
        print("📊 Статистика по тегам:")
        tag_pairs = {}
        for dup in duplicates:
            pair = f"{dup['first_tag']} → {dup['second_tag']}"
            tag_pairs[pair] = tag_pairs.get(pair, 0) + 1
        
        for pair, count in sorted(tag_pairs.items(), key=lambda x: -x[1]):
            print(f"   {pair}: {count} раз")
    else:
        print("✅ Дубликатов не найдено!")

if __name__ == "__main__":
    find_duplicate_headers()
