#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Поиск всех конструкций с "до" в EPUB
"""

import os
import re
import zipfile
import shutil
from bs4 import BeautifulSoup

EPUB_FILE = "Hazan_RU_Final_0.3.epub"
TEMP_DIR = "temp_check_ranges"

def check_ranges():
    print("🔍 Распаковка EPUB...")
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    
    with zipfile.ZipFile(EPUB_FILE, 'r') as z:
        z.extractall(TEMP_DIR)
    
    # Паттерн для поиска конструкций с "до"
    # Ищем любые слова/числа + "до" + числа/дроби
    pattern = re.compile(r'([^\s.!?]{0,15})\s+(до)\s+([¼½¾⅓⅔⅛⅜⅝⅞\d]+[¼½¾⅓⅔⅛⅜⅝⅞]?)', re.IGNORECASE)
    
    found_cases = []
    
    # Находим HTML файлы
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
        
        # Ищем в текстовых узлах
        for text_node in soup.find_all(string=True):
            if text_node.parent.name in ['script', 'style']:
                continue
            
            text = str(text_node)
            matches = pattern.findall(text)
            
            if matches:
                for match in matches:
                    before, do_word, after = match
                    # Фильтруем ложные срабатывания (например "подо", "судо")
                    if before and before[-1].isalpha() and before[-2:].lower() in ['по', 'су', 'пе']:
                        continue
                    
                    context = f"{before} {do_word} {after}"
                    found_cases.append({
                        'file': os.path.basename(filepath),
                        'context': context,
                        'full_text': text[:100]
                    })
    
    # Очистка
    shutil.rmtree(TEMP_DIR)
    
    # Отчет
    print(f"{'='*60}")
    print(f"📊 РЕЗУЛЬТАТЫ ПОИСКА:")
    print(f"{'='*60}\n")
    
    if found_cases:
        print(f"⚠️  Найдено конструкций с 'до': {len(found_cases)}\n")
        
        # Показываем первые 20
        for i, case in enumerate(found_cases[:20], 1):
            print(f"{i}. Файл: {case['file']}")
            print(f"   Фрагмент: «{case['context']}»")
            print(f"   Контекст: {case['full_text'][:80]}...")
            print()
        
        if len(found_cases) > 20:
            print(f"   ... и еще {len(found_cases) - 20} вхождений")
    else:
        print("✅ Конструкций типа 'X до Y' не найдено!")
        print("   Все диапазоны уже в формате 'X-Y'")

if __name__ == "__main__":
    check_ranges()
