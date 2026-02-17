#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Поиск всех подзаголовков в оригинальной английской книге
"""

import os
import zipfile
import shutil
from bs4 import BeautifulSoup

EPUB_FILE = "Marcella_Hazan_Essentials_of_Classic_Italian_Cooking_1st_Edition.epub"
TEMP_DIR = "temp_find_original_subtitles"

def find_original_subtitles():
    print("🔍 Распаковка оригинальной книги...")
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    
    with zipfile.ZipFile(EPUB_FILE, 'r') as z:
        z.extractall(TEMP_DIR)
    
    subtitles = []
    
    html_files = []
    for root, dirs, files in os.walk(TEMP_DIR):
        for f in files:
            if f.endswith(('.html', '.htm', '.xhtml')):
                html_files.append(os.path.join(root, f))
    
    print(f"📂 Проверка {len(html_files)} файлов...\n")
    
    for filepath in html_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        
        # Ищем все h3
        h3_tags = soup.find_all('h3')
        
        for h3 in h3_tags:
            next_elem = h3.find_next_sibling()
            
            if not next_elem:
                continue
            
            # Проверяем: это <p class="center"> с margin-top: 0?
            if next_elem.name == 'p' and 'center' in next_elem.get('class', []):
                style = next_elem.get('style', '')
                if 'margin-top: 0' in style or 'margin-top:0' in style:
                    h3_text = h3.get_text(strip=True)
                    p_text = next_elem.get_text(strip=True)
                    
                    subtitles.append({
                        'file': os.path.basename(filepath),
                        'main': h3_text,
                        'subtitle': p_text
                    })
    
    shutil.rmtree(TEMP_DIR)
    
    print(f"{'='*70}")
    print(f"📊 НАЙДЕНО ПОДЗАГОЛОВКОВ В ОРИГИНАЛЕ: {len(subtitles)}")
    print(f"{'='*70}\n")
    
    if subtitles:
        for i, sub in enumerate(subtitles, 1):
            print(f"{i:2d}. {sub['main']}")
            print(f"    └─ {sub['subtitle']}")
            print()
    else:
        print("❌ Подзаголовков не найдено")

if __name__ == "__main__":
    find_original_subtitles()
