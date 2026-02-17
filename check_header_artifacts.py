#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка артефактов в заголовках (смешанный текст)
"""

import os
import zipfile
import shutil
from bs4 import BeautifulSoup

EPUB_FILE = "Hazan_RU_Final_0.3.epub"
TEMP_DIR = "temp_check_artifacts"

def check_header_artifacts():
    print("🔍 Распаковка EPUB...")
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    
    with zipfile.ZipFile(EPUB_FILE, 'r') as z:
        z.extractall(TEMP_DIR)
    
    artifacts = []
    
    for root, dirs, files in os.walk(TEMP_DIR):
        for f in files:
            if f.endswith(('.html', '.htm', '.xhtml')):
                filepath = os.path.join(root, f)
                with open(filepath, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file.read(), 'html.parser')
                
                # Проверяем все заголовки
                for tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    for tag in soup.find_all(tag_name):
                        text = tag.get_text(strip=True)
                        tag_id = tag.get('id', 'no-id')
                        
                        # Ищем смешанный регистр (КАПС + обычный)
                        # Например: "ПЕТРУШКАПетрушка"
                        has_upper = any(c.isupper() for c in text)
                        has_lower = any(c.islower() for c in text)
                        
                        if has_upper and has_lower:
                            # Проверяем: это не нормальный заголовок типа "Меню на 45 минут"
                            # Ищем паттерн: КАПС сразу переходит в строчные без пробела
                            import re
                            suspicious = re.search(r'[А-ЯA-Z]{3,}[а-яa-z]{3,}', text)
                            
                            if suspicious:
                                artifacts.append({
                                    'file': os.path.basename(filepath),
                                    'tag': tag_name,
                                    'id': tag_id,
                                    'text': text,
                                    'html': str(tag)[:200]
                                })
    
    shutil.rmtree(TEMP_DIR)
    
    print(f"{'='*70}")
    print(f"📊 НАЙДЕНО АРТЕФАКТОВ: {len(artifacts)}")
    print(f"{'='*70}\n")
    
    if artifacts:
        for i, art in enumerate(artifacts, 1):
            print(f"{i}. <{art['tag']} id='{art['id']}'>")
            print(f"   Файл: {art['file']}")
            print(f"   Текст: {art['text']}")
            print(f"   HTML: {art['html']}")
            print()
    else:
        print("✅ Артефактов не найдено!")

if __name__ == "__main__":
    check_header_artifacts()
