#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Автоматически добавляет уточнения к "масло" на основе английского оригинала
"""

import json
import re
from pathlib import Path

# Словарь замен для разных типов масла
REPLACEMENTS = {
    'butter': {
        'масло': 'сливочное масло',
        'масла': 'сливочного масла',
        'маслу': 'сливочному маслу',
        'маслом': 'сливочным маслом',
        'масле': 'сливочном масле',
        'Масло': 'Сливочное масло',
        'Масла': 'Сливочного масла',
        'Маслу': 'Сливочному маслу',
        'Маслом': 'Сливочным маслом',
        'Масле': 'Сливочном масле',
        'МАСЛО': 'СЛИВОЧНОЕ МАСЛО',
        'МАСЛА': 'СЛИВОЧНОГО МАСЛА',
        'МАСЛУ': 'СЛИВОЧНОМУ МАСЛУ',
        'МАСЛОМ': 'СЛИВОЧНЫМ МАСЛОМ',
        'МАСЛЕ': 'СЛИВОЧНОМ МАСЛЕ',
    },
    'olive_oil': {
        'масло': 'оливковое масло',
        'масла': 'оливкового масла',
        'маслу': 'оливковому маслу',
        'маслом': 'оливковым маслом',
        'масле': 'оливковом масле',
        'Масло': 'Оливковое масло',
        'Масла': 'Оливкового масла',
        'Маслу': 'Оливковому маслу',
        'Маслом': 'Оливковым маслом',
        'Масле': 'Оливковом масле',
        'МАСЛО': 'ОЛИВКОВОЕ МАСЛО',
        'МАСЛА': 'ОЛИВКОВОГО МАСЛА',
        'МАСЛУ': 'ОЛИВКОВОМУ МАСЛУ',
        'МАСЛОМ': 'ОЛИВКОВЫМ МАСЛОМ',
        'МАСЛЕ': 'ОЛИВКОВОМ МАСЛЕ',
    }
}

def fix_oil_mentions():
    """Исправляет упоминания масла"""
    
    # Загружаем анализ
    with open('oil_analysis.json', 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    # Фильтруем только те, что требуют уточнения
    to_fix = [r for r in results if not r['already_specified'] and r['oil_type'] in ['butter', 'olive_oil']]
    
    print(f"📝 Будет исправлено: {len(to_fix)} мест")
    print(f"   - butter → сливочное масло: {sum(1 for r in to_fix if r['oil_type'] == 'butter')}")
    print(f"   - olive_oil → оливковое масло: {sum(1 for r in to_fix if r['oil_type'] == 'olive_oil')}")
    
    # Группируем по файлам
    from collections import defaultdict
    by_file = defaultdict(list)
    for item in to_fix:
        by_file[item['file']].append(item)
    
    source_dir = Path("temp_ru_check/OEBPS")
    total_fixed = 0
    
    for filename, items in sorted(by_file.items()):
        filepath = source_dir / filename
        if not filepath.exists():
            print(f"⚠️  Файл не найден: {filename}")
            continue
        
        # Читаем файл
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        fixed_in_file = 0
        
        for item in items:
            element_id = item['element_id']
            word = item['word']
            oil_type = item['oil_type']
            
            # Получаем замену
            if oil_type not in REPLACEMENTS:
                continue
            
            replacement = REPLACEMENTS[oil_type].get(word)
            if not replacement:
                continue
            
            # Ищем элемент и заменяем слово
            pattern = rf'(<[^>]+id="{element_id}"[^>]*>.*?</[^>]+>)'
            
            def replace_in_match(match):
                element_html = match.group(1)
                # Заменяем только первое вхождение слова
                word_pattern = rf'\b{re.escape(word)}\b'
                new_html = re.sub(word_pattern, replacement, element_html, count=1)
                return new_html
            
            new_content = re.sub(pattern, replace_in_match, content, flags=re.DOTALL, count=1)
            
            if new_content != content:
                content = new_content
                fixed_in_file += 1
                total_fixed += 1
        
        if content != original_content:
            # Сохраняем файл
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            percentage = (fixed_in_file / len(items)) * 100
            print(f"✅ {filename}: исправлено {fixed_in_file} из {len(items)} мест ({percentage:.0f}%)")
    
    print(f"\n🎉 Всего исправлено: {total_fixed} мест")
    return total_fixed

if __name__ == "__main__":
    print("🔧 Автоматическое добавление уточнений к 'масло'\n")
    fixed = fix_oil_mentions()
    print(f"\n✅ Готово! Исправлено {fixed} мест")
