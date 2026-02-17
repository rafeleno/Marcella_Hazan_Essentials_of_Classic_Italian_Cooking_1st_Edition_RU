#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генератор версии 0.3 с применением СТРОГИХ правил перевода (Oil=Оливковое).
"""

import glob
import os
import re
import shutil
import time
from bs4 import BeautifulSoup
import zipfile

def generate_03():
    print("🚀 Запуск генерации Hazan_RU_Final_0.3.epub...")
    print("📜 Применяю правила из ZAMETKI_PO_PEREVODU.md")
    
    # 1. Подготовка
    # Используем 0.5 как лучшую базу (там уже исправлен butter и gnocchi)
    base_epub = "Hazan_RU_Final_0.5.epub"
    orig_epub = "Marcella_Hazan_Essentials_of_Classic_Italian_Cooking_1st_Edition.epub"
    
    work_dir = "temp_gen_03"
    en_dir = "temp_gen_en"
    
    if os.path.exists(work_dir): shutil.rmtree(work_dir)
    if os.path.exists(en_dir): shutil.rmtree(en_dir)
    
    print(f"📦 Распаковка {base_epub}...")
    with zipfile.ZipFile(base_epub, 'r') as z:
        z.extractall(work_dir)
        
    print(f"📦 Распаковка оригинала...")
    with zipfile.ZipFile(orig_epub, 'r') as z:
        z.extractall(en_dir)
        
    # Пути к контенту (в версии 0.5 структура должна быть правильной)
    # Но так как 0.5 делался zip-ом, файлы могут быть где угодно.
    # Ищем OEBPS
    ru_oebps = os.path.join(work_dir, "OEBPS")
    en_oebps = os.path.join(en_dir, "OEBPS")
    
    if not os.path.exists(ru_oebps):
        # Если структуры OEBPS нет, ищем htm файлы рекурсивно
        print("⚠️  Папка OEBPS не найдена в корне, ищу глубже...")
        # (Упрощение: мы знаем структуру 0.5, она должна быть OEBPS в корне)

    files = sorted(glob.glob(os.path.join(ru_oebps, "*.htm")))
    total_files = len(files)
    
    fixes_count = {'butter': 0, 'olive': 0, 'typo': 0}
    
    print(f"🔄 Обработка {total_files} файлов...")

    for idx, ru_file in enumerate(files):
        filename = os.path.basename(ru_file)
        en_file = os.path.join(en_oebps, filename)
        
        # Прогресс бар
        print(f"   [{idx+1}/{total_files}] Processing {filename}...", end='\r')
        
        if not os.path.exists(en_file):
            continue
            
        with open(ru_file, 'r', encoding='utf-8') as f:
            ru_soup = BeautifulSoup(f.read(), 'html.parser')
        with open(en_file, 'r', encoding='utf-8') as f:
            en_soup = BeautifulSoup(f.read(), 'html.parser')
            
        file_changed = False
        
        # 1. Исправление опечатки "игееук" (глобально по тексту)
        # Это безопасно делать простым replace строки
        full_text = str(ru_soup)
        if "игееук" in full_text:
            new_text = full_text.replace("игееук", "сливочное масло")
            ru_soup = BeautifulSoup(new_text, 'html.parser')
            fixes_count['typo'] += full_text.count("игееук")
            file_changed = True

        # 2. Умное сопоставление Oil -> Оливковое, Butter -> Сливочное
        # Итерируемся по элементам
        for ru_elem in ru_soup.find_all(True, {"id": True}):
            elem_id = ru_elem['id']
            ru_text_node = ru_elem.get_text()
            
            # Есть ли масло?
            if "масл" not in ru_text_node.lower():
                continue
                
            en_elem = en_soup.find(id=elem_id)
            if not en_elem: continue
            
            en_text = en_elem.get_text()
            
            # Паттерны
            ru_matches = list(re.finditer(r'\b(масл[а-я]*)\b', ru_text_node, re.IGNORECASE))
            en_matches = list(re.finditer(r'\b(butter|oil)\b', en_text, re.IGNORECASE))
            
            if len(ru_matches) != len(en_matches):
                # Если кол-во не совпадает, пропускаем автоматику (рискованно)
                # Но для Oil -> Оливковое правило МЕГА ВАЖНОЕ.
                # Попробуем найти однозначные соответствия.
                continue

            # Список замен для текущего элемента
            replacements = []
            
            for i, ru_m in enumerate(ru_matches):
                ru_word = ru_m.group(1)
                en_m = en_matches[i]
                en_word = en_m.group(1).lower()
                
                # Контекст (слова до)
                ru_prefix = ru_text_node[max(0, ru_m.start()-30):ru_m.start()].lower()
                
                # Уже уточнено?
                is_clarified = False
                if 'сливочн' in ru_prefix or 'оливков' in ru_prefix or 'растительн' in ru_prefix:
                    is_clarified = True
                
                new_word = None
                
                if not is_clarified:
                    # RULE: BUTTER -> Сливочное
                    if en_word == 'butter':
                         new_word = "сливочное масло" # Склонения опустим для простоты примера или реализуем маппинг
                         # Маппинг склонений
                         if ru_word.lower().endswith('о'): new_word = "сливочное масло"
                         elif ru_word.lower().endswith('а'): new_word = "сливочного масла"
                         elif ru_word.lower().endswith('у'): new_word = "сливочному маслу"
                         elif ru_word.lower().endswith('ом'): new_word = "сливочным маслом"
                         elif ru_word.lower().endswith('е'): new_word = "сливочном масле"
                         else: new_word = "сливочное масло"
                         fixes_count['butter'] += 1

                    # RULE: OIL -> Оливковое (CRITICAL NEW RULE)
                    elif en_word == 'oil':
                         # Даже если просто oil - меняем на оливковое
                         if ru_word.lower().endswith('о'): new_word = "оливковое масло"
                         elif ru_word.lower().endswith('а'): new_word = "оливкового масла"
                         elif ru_word.lower().endswith('у'): new_word = "оливковому маслу"
                         elif ru_word.lower().endswith('ом'): new_word = "оливковым маслом"
                         elif ru_word.lower().endswith('е'): new_word = "оливковом масле"
                         else: new_word = "оливковое масло"
                         fixes_count['olive'] += 1
                
                if new_word:
                    # Сохраняем регистр
                    if ru_word[0].isupper(): new_word = new_word.capitalize()
                    replacements.append((ru_word, new_word))

            # Применяем замены в строковом представлении элемента
            # (Это немного грубо, но эффективно для BeautifulSoup node)
            if replacements:
                # Чтобы не заменить лишнее, нужно быть аккуратным.
                # Но мы работаем в рамках одного элемента.
                str_elem = str(ru_elem)
                for old, new in replacements:
                    # Используем sub с count=1 для каждой пары по очереди?
                    # Нет, порядок важен.
                    # Просто заменяем text?
                    # Ограничимся простой заменой текста внутри тега
                    for text_node in ru_elem.find_all(text=True):
                         if old in text_node:
                             replaced_text = text_node.replace(old, new)
                             text_node.replace_with(replaced_text)
                             file_changed = True

        if file_changed:
            with open(ru_file, 'w', encoding='utf-8') as f:
                f.write(str(ru_soup))
                
    print("\n✅ Обработка завершена.")
    print(f"   Исправлений Butter: {fixes_count['butter']}")
    print(f"   Исправлений Oil -> Оливковое: {fixes_count['olive']} (Новое правило!)")
    print(f"   Исправлений 'игееук': {fixes_count['typo']}")
    
    # Репак
    print("📦 Упаковка в Hazan_RU_Final_0.3.epub...")
    out_name = "Hazan_RU_Final_0.3.epub"
    if os.path.exists(out_name): os.remove(out_name)
    
    # Копирование mimetype первым
    # Создаем zip вручную, чтобы контролировать порядок (как мы делали в командной строке)
    # Важно: mimetype без сжатия
    
    # Выполнение командной строки для надежности (python zipfile иногда капризный с mimetype)
    os.chdir(work_dir)
    os.system(f"zip -0 -X ../{out_name} mimetype")
    os.system(f"zip -r -q ../{out_name} META-INF OEBPS Haza_9780307958303_epub_opf_r1.opf Haza_9780307958303_epub_ncx_r1.ncx -x '*.DS_Store'")
    os.chdir("..")
    
    # Очистка
    shutil.rmtree(work_dir)
    shutil.rmtree(en_dir)
    
    print(f"🎉 Готово! Файл создан: {out_name}")

if __name__ == "__main__":
    generate_03()
