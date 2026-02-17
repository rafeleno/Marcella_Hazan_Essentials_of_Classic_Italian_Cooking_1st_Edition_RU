#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Финальное исправление всех масел на основе точного анализа английского текста
"""

import re
from pathlib import Path
from bs4 import BeautifulSoup
from collections import defaultdict

# Словари замен
BUTTER_FORMS = {
    'масло': 'сливочное масло', 'масла': 'сливочного масла', 'маслу': 'сливочному маслу',
    'маслом': 'сливочным маслом', 'масле': 'сливочном масле',
    'Масло': 'Сливочное масло', 'Масла': 'Сливочного масла', 'Маслу': 'Сливочному маслу',
    'Маслом': 'Сливочным маслом', 'Масле': 'Сливочном масле',
    'МАСЛО': 'СЛИВОЧНОЕ МАСЛО', 'МАСЛА': 'СЛИВОЧНОГО МАСЛА', 'МАСЛУ': 'СЛИВОЧНОМУ МАСЛУ',
    'МАСЛОМ': 'СЛИВОЧНЫМ МАСЛОМ', 'МАСЛЕ': 'СЛИВОЧНОМ МАСЛЕ',
}

OLIVE_FORMS = {
    'масло': 'оливковое масло', 'масла': 'оливкового масла', 'маслу': 'оливковому маслу',
    'маслом': 'оливковым маслом', 'масле': 'оливковом масле',
    'Масло': 'Оливковое масло', 'Масла': 'Оливкового масла', 'Маслу': 'Оливковому маслу',
    'Маслом': 'Оливковым маслом', 'Масле': 'Оливковом масле',
    'МАСЛО': 'ОЛИВКОВОЕ МАСЛО', 'МАСЛА': 'ОЛИВКОВОГО МАСЛА', 'МАСЛУ': 'ОЛИВКОВОМУ МАСЛУ',
    'МАСЛОМ': 'ОЛИВКОВЫМ МАСЛОМ', 'МАСЛЕ': 'ОЛИВКОВОМ МАСЛЕ',
}

def fix_all_oils():
    """Исправляет все масла"""
    
    ru_dir = Path("temp_work/OEBPS")
    en_dir = Path("temp_en/OEBPS")
    
    stats = {'butter': 0, 'olive': 0, 'skipped': 0}
    
    for ru_file in sorted(ru_dir.glob("*.htm")):
        en_file = en_dir / ru_file.name
        if not en_file.exists():
            continue
        
        # Читаем файлы
        with open(ru_file, 'r', encoding='utf-8') as f:
            ru_content = f.read()
        
        with open(en_file, 'r', encoding='utf-8') as f:
            en_soup = BeautifulSoup(f.read(), 'html.parser')
        
        ru_soup = BeautifulSoup(ru_content, 'html.parser')
        
        # Для каждого элемента с ID
        for element in ru_soup.find_all(id=True):
            element_id = element.get('id')
            ru_text = element.get_text()
            
            # Находим английский элемент
            en_element = en_soup.find(id=element_id)
            if not en_element:
                continue
            
            en_text = en_element.get_text().lower()
            
            # Определяем, что нужно заменить
            replacements = None
            if 'butter' in en_text and 'olive' not in ru_text.lower() and 'сливочн' not in ru_text.lower():
                replacements = BUTTER_FORMS
                oil_type = 'butter'
            elif 'olive oil' in en_text and 'оливков' not in ru_text.lower():
                replacements = OLIVE_FORMS
                oil_type = 'olive'
            else:
                continue
            
            # Заменяем в HTML элемента
            element_html = str(element)
            modified = False
            
            for word, replacement in replacements.items():
                pattern = rf'\b{re.escape(word)}\b'
                new_html = re.sub(pattern, replacement, element_html)
                if new_html != element_html:
                    element_html = new_html
                    modified = True
            
            if modified:
                # Заменяем элемент в контенте
                old_element_str = str(element)
                ru_content = ru_content.replace(old_element_str, element_html, 1)
                stats[oil_type] += 1
        
        # Сохраняем файл
        with open(ru_file, 'w', encoding='utf-8') as f:
            f.write(ru_content)
    
    return stats

if __name__ == "__main__":
    print("🔧 Исправляю все масла...\n")
    stats = fix_all_oils()
    print(f"✅ Готово!")
    print(f"   Butter → сливочное: {stats['butter']}")
    print(f"   Olive oil → оливковое: {stats['olive']}")
