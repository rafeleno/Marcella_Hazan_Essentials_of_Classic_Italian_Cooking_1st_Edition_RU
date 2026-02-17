#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для исправления неправильного перевода "butter" как "масло" вместо "сливочное масло"
"""

import json
import re
from pathlib import Path
import shutil

def get_proper_butter_translation(word):
    """
    Возвращает правильный перевод 'butter' в нужном падеже
    """
    word_lower = word.lower()
    
    # Словарь склонений "сливочное масло"
    declensions = {
        'масло': 'сливочное масло',
        'масла': 'сливочного масла',
        'маслу': 'сливочному маслу',
        'маслом': 'сливочным маслом',
        'масле': 'сливочном масле',
        'масел': 'сливочных масел',
        'маслам': 'сливочным маслам',
        'маслами': 'сливочными маслами',
        'маслах': 'сливочных маслах',
    }
    
    proper_form = declensions.get(word_lower, 'сливочное масло')
    
    # Сохраняем регистр
    if word.isupper():
        return proper_form.upper()
    elif word[0].isupper():
        return proper_form[0].upper() + proper_form[1:]
    else:
        return proper_form

def fix_file(filepath, file_issues):
    """Исправляет все проблемы в одном файле"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    fixed_count = 0
    
    # Сортируем проблемы по позиции в тексте (от конца к началу, чтобы не сбивать индексы)
    # Группируем по element_id для точности
    issues_by_element = {}
    for issue in file_issues:
        elem_id = issue['element_id']
        if elem_id not in issues_by_element:
            issues_by_element[elem_id] = []
        issues_by_element[elem_id].append(issue)
    
    # Обрабатываем каждый элемент
    for elem_id, elem_issues in issues_by_element.items():
        # Находим элемент по ID
        pattern = rf'(<[^>]+id="{re.escape(elem_id)}"[^>]*>)(.*?)(</[^>]+>)'
        
        def replace_in_element(match):
            opening_tag = match.group(1)
            element_content = match.group(2)
            closing_tag = match.group(3)
            
            modified_content = element_content
            local_fixed = 0
            
            # Для каждой проблемы в этом элементе
            for issue in elem_issues:
                ru_word = issue['ru_word']
                
                # Проверяем, не является ли это уже сливочным/оливковым/растительным маслом
                # Ищем слово с контекстом
                word_pattern = rf'(?<![а-яА-Я])({re.escape(ru_word)})(?![а-яА-Я])'
                
                # Функция для проверки контекста перед заменой
                def check_and_replace(m):
                    nonlocal local_fixed
                    word = m.group(1)
                    start_pos = m.start()
                    
                    # Проверяем контекст перед словом (50 символов)
                    context_start = max(0, start_pos - 50)
                    context_before = modified_content[context_start:start_pos]
                    
                    # Если перед словом уже есть "сливочн", "оливков", "растительн" - не заменяем
                    if re.search(r'(сливочн|оливков|растительн|овощн)[а-яА-Я]*\s*$', context_before):
                        return word
                    
                    # Заменяем
                    local_fixed += 1
                    return get_proper_butter_translation(word)
                
                # Заменяем только первое вхождение (так как каждая проблема - это одно вхождение)
                modified_content = re.sub(word_pattern, check_and_replace, modified_content, count=1)
            
            nonlocal fixed_count
            fixed_count += local_fixed
            
            return opening_tag + modified_content + closing_tag
        
        # Заменяем содержимое элемента
        content = re.sub(pattern, replace_in_element, content, flags=re.DOTALL)
    
    # Сохраняем только если были изменения
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return fixed_count
    
    return 0

def main():
    # Загружаем список проблем
    with open('butter_translation_issues.json', 'r', encoding='utf-8') as f:
        issues = json.load(f)
    
    print(f"📝 Загружено {len(issues)} проблемных мест")
    
    # Группируем по файлам
    files_to_fix = {}
    for issue in issues:
        filename = issue['file']
        if filename not in files_to_fix:
            files_to_fix[filename] = []
        files_to_fix[filename].append(issue)
    
    print(f"📁 Файлов для исправления: {len(files_to_fix)}")
    
    translated_dir = Path("temp_translated/OEBPS")
    total_fixed = 0
    
    for filename, file_issues in files_to_fix.items():
        filepath = translated_dir / filename
        
        if not filepath.exists():
            print(f"⚠️  Файл не найден: {filename}")
            continue
        
        fixed_count = fix_file(filepath, file_issues)
        if fixed_count > 0:
            total_fixed += fixed_count
            print(f"✅ {filename}: исправлено {fixed_count} мест")
    
    print(f"\n🎉 Всего исправлено: {total_fixed} из {len(issues)} проблемных мест")
    
    # Создаем новый EPUB
    print("\n📦 Создание исправленного EPUB...")
    import subprocess
    
    # Удаляем старый файл, если существует
    output_epub = "Hazan_RU_Final_0.3_butter_fixed.epub"
    if Path(output_epub).exists():
        Path(output_epub).unlink()
    
    # Упаковываем EPUB
    result = subprocess.run([
        "python3", "pack_epub_ordered.py",
        "temp_translated",
        output_epub
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ Создан исправленный EPUB: {output_epub}")
    else:
        print(f"❌ Ошибка при создании EPUB:")
        print(result.stderr)

if __name__ == "__main__":
    main()
