#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Извлекает все контексты с упоминанием "масло" для ручного анализа
"""

import re
import json
from pathlib import Path
from bs4 import BeautifulSoup

def extract_contexts():
    """Извлекает все контексты с 'масло'"""
    
    source_dir = Path("temp_butter_fix/OEBPS")
    contexts = []
    
    # Паттерн для поиска слова "масло" в разных формах
    pattern = re.compile(r'\b(масл[оа-я]*)\b', re.IGNORECASE)
    
    for html_file in sorted(source_dir.glob("*.htm")):
        with open(html_file, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        
        # Ищем все текстовые узлы
        for element in soup.find_all(text=True):
            text = element.string
            if not text or not text.strip():
                continue
            
            # Ищем все вхождения "масло"
            for match in pattern.finditer(text):
                word = match.group(0)
                start = max(0, match.start() - 100)
                end = min(len(text), match.end() + 100)
                context = text[start:end].strip()
                
                contexts.append({
                    'file': html_file.name,
                    'word': word,
                    'context': context,
                    'full_text': text.strip()[:500]  # Первые 500 символов
                })
    
    return contexts

if __name__ == "__main__":
    print("🔍 Извлекаю контексты с 'масло'...")
    contexts = extract_contexts()
    
    # Сохраняем в JSON
    with open('butter_contexts.json', 'w', encoding='utf-8') as f:
        json.dump(contexts, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Найдено {len(contexts)} упоминаний")
    print(f"📄 Сохранено в butter_contexts.json")
    
    # Показываем первые 10 примеров
    print("\n📋 Первые 10 примеров:\n")
    for i, ctx in enumerate(contexts[:10], 1):
        print(f"{i}. [{ctx['file']}] {ctx['word']}")
        print(f"   Контекст: ...{ctx['context']}...")
        print()
