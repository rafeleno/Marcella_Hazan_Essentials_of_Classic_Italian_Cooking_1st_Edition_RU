#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Анализирует все упоминания "масло" и определяет тип на основе английского оригинала
"""

import re
import json
from pathlib import Path
from bs4 import BeautifulSoup
from collections import defaultdict

def analyze_oil_mentions():
    """Анализирует все упоминания масла"""
    
    ru_dir = Path("Hazan_RU_Final_0.4.epub")
    en_dir = Path("temp_original_en/OEBPS")
    
    # Распаковываем русский EPUB
    import subprocess
    subprocess.run(["unzip", "-q", "-o", str(ru_dir), "-d", "temp_ru_check"], check=True)
    
    ru_dir = Path("temp_ru_check/OEBPS")
    
    results = []
    
    # Паттерн для поиска "масло" в разных формах
    oil_pattern = re.compile(r'\b(масл[оа-я]*)\b', re.IGNORECASE)
    
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
            
            # Ищем "масло" в русском тексте
            matches = list(oil_pattern.finditer(ru_text))
            if not matches:
                continue
            
            # Находим соответствующий английский элемент
            en_element = en_soup.find(id=element_id)
            if not en_element:
                continue
            
            en_text = en_element.get_text()
            
            # Для каждого вхождения "масло" определяем тип
            for match in matches:
                word = match.group(0)
                start = max(0, match.start() - 50)
                end = min(len(ru_text), match.end() + 50)
                ru_context = ru_text[start:end].strip()
                
                # Определяем тип масла по английскому тексту
                oil_type = None
                if 'butter' in en_text.lower():
                    oil_type = 'butter'
                elif 'olive oil' in en_text.lower():
                    oil_type = 'olive_oil'
                elif 'oil' in en_text.lower():
                    oil_type = 'oil'
                
                # Проверяем, не указано ли уже уточнение
                already_specified = False
                if 'оливков' in ru_context.lower():
                    already_specified = True
                    oil_type = 'olive_oil_already'
                elif 'сливочн' in ru_context.lower():
                    already_specified = True
                    oil_type = 'butter_already'
                elif 'растительн' in ru_context.lower():
                    already_specified = True
                    oil_type = 'vegetable_oil_already'
                
                results.append({
                    'file': ru_file.name,
                    'element_id': element_id,
                    'word': word,
                    'ru_context': ru_context,
                    'en_text': en_text[:200],
                    'oil_type': oil_type,
                    'already_specified': already_specified
                })
    
    return results

if __name__ == "__main__":
    print("🔍 Анализирую все упоминания 'масло'...")
    results = analyze_oil_mentions()
    
    # Сохраняем результаты
    with open('oil_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Найдено {len(results)} упоминаний")
    
    # Статистика
    by_type = defaultdict(int)
    for r in results:
        by_type[r['oil_type']] += 1
    
    print("\n📊 Статистика:")
    for oil_type, count in sorted(by_type.items(), key=lambda x: (x[0] is None, x[0])):
        print(f"   {oil_type}: {count}")
    
    # Показываем примеры неуточненных
    unspecified = [r for r in results if not r['already_specified'] and r['oil_type'] in ['butter', 'oil', 'olive_oil']]
    print(f"\n⚠️  Требуют уточнения: {len(unspecified)}")
    
    print("\n📋 Первые 10 примеров требующих уточнения:\n")
    for i, r in enumerate(unspecified[:10], 1):
        print(f"{i}. [{r['file']}] {r['word']} ({r['oil_type']})")
        print(f"   RU: ...{r['ru_context']}...")
        print(f"   EN: {r['en_text'][:100]}...")
        print()
