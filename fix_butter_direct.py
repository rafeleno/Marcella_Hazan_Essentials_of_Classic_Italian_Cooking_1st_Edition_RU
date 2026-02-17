#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Прямое исправление перевода butter без BeautifulSoup
Редактирует HTML напрямую, сохраняя оригинальное форматирование
"""

import json
import re
from pathlib import Path
from collections import defaultdict

# Словарь склонений
BUTTER_FORMS = {
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
}

def load_issues():
    """Загружает проблемные места из JSON"""
    with open('butter_translation_issues.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def fix_files():
    """Исправляет файлы напрямую"""
    
    issues = load_issues()
    print(f"📝 Загружено {len(issues)} проблемных мест")
    
    # Группируем по файлам
    by_file = defaultdict(list)
    for issue in issues:
        # Проверяем, что в английском тексте есть "butter"
        if 'butter' in issue['en_full_text'].lower():
            by_file[issue['file']].append(issue)
    
    print(f"📁 Файлов для исправления: {len(by_file)}")
    
    source_dir = Path("temp_butter_fix/OEBPS")
    total_fixed = 0
    total_attempted = 0
    
    for filename, file_issues in sorted(by_file.items()):
        filepath = source_dir / filename
        if not filepath.exists():
            print(f"⚠️  Файл не найден: {filename}")
            continue
        
        # Читаем весь файл как текст
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        fixed_in_file = 0
        
        for issue in file_issues:
            element_id = issue['element_id']
            ru_word = issue['ru_word']
            
            # Получаем замену
            replacement = BUTTER_FORMS.get(ru_word)
            if not replacement:
                continue
            
            # Ищем элемент с этим ID и заменяем в нем слово
            # Паттерн: находим элемент с id="element_id" и заменяем в нем слово
            pattern = rf'(<[^>]+id="{element_id}"[^>]*>.*?</[^>]+>)'
            
            def replace_in_match(match):
                element_html = match.group(1)
                # Заменяем слово внутри элемента
                word_pattern = rf'\b{re.escape(ru_word)}\b'
                new_html = re.sub(word_pattern, replacement, element_html)
                return new_html
            
            new_content = re.sub(pattern, replace_in_match, content, flags=re.DOTALL)
            
            if new_content != content:
                content = new_content
                fixed_in_file += 1
                total_fixed += 1
            
            total_attempted += 1
        
        if content != original_content:
            # Сохраняем файл
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            percentage = (fixed_in_file / len(file_issues)) * 100
            print(f"✅ {filename}: исправлено {fixed_in_file} из {len(file_issues)} мест ({percentage:.0f}%)")
    
    print(f"\n🎉 Всего исправлено: {total_fixed} из {total_attempted} проблемных мест ({(total_fixed/total_attempted*100):.1f}%)")
    return total_fixed, total_attempted

if __name__ == "__main__":
    print("🔧 Прямое исправление перевода butter\n")
    fixed, attempted = fix_files()
    print(f"\n📊 Итоговая статистика:")
    print(f"   - Исправлено: {fixed} мест")
    print(f"   - Не исправлено: {attempted - fixed} мест")
    print(f"   - Процент успеха: {(fixed/attempted*100):.1f}%")
