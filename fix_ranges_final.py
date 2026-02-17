#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Замена конструкций "от X до Y" и "X до Y" на "X-Y"
Поддержка целых чисел, дробей и смешанных чисел
"""

import os
import re
import zipfile
import shutil
from bs4 import BeautifulSoup

EPUB_FILE = "Hazan_RU_Final_0.3.epub"
TEMP_DIR = "temp_fix_ranges"
OUTPUT_FILE = "Hazan_RU_Final_0.3.epub"

def fix_ranges():
    print("🔍 Распаковка EPUB...")
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    
    with zipfile.ZipFile(EPUB_FILE, 'r') as z:
        z.extractall(TEMP_DIR)
    
    total_replaced = 0
    
    # Находим HTML файлы
    html_files = []
    for root, dirs, files in os.walk(TEMP_DIR):
        for f in files:
            if f.endswith(('.html', '.htm', '.xhtml')):
                html_files.append(os.path.join(root, f))
    
    print(f"📂 Обработка {len(html_files)} файлов...\n")
    
    # Паттерн для чисел (целые, дроби, смешанные)
    # Примеры: 2, ¾, 2¾, 1½, ⅓, 2.5
    number_pattern = r'(?:\d+(?:[.,]\d+)?)?[¼½¾⅓⅔⅛⅜⅝⅞]|\d+(?:[.,]\d+)?'
    
    # Регулярные выражения для замены
    patterns = [
        # "от X до Y" -> "X-Y"
        (re.compile(rf'\bот\s+({number_pattern})\s+до\s+({number_pattern})\b', re.IGNORECASE), r'\1-\2'),
        # "X до Y" -> "X-Y" (без "от")
        (re.compile(rf'\b({number_pattern})\s+до\s+({number_pattern})\b', re.IGNORECASE), r'\1-\2'),
    ]
    
    for filepath in html_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        file_changed = False
        
        # Обрабатываем текстовые узлы
        for text_node in soup.find_all(string=True):
            if text_node.parent.name in ['script', 'style']:
                continue
            
            text = str(text_node)
            original = text
            
            # Применяем все паттерны
            for pattern, replacement in patterns:
                text = pattern.sub(replacement, text)
            
            # Если текст изменился
            if text != original:
                changes = len(pattern.findall(original))
                total_replaced += changes
                text_node.replace_with(text)
                file_changed = True
        
        # Сохраняем файл если были изменения
        if file_changed:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(str(soup))
    
    print(f"{'='*60}")
    print(f"✅ Заменено конструкций 'до': {total_replaced}")
    print(f"{'='*60}\n")
    
    # Пересборка EPUB
    print(f"📦 Сборка {OUTPUT_FILE}...")
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
    
    cwd = os.getcwd()
    os.chdir(TEMP_DIR)
    os.system(f"zip -0 -X ../{OUTPUT_FILE} mimetype >/dev/null 2>&1")
    os.system(f"zip -r -q ../{OUTPUT_FILE} META-INF OEBPS -x '*.DS_Store'")
    
    if os.path.exists("Haza_9780307958303_epub_opf_r1.opf"):
        os.system(f"zip -r -q ../{OUTPUT_FILE} *.opf *.ncx")
    
    os.chdir(cwd)
    
    # Очистка
    shutil.rmtree(TEMP_DIR)
    
    print(f"🎉 Готово! Файл: {OUTPUT_FILE}")
    print(f"📏 Размер: {os.path.getsize(OUTPUT_FILE) / 1024 / 1024:.1f} MB")
    
    # Примеры замен для проверки
    print(f"\n📋 Примеры замен:")
    print(f"  'от 2 до 3' → '2-3'")
    print(f"  '¾ до 1' → '¾-1'")
    print(f"  'от 2 до 2¾' → '2-2¾'")
    print(f"  '1 до ¾' → '1-¾'")

if __name__ == "__main__":
    fix_ranges()
