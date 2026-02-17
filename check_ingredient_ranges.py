#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Поиск ТОЛЬКО диапазонов количества (ингредиентов)
Исключаем: "разогрейте до", "может быть до", "или до"
"""

import os
import re
import zipfile
import shutil
from bs4 import BeautifulSoup

EPUB_FILE = "Hazan_RU_Final_0.3.epub"
TEMP_DIR = "temp_check_ingredient_ranges"

def check_ingredient_ranges():
    print("🔍 Распаковка EPUB...")
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    
    with zipfile.ZipFile(EPUB_FILE, 'r') as z:
        z.extractall(TEMP_DIR)
    
    # Паттерн для диапазонов КОЛИЧЕСТВА (не температуры, не времени)
    # Ищем: ЧИСЛО + "до" + ЧИСЛО (где числа могут быть дробями)
    # НО исключаем контексты типа "духовку до", "разогрейте до", "может быть до"
    number = r'(?:\d+)?[¼½¾⅓⅔⅛⅜⅝⅞]|\d+(?:[.,]\d+)?'
    
    # Паттерн: число + "до" + число
    # С негативным lookbehind для исключения "духовку до", "разогрейте до" и т.д.
    pattern = re.compile(
        rf'(?<!духовку\s)(?<!разогрейте\s)(?<!температуру\s)(?<!быть\s)(?<!или\s)'
        rf'(?<!может быть\s)(?<!охладите\s)(?<!минут\s)(?<!часа\s)(?<!дней\s)'
        rf'\b({number})\s+до\s+({number})\b',
        re.IGNORECASE
    )
    
    found_cases = []
    
    html_files = []
    for root, dirs, files in os.walk(TEMP_DIR):
        for f in files:
            if f.endswith(('.html', '.htm', '.xhtml')):
                html_files.append(os.path.join(root, f))
    
    print(f"📂 Проверка {len(html_files)} файлов...\n")
    
    for filepath in html_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        for text_node in soup.find_all(string=True):
            if text_node.parent.name in ['script', 'style']:
                continue
            
            text = str(text_node)
            matches = pattern.finditer(text)
            
            for match in matches:
                # Получаем контекст (30 символов до и после)
                start = max(0, match.start() - 30)
                end = min(len(text), match.end() + 30)
                context = text[start:end]
                
                found_cases.append({
                    'file': os.path.basename(filepath),
                    'match': match.group(0),
                    'context': context.strip()
                })
    
    shutil.rmtree(TEMP_DIR)
    
    print(f"{'='*60}")
    print(f"📊 РЕЗУЛЬТАТЫ:")
    print(f"{'='*60}\n")
    
    if found_cases:
        print(f"⚠️  Найдено диапазонов количества: {len(found_cases)}\n")
        
        for i, case in enumerate(found_cases[:30], 1):
            print(f"{i}. Файл: {case['file']}")
            print(f"   Найдено: «{case['match']}»")
            print(f"   Контекст: ...{case['context']}...")
            print()
    else:
        print("✅ Диапазонов типа 'X до Y' (для количества) не найдено!")

if __name__ == "__main__":
    check_ingredient_ranges()
