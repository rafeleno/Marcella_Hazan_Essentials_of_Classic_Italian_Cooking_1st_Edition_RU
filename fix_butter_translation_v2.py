#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Улучшенный скрипт для исправления неправильного перевода "butter"
Использует BeautifulSoup для точного поиска элементов
"""

import json
import re
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString

def get_proper_butter_translation(word):
    """Возвращает правильный перевод 'butter' в нужном падеже"""
    word_lower = word.lower()
    
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

def replace_in_text_nodes(element, word, replacement):
    """Рекурсивно заменяет слово в текстовых узлах элемента"""
    replaced = False
    
    for content in element.contents:
        if isinstance(content, NavigableString):
            # Это текстовый узел
            text = str(content)
            
            # Проверяем контекст перед словом
            word_pattern = rf'(?<![а-яА-Я])({re.escape(word)})(?![а-яА-Я])'
            match = re.search(word_pattern, text)
            
            if match:
                # Проверяем, нет ли перед словом "сливочн", "оливков", "растительн"
                start_pos = match.start()
                context_start = max(0, start_pos - 50)
                context_before = text[context_start:start_pos]
                
                if not re.search(r'(сливочн|оливков|растительн|овощн)[а-яА-Я]*\s*$', context_before):
                    # Заменяем только первое вхождение
                    new_text = re.sub(word_pattern, replacement, text, count=1)
                    content.replace_with(NavigableString(new_text))
                    replaced = True
                    break
        elif hasattr(content, 'contents'):
            # Это элемент, рекурсивно обрабатываем
            if replace_in_text_nodes(content, word, replacement):
                replaced = True
                break
    
    return replaced

def fix_file_with_soup(filepath, file_issues):
    """Исправляет все проблемы в файле используя BeautifulSoup"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    fixed_count = 0
    
    # Группируем по element_id
    issues_by_element = {}
    for issue in file_issues:
        elem_id = issue['element_id']
        if elem_id not in issues_by_element:
            issues_by_element[elem_id] = []
        issues_by_element[elem_id].append(issue)
    
    # Обрабатываем каждый элемент
    for elem_id, elem_issues in issues_by_element.items():
        element = soup.find(id=elem_id)
        
        if not element:
            continue
        
        # Для каждой проблемы в этом элементе
        for issue in elem_issues:
            ru_word = issue['ru_word']
            proper_translation = get_proper_butter_translation(ru_word)
            
            if replace_in_text_nodes(element, ru_word, proper_translation):
                fixed_count += 1
    
    # Сохраняем файл
    if fixed_count > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(str(soup))
    
    return fixed_count

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
    
    for filename, file_issues in sorted(files_to_fix.items()):
        filepath = translated_dir / filename
        
        if not filepath.exists():
            print(f"⚠️  Файл не найден: {filename}")
            continue
        
        fixed_count = fix_file_with_soup(filepath, file_issues)
        total_fixed += fixed_count
        
        if fixed_count > 0:
            print(f"✅ {filename}: исправлено {fixed_count} из {len(file_issues)} мест")
        else:
            print(f"⚠️  {filename}: 0 из {len(file_issues)} мест (возможно, уже исправлено)")
    
    print(f"\n🎉 Всего исправлено: {total_fixed} из {len(issues)} проблемных мест")
    
    # Создаем новый EPUB
    print("\n📦 Создание исправленного EPUB...")
    import subprocess
    
    output_epub = "Hazan_RU_Final_0.3_butter_fixed.epub"
    if Path(output_epub).exists():
        Path(output_epub).unlink()
    
    result = subprocess.run([
        "python3", "pack_epub_ordered.py",
        "temp_translated",
        output_epub
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ Создан исправленный EPUB: {output_epub}")
        
        # Очищаем временные директории
        print("\n🧹 Очистка временных файлов...")
        import shutil
        for temp_dir in ["temp_translated", "temp_original"]:
            if Path(temp_dir).exists():
                shutil.rmtree(temp_dir)
                print(f"   Удалено: {temp_dir}")
    else:
        print(f"❌ Ошибка при создании EPUB:")
        print(result.stderr)

if __name__ == "__main__":
    main()
