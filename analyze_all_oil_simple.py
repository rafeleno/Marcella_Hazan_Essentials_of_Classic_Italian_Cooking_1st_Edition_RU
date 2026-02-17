#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Выводит ВСЕ вхождения "масл" для ручного анализа
"""

import re
from pathlib import Path
from bs4 import BeautifulSoup

def analyze_all_oil():
    """Анализирует все упоминания масла"""
    
    ru_dir = Path("temp_work/OEBPS")
    en_dir = Path("temp_en/OEBPS")
    
    all_cases = []
    
    # Паттерн для поиска "масл" в разных формах
    oil_pattern = re.compile(r'\b(масл[а-яА-ЯёЁ]*)\b')
    
    for ru_file in sorted(ru_dir.glob("*.htm")):
        en_file = en_dir / ru_file.name
        if not en_file.exists():
            continue
        
        # Читаем файлы
        with open(ru_file, 'r', encoding='utf-8') as f:
            ru_soup = BeautifulSoup(f.read(), 'html.parser')
        
        with open(en_file, 'r', encoding='utf-8') as f:
            en_soup = BeautifulSoup(f.read(), 'html.parser')
        
        # Ищем все элементы с ID
        for element in ru_soup.find_all(id=True):
            element_id = element.get('id')
            ru_text = element.get_text()
            
            # Ищем "масл" в русском тексте
            matches = list(oil_pattern.finditer(ru_text))
            if not matches:
                continue
            
            # Находим соответствующий английский элемент
            en_element = en_soup.find(id=element_id)
            if not en_element:
                continue
            
            en_text = en_element.get_text()
            
            # Для каждого вхождения
            for match in matches:
                word = match.group(0)
                start = max(0, match.start() - 60)
                end = min(len(ru_text), match.end() + 60)
                ru_context = ru_text[start:end].strip()
                
                # Определяем тип по английскому
                en_lower = en_text.lower()
                oil_type = 'unknown'
                if 'butter' in en_lower:
                    oil_type = 'BUTTER'
                if 'olive oil' in en_lower:
                    oil_type = 'OLIVE_OIL'
                elif 'oil' in en_lower and 'butter' not in en_lower:
                    oil_type = 'OIL'
                
                # Проверяем, не указано ли уже
                ru_lower = ru_context.lower()
                already = 'NO'
                if 'оливков' in ru_lower:
                    already = 'YES_OLIVE'
                elif 'сливочн' in ru_lower:
                    already = 'YES_BUTTER'
                elif 'растительн' in ru_lower:
                    already = 'YES_VEG'
                
                all_cases.append({
                    'file': ru_file.name,
                    'id': element_id,
                    'word': word,
                    'ru_context': ru_context,
                    'en_snippet': en_text[:100],
                    'type': oil_type,
                    'already': already
                })
    
    return all_cases

if __name__ == "__main__":
    print("🔍 Анализирую все вхождения 'масл'...\n")
    cases = analyze_all_oil()
    
    print(f"Всего найдено: {len(cases)}\n")
    print("="*120)
    
    # Выводим только те, что требуют внимания
    need_fix = [c for c in cases if c['already'] == 'NO' and c['type'] in ['BUTTER', 'OLIVE_OIL']]
    
    print(f"\n⚠️  ТРЕБУЮТ ИСПРАВЛЕНИЯ: {len(need_fix)}\n")
    print("="*120)
    
    for i, c in enumerate(need_fix, 1):
        print(f"\n{i}. [{c['file']}#{c['id']}] {c['word']} → {c['type']}")
        print(f"   RU: ...{c['ru_context']}...")
        print(f"   EN: {c['en_snippet']}...")
        print("-"*120)
        
        if i >= 50:  # Первые 50 для начала
            print(f"\n... и еще {len(need_fix) - 50} случаев")
            break
