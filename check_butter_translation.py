#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для проверки правильности перевода слова "butter" как "сливочное масло"
"""

import re
import os
from pathlib import Path
from bs4 import BeautifulSoup
import json

def extract_text_with_ids(soup):
    """Извлекает текст с сохранением ID элементов для сопоставления"""
    text_map = {}
    for elem in soup.find_all(id=True):
        elem_id = elem.get('id')
        text = elem.get_text(strip=True)
        if text:
            text_map[elem_id] = text
    return text_map

def find_maslo_contexts(translated_dir):
    """Находит все упоминания 'масло' в переведенных файлах"""
    maslo_pattern = re.compile(r'\bмасл[а-яА-Я]*\b', re.IGNORECASE)
    contexts = []
    
    oebps_dir = Path(translated_dir) / "OEBPS"
    for html_file in sorted(oebps_dir.glob("*.htm")):
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Ищем все элементы с текстом
            for elem in soup.find_all(id=True):
                elem_id = elem.get('id')
                text = elem.get_text()
                
                # Проверяем наличие слова "масл"
                matches = maslo_pattern.finditer(text)
                for match in matches:
                    # Извлекаем контекст (50 символов до и после)
                    start = max(0, match.start() - 50)
                    end = min(len(text), match.end() + 50)
                    context = text[start:end]
                    
                    contexts.append({
                        'file': html_file.name,
                        'element_id': elem_id,
                        'word': match.group(),
                        'context': context,
                        'full_text': text
                    })
    
    return contexts

def check_original_word(original_dir, filename, element_id, context):
    """Проверяет, какое слово использовано в оригинале (butter или oil)"""
    original_file = Path(original_dir) / "OEBPS" / filename
    
    if not original_file.exists():
        return None, None
    
    with open(original_file, 'r', encoding='utf-8') as f:
        content = f.read()
        soup = BeautifulSoup(content, 'html.parser')
        
        # Ищем элемент с таким же ID
        elem = soup.find(id=element_id)
        if elem:
            original_text = elem.get_text()
            
            # Проверяем наличие butter или oil
            has_butter = bool(re.search(r'\bbutter\b', original_text, re.IGNORECASE))
            has_oil = bool(re.search(r'\boil\b', original_text, re.IGNORECASE))
            
            return original_text, {'butter': has_butter, 'oil': has_oil}
    
    return None, None

def is_explicitly_butter(ru_text):
    """Проверяет, явно ли указано 'сливочное масло' в русском тексте"""
    return bool(re.search(r'\bсливочн[а-яА-Я]*\s+масл[а-яА-Я]*\b', ru_text, re.IGNORECASE))

def is_explicitly_oil(ru_text):
    """Проверяет, явно ли указано растительное/оливковое масло в русском тексте"""
    oil_patterns = [
        r'\bоливков[а-яА-Я]*\s+масл[а-яА-Я]*\b',
        r'\bрастительн[а-яА-Я]*\s+масл[а-яА-Я]*\b',
        r'\bовощн[а-яА-Я]*\s+масл[а-яА-Я]*\b',
    ]
    return any(re.search(pattern, ru_text, re.IGNORECASE) for pattern in oil_patterns)

def main():
    translated_dir = "temp_translated"
    original_dir = "temp_original"
    
    print("🔍 Поиск всех упоминаний 'масло' в переводе...")
    contexts = find_maslo_contexts(translated_dir)
    print(f"Найдено {len(contexts)} упоминаний")
    
    print("\n🔎 Проверка соответствия с оригиналом...")
    
    issues = []
    
    for i, ctx in enumerate(contexts):
        if (i + 1) % 100 == 0:
            print(f"Обработано {i + 1}/{len(contexts)}...")
        
        # Проверяем, явно ли указан тип масла в переводе
        is_butter_explicit = is_explicitly_butter(ctx['full_text'])
        is_oil_explicit = is_explicitly_oil(ctx['full_text'])
        
        # Если тип масла уже явно указан, пропускаем
        if is_butter_explicit or is_oil_explicit:
            continue
        
        # Проверяем оригинал
        original_text, word_types = check_original_word(
            original_dir, 
            ctx['file'], 
            ctx['element_id'],
            ctx['context']
        )
        
        if word_types and word_types['butter'] and not word_types['oil']:
            # В оригинале только butter, но в переводе просто "масло"
            issues.append({
                'file': ctx['file'],
                'element_id': ctx['element_id'],
                'ru_word': ctx['word'],
                'ru_context': ctx['context'],
                'ru_full_text': ctx['full_text'],
                'en_full_text': original_text,
                'issue': 'butter_not_specified'
            })
    
    print(f"\n✅ Проверка завершена!")
    print(f"📊 Найдено проблемных мест: {len(issues)}")
    
    # Сохраняем результаты
    with open('butter_translation_issues.json', 'w', encoding='utf-8') as f:
        json.dump(issues, f, ensure_ascii=False, indent=2)
    
    # Выводим первые 10 примеров
    print("\n📝 Примеры найденных проблем:")
    for i, issue in enumerate(issues[:10], 1):
        print(f"\n{i}. Файл: {issue['file']}, ID: {issue['element_id']}")
        print(f"   RU: ...{issue['ru_context']}...")
        print(f"   EN: {issue['en_full_text'][:100]}...")
    
    if len(issues) > 10:
        print(f"\n... и еще {len(issues) - 10} проблем")
    
    return issues

if __name__ == "__main__":
    main()
