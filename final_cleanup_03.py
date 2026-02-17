#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Финальная очистка и проверка Hazan_RU_Final_0.3.epub
"""

import os
import re
import zipfile
import shutil
from bs4 import BeautifulSoup
from collections import defaultdict

EPUB_FILE = "Hazan_RU_Final_0.3.epub"
TEMP_DIR = "temp_cleanup_03"
OUTPUT_FILE = "Hazan_RU_Final_0.3_cleaned.epub"

def cleanup_and_check():
    print("🔍 Распаковка EPUB...")
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    
    with zipfile.ZipFile(EPUB_FILE, 'r') as z:
        z.extractall(TEMP_DIR)
    
    stats = {
        'asterisks_removed': 0,
        'underscores_removed': 0,
        'gnocchi_fixed': 0,
        'english_words_found': defaultdict(int)
    }
    
    # Находим HTML файлы
    html_files = []
    for root, dirs, files in os.walk(TEMP_DIR):
        for f in files:
            if f.endswith(('.html', '.htm', '.xhtml')):
                html_files.append(os.path.join(root, f))
    
    print(f"📂 Найдено {len(html_files)} HTML файлов\n")
    
    # Паттерны для поиска английских слов (общие артикли и предлоги)
    english_pattern = re.compile(r'\b(the|and|with|for|from|that|this|are|was|were|have|has|been)\b', re.IGNORECASE)
    
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
            
            # 1. Удаление Markdown астерисков: *слово* -> слово
            if '*' in text:
                # Убираем *текст* (но не внутри HTML тегов)
                text = re.sub(r'\*([^\*]+)\*', r'\1', text)
                if text != original:
                    stats['asterisks_removed'] += original.count('*') - text.count('*')
            
            # 2. Удаление подчеркиваний: _слово_ -> слово
            if '_' in text:
                text = re.sub(r'_([^_]+)_', r'\1', text)
                if text != original:
                    stats['underscores_removed'] += original.count('_') - text.count('_')
            
            # 3. Исправление ГнOcchi -> Гнокки
            if 'гнOcchi' in text.lower():
                text = re.sub(r'ГнOcchi', 'Гнокки', text)
                text = re.sub(r'гнOcchi', 'гнокки', text)
                text = re.sub(r'ГНOCCHI', 'ГНОККИ', text)
                if text != original:
                    stats['gnocchi_fixed'] += 1
            
            # 4. Поиск английских слов
            matches = english_pattern.findall(text)
            if matches:
                for word in matches:
                    stats['english_words_found'][word.lower()] += 1
            
            # Применяем изменения
            if text != original:
                text_node.replace_with(text)
                file_changed = True
        
        # Сохраняем файл если были изменения
        if file_changed:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(str(soup))
    
    # Отчет
    print("=" * 60)
    print("📊 РЕЗУЛЬТАТЫ ПРОВЕРКИ:")
    print("=" * 60)
    print(f"✂️  Удалено астерисков (*): {stats['asterisks_removed']}")
    print(f"✂️  Удалено подчеркиваний (_): {stats['underscores_removed']}")
    print(f"✅ Исправлено 'ГнOcchi': {stats['gnocchi_fixed']}")
    
    if stats['english_words_found']:
        print(f"\n⚠️  НАЙДЕНЫ АНГЛИЙСКИЕ СЛОВА:")
        for word, count in sorted(stats['english_words_found'].items(), key=lambda x: -x[1])[:20]:
            print(f"   '{word}': {count} раз")
        print(f"\n   Всего уникальных английских слов: {len(stats['english_words_found'])}")
    else:
        print(f"\n✅ Английских слов не найдено!")
    
    # Пересборка EPUB
    print(f"\n📦 Сборка {OUTPUT_FILE}...")
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
    
    cwd = os.getcwd()
    os.chdir(TEMP_DIR)
    os.system(f"zip -0 -X ../{OUTPUT_FILE} mimetype")
    os.system(f"zip -r -q ../{OUTPUT_FILE} META-INF OEBPS -x '*.DS_Store'")
    
    # Проверяем структуру (OPF в корне или в OEBPS)
    if os.path.exists("Haza_9780307958303_epub_opf_r1.opf"):
        os.system(f"zip -r -q ../{OUTPUT_FILE} *.opf *.ncx")
    
    os.chdir(cwd)
    
    # Очистка
    shutil.rmtree(TEMP_DIR)
    
    print(f"\n🎉 Готово! Файл сохранен как: {OUTPUT_FILE}")
    print(f"📏 Размер: {os.path.getsize(OUTPUT_FILE) / 1024 / 1024:.1f} MB")

if __name__ == "__main__":
    cleanup_and_check()
