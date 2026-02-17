#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Финальная версия скрипта для исправления неправильного перевода "butter"
БЕЗ удаления временных файлов и результата
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

def replace_all_in_text_nodes(element, words_to_replace):
    """
    Рекурсивно заменяет все указанные слова в текстовых узлах элемента
    """
    replaced_count = 0
    
    def process_node(node):
        nonlocal replaced_count
        
        if isinstance(node, NavigableString):
            text = str(node)
            modified_text = text
            
            for word in words_to_replace:
                word_pattern = rf'(?<![а-яА-Я])({re.escape(word)})(?![а-яА-Я])'
                
                def check_and_replace(match):
                    nonlocal replaced_count
                    matched_word = match.group(1)
                    start_pos = match.start()
                    
                    context_start = max(0, start_pos - 50)
                    context_before = modified_text[context_start:start_pos]
                    
                    if re.search(r'(сливочн|оливков|растительн|овощн)[а-яА-Я]*\s*$', context_before):
                        return matched_word
                    
                    replaced_count += 1
                    return get_proper_butter_translation(matched_word)
                
                modified_text = re.sub(word_pattern, check_and_replace, modified_text)
            
            if modified_text != text:
                node.replace_with(NavigableString(modified_text))
        
        elif hasattr(node, 'contents'):
            for child in list(node.contents):
                process_node(child)
    
    process_node(element)
    return replaced_count

def fix_file_with_soup(filepath, file_issues):
    """Исправляет все проблемы в файле используя BeautifulSoup"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    fixed_count = 0
    
    issues_by_element = {}
    for issue in file_issues:
        elem_id = issue['element_id']
        if elem_id not in issues_by_element:
            issues_by_element[elem_id] = set()
        issues_by_element[elem_id].add(issue['ru_word'])
    
    for elem_id, words_to_replace in issues_by_element.items():
        element = soup.find(id=elem_id)
        
        if not element:
            continue
        
        count = replace_all_in_text_nodes(element, words_to_replace)
        fixed_count += count
    
    if fixed_count > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(str(soup))
    
    return fixed_count

def main():
    with open('butter_translation_issues.json', 'r', encoding='utf-8') as f:
        issues = json.load(f)
    
    print(f"📝 Загружено {len(issues)} проблемных мест")
    
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
        
        expected = len(file_issues)
        if fixed_count > 0:
            percentage = (fixed_count / expected) * 100
            print(f"✅ {filename}: исправлено {fixed_count} из {expected} мест ({percentage:.0f}%)")
    
    percentage_total = (total_fixed / len(issues)) * 100
    print(f"\n🎉 Всего исправлено: {total_fixed} из {len(issues)} проблемных мест ({percentage_total:.1f}%)")
    
    print("\n📦 Создание исправленного EPUB...")
    import subprocess
    
    output_epub = "Hazan_RU_Final_0.3.epub"
    if Path(output_epub).exists():
        Path(output_epub).unlink()
    
    result = subprocess.run([
        "python3", "pack_epub_ordered.py",
        "temp_translated",
        output_epub
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ Создан исправленный EPUB: {output_epub}")
        print("\n✨ Готово! Файл готов к использованию.")
        print(f"\n📊 Итоговая статистика:")
        print(f"   - Исправлено: {total_fixed} мест")
        print(f"   - Не исправлено: {len(issues) - total_fixed} мест")
        print(f"   - Процент успеха: {percentage_total:.1f}%")
    else:
        print(f"❌ Ошибка при создании EPUB:")
        print(result.stderr)

if __name__ == "__main__":
    main()
