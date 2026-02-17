#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Поиск непереведённых английских фрагментов в EPUB
"""

import os
import re
import zipfile
import shutil
from bs4 import BeautifulSoup

EPUB_FILE = "Hazan_RU_Final_0.3.epub"
TEMP_DIR = "temp_find_english"

def find_english_fragments():
    print("🔍 Распаковка EPUB...")
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    
    with zipfile.ZipFile(EPUB_FILE, 'r') as z:
        z.extractall(TEMP_DIR)
    
    # Паттерн для поиска английских слов (минимум 3 слова подряд)
    # Ищем последовательности: слово слово слово
    english_pattern = re.compile(
        r'\b[a-z]+\s+(?:to|and|or|of|the|a|an|in|with|for)\s+[a-z]+(?:\s+[a-z]+)*',
        re.IGNORECASE
    )
    
    # Более простой паттерн: 4+ английских слова подряд
    simple_pattern = re.compile(r'\b[a-zA-Z]+\s+[a-zA-Z]+\s+[a-zA-Z]+\s+[a-zA-Z]+')
    
    found_fragments = []
    
    for root, dirs, files in os.walk(TEMP_DIR):
        for f in files:
            if f.endswith(('.html', '.htm', '.xhtml')):
                filepath = os.path.join(root, f)
                with open(filepath, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file.read(), 'html.parser')
                
                # Проверяем все текстовые элементы
                for tag in soup.find_all(['p', 'li', 'td', 'div', 'span']):
                    text = tag.get_text()
                    
                    # Ищем английские фрагменты
                    matches = simple_pattern.findall(text)
                    
                    for match in matches:
                        # Фильтруем ложные срабатывания (итальянские названия)
                        # Пропускаем если это часть итальянского названия блюда
                        if any(word in match.lower() for word in ['alla', 'di', 'con', 'del', 'della']):
                            continue
                        
                        # Получаем контекст (50 символов до и после)
                        start = max(0, text.find(match) - 50)
                        end = min(len(text), text.find(match) + len(match) + 50)
                        context = text[start:end].strip()
                        
                        found_fragments.append({
                            'file': os.path.basename(filepath),
                            'fragment': match,
                            'context': context,
                            'tag_id': tag.get('id', 'no-id')
                        })
    
    shutil.rmtree(TEMP_DIR)
    
    print(f"{'='*70}")
    print(f"📊 НАЙДЕНО АНГЛИЙСКИХ ФРАГМЕНТОВ: {len(found_fragments)}")
    print(f"{'='*70}\n")
    
    if found_fragments:
        # Убираем дубликаты
        unique_fragments = {}
        for frag in found_fragments:
            key = frag['fragment']
            if key not in unique_fragments:
                unique_fragments[key] = frag
        
        print(f"Уникальных фрагментов: {len(unique_fragments)}\n")
        
        for i, (key, frag) in enumerate(list(unique_fragments.items())[:30], 1):
            print(f"{i:2d}. Файл: {frag['file']}")
            print(f"    Фрагмент: «{frag['fragment']}»")
            print(f"    Контекст: ...{frag['context']}...")
            print()
        
        if len(unique_fragments) > 30:
            print(f"   ... и еще {len(unique_fragments) - 30} фрагментов")
    else:
        print("✅ Английских фрагментов не найдено!")

if __name__ == "__main__":
    find_english_fragments()
