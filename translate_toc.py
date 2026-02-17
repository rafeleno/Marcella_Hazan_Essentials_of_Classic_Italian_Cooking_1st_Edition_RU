#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Перевод оглавления (Table of Contents) в EPUB
"""

import os
import zipfile
import shutil
import re
from bs4 import BeautifulSoup

EPUB_FILE = "Hazan_RU_Final_0.3.epub"
TEMP_DIR = "temp_translate_toc"
OUTPUT_FILE = "Hazan_RU_Final_0.3.epub"

# Словарь переводов глав
TRANSLATIONS = {
    "Title Page": "Титульная страница",
    "Copyright": "Авторские права",
    "Other Books by This Author": "Другие книги автора",
    "Dedication": "Посвящение",
    "Preface": "Предисловие",
    "Introduction": "Введение",
    "Fundamentals": "Основы",
    "Appetizers": "Закуски",
    "Soups": "Супы",
    "Pasta": "Паста",
    "Risotto": "Ризотто",
    "Gnocchi": "Гнокки",
    "Crespelle": "Креспелле",
    "Polenta": "Полента",
    "Frittate": "Фриттата",
    "Fish and Shellfish": "Рыба и морепродукты",
    "Chicken, Squab, Duck, and Rabbit": "Курица, голубь, утка и кролик",
    "Veal": "Телятина",
    "Beef": "Говядина",
    "Lamb": "Баранина",
    "Pork": "Свинина",
    "Variety Meats": "Субпродукты",
    "Vegetables": "Овощи",
    "Salads": "Салаты",
    "Desserts": "Десерты",
    "Focaccia, Pizza, Bread, and Other Special Doughs": "Фокачча, пицца, хлеб и другое особое тесто",
    "At Table": "За столом",
    "Index": "Указатель",
    "About the Author": "Об авторе"
}

def translate_toc():
    print("🔍 Распаковка EPUB...")
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    
    with zipfile.ZipFile(EPUB_FILE, 'r') as z:
        z.extractall(TEMP_DIR)
    
    translated_count = 0
    
    # Ищем NCX файл (навигация)
    ncx_files = []
    toc_files = []
    
    for root, dirs, files in os.walk(TEMP_DIR):
        for f in files:
            if f.endswith('.ncx'):
                ncx_files.append(os.path.join(root, f))
            if 'toc' in f.lower() and f.endswith(('.html', '.xhtml')):
                toc_files.append(os.path.join(root, f))
    
    print(f"📂 Найдено NCX файлов: {len(ncx_files)}")
    print(f"📂 Найдено TOC файлов: {len(toc_files)}\n")
    
    # Обработка NCX (основной файл навигации)
    for ncx_path in ncx_files:
        print(f"🔄 Обработка {os.path.basename(ncx_path)}...")
        
        with open(ncx_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'xml')
        
        # В NCX названия глав находятся в <text> внутри <navLabel>
        for text_tag in soup.find_all('text'):
            original = text_tag.string
            if original and original.strip() in TRANSLATIONS:
                new_text = TRANSLATIONS[original.strip()]
                text_tag.string.replace_with(new_text)
                print(f"  ✅ '{original.strip()}' → '{new_text}'")
                translated_count += 1
        
        # Сохраняем
        with open(ncx_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
    
    # Обработка TOC HTML (если есть)
    for toc_path in toc_files:
        print(f"\n🔄 Обработка {os.path.basename(toc_path)}...")
        
        with open(toc_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # В HTML TOC названия обычно в <a> или <span>
        for tag in soup.find_all(['a', 'span', 'li', 'p']):
            text = tag.get_text(strip=True)
            if text in TRANSLATIONS:
                # Заменяем текст внутри тега
                if tag.string:
                    tag.string.replace_with(TRANSLATIONS[text])
                else:
                    # Если есть вложенные теги, заменяем текстовые узлы
                    for text_node in tag.find_all(string=True):
                        if text_node.strip() in TRANSLATIONS:
                            text_node.replace_with(TRANSLATIONS[text_node.strip()])
                print(f"  ✅ '{text}' → '{TRANSLATIONS[text]}'")
                translated_count += 1
        
        with open(toc_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
    
    print(f"\n{'='*60}")
    print(f"✅ Переведено названий глав: {translated_count}")
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

if __name__ == "__main__":
    translate_toc()
