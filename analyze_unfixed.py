#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для анализа неисправленных случаев
"""

import json
from pathlib import Path
from bs4 import BeautifulSoup

def main():
    # Загружаем список проблем
    with open('butter_translation_issues.json', 'r', encoding='utf-8') as f:
        issues = json.load(f)
    
    print("🔍 Анализ неисправленных случаев...")
    print("=" * 80)
    
    # Распаковываем EPUB для проверки
    import subprocess
    subprocess.run(["unzip", "-q", "Hazan_RU_Final_0.3_butter_fixed.epub", "-d", "temp_check"], check=True)
    
    check_dir = Path("temp_check/OEBPS")
    unfixed_examples = []
    
    for issue in issues[:100]:  # Проверяем первые 100
        filepath = check_dir / issue['file']
        
        if not filepath.exists():
            continue
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        element = soup.find(id=issue['element_id'])
        
        if element:
            text = element.get_text()
            
            # Проверяем, было ли исправлено
            if 'сливочн' not in text and issue['ru_word'].lower() in text.lower():
                unfixed_examples.append({
                    'file': issue['file'],
                    'element_id': issue['element_id'],
                    'word': issue['ru_word'],
                    'context': text[:200]
                })
    
    print(f"\nНайдено {len(unfixed_examples)} неисправленных примеров из первых 100:")
    print()
    
    for i, example in enumerate(unfixed_examples[:10], 1):
        print(f"{i}. Файл: {example['file']}, ID: {example['element_id']}")
        print(f"   Слово: {example['word']}")
        print(f"   Контекст: {example['context'][:150]}...")
        print()
    
    # Очистка
    import shutil
    shutil.rmtree("temp_check")

if __name__ == "__main__":
    main()
