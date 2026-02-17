#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import glob
import os
from bs4 import BeautifulSoup
import re
import json

def get_context(text, match_start, match_end, num_words=8):
    before = text[:match_start].split()
    after = text[match_end:].split()
    return f"...{' '.join(before[-num_words:])} [TARGET] {' '.join(after[:num_words])}..."

def find_and_fix_oil():
    ru_dir = "temp_ru_02/OEBPS"
    en_dir = "temp_en_orig/OEBPS"
    
    report_data = []
    
    ru_oil_pattern = re.compile(r'\b(масл[а-я]*)\b', re.IGNORECASE)
    # Ищем butter, oil, lard (на всякий случай)
    en_oil_pattern = re.compile(r'\b(butter|oil|lard)\b', re.IGNORECASE)

    ru_files = sorted(glob.glob(os.path.join(ru_dir, "*.htm")))
    
    corrections_applied = 0
    
    for ru_filepath in ru_files:
        filename = os.path.basename(ru_filepath)
        en_filepath = os.path.join(en_dir, filename)
        
        if not os.path.exists(en_filepath):
            continue
            
        with open(ru_filepath, 'r', encoding='utf-8') as f:
            ru_content = f.read() # Читаем как текст для замен
            
        # Для анализа используем BeautifulSoup
        ru_soup = BeautifulSoup(ru_content, 'html.parser')
        with open(en_filepath, 'r', encoding='utf-8') as f:
            en_soup = BeautifulSoup(f.read(), 'html.parser')
            
        modified_content = ru_content
        
        # Словарь замен для текущего файла (чтобы не менять сразу и не сбивать оффсеты)
        # Лучше менять сразу, но идти с конца или использовать уникальные ключи?
        # Поскольку мы используем replace по уникальному контексту элемента, должно быть ок.
        # Но лучше всего пересобирать контент поэлементно.
        
        # Создадим список замен и применим их
        replacements_for_file = []

        for ru_elem in ru_soup.find_all(True, {"id": True}):
            elem_id = ru_elem['id']
            ru_text = ru_elem.get_text()
            ru_matches = list(ru_oil_pattern.finditer(ru_text))
            
            if not ru_matches:
                continue
                
            en_elem = en_soup.find(id=elem_id)
            if not en_elem:
                continue
                
            en_text = en_elem.get_text()
            en_matches = list(en_oil_pattern.finditer(en_text))

            if len(ru_matches) == len(en_matches):
                for i, ru_match in enumerate(ru_matches):
                    ru_word = ru_match.group(1)
                    en_match = en_matches[i]
                    en_term = en_match.group(1).lower() # butter или oil
                    
                    # Анализ типа масла
                    real_oil_type = None
                    
                    # Смотрим 50 символов ДО английского слова
                    en_prefix = en_text[max(0, en_match.start()-50):en_match.start()].lower()
                    
                    if en_term == 'butter':
                        real_oil_type = 'butter'
                    elif en_term == 'oil':
                        if 'olive' in en_prefix[-20:]: # "olive oil"
                            real_oil_type = 'olive'
                        elif 'vegetable' in en_prefix[-20:]: # "vegetable oil"
                             real_oil_type = 'vegetable'
                        elif 'peanut' in en_prefix:
                             real_oil_type = 'peanut'
                        else:
                             real_oil_type = 'generic_oil'
                    
                    # Проверяем русское уточнение
                    ru_prefix = ru_text[max(0, ru_match.start()-50):ru_match.start()].lower()
                    is_clarified = False
                    if 'сливочн' in ru_prefix or 'сливочн' in ru_text[ru_match.start():ru_match.end()+20].lower(): is_clarified = True
                    if 'оливков' in ru_prefix or 'оливков' in ru_text[ru_match.start():ru_match.end()+20].lower(): is_clarified = True
                    if 'растительн' in ru_prefix: is_clarified = True
                    if 'арахисовое' in ru_prefix: is_clarified = True

                    correction = None
                    
                    if not is_clarified:
                        if real_oil_type == 'butter':
                            # Склоняем "сливочное"
                            if ru_word.lower() == 'масло': correction = 'сливочное масло'
                            elif ru_word.lower() == 'масла': correction = 'сливочного масла'
                            elif ru_word.lower() == 'маслу': correction = 'сливочному маслу'
                            elif ru_word.lower() == 'маслом': correction = 'сливочным маслом'
                            elif ru_word.lower() == 'масле': correction = 'сливочном масле'
                        elif real_oil_type == 'olive':
                            if ru_word.lower() == 'масло': correction = 'оливковое масло'
                            elif ru_word.lower() == 'масла': correction = 'оливкового масла'
                            elif ru_word.lower() == 'маслу': correction = 'оливковому маслу'
                            elif ru_word.lower() == 'маслом': correction = 'оливковым маслом'
                            elif ru_word.lower() == 'масле': correction = 'оливковом масле'
                    
                    if correction:
                        # Сохраняем регистр первой буквы
                        if ru_word[0].isupper():
                            correction = correction.capitalize()
                        elif ru_word.isupper(): # МАСЛО -> СЛИВОЧНОЕ МАСЛО
                             correction = correction.upper()

                        # Формируем данные для замены
                        # Чтобы заменить точно в тексте HTML, нам нужно взять HTML элемента
                        # И заменить первое вхождение (если мы идем по порядку)
                        # Но это сложно из-за тегов.
                        # Самый надежный способ - заменить в исходном тексте элемента, но осторожно.
                        
                        replacements_for_file.append({
                            "elem_id": elem_id,
                            "original": ru_word,
                            "replacement": correction,
                            "context_start": ru_match.start(), # Это смещение в plain text, не в HTML!
                            "type": real_oil_type
                        })
                        
                        report_data.append({
                            "file": filename,
                            "id": elem_id,
                            "ru_word": ru_word,
                            "correction": correction,
                            "type": real_oil_type
                        })

        # Применяем замены к файлу
        # Поскольку у нас смещения в plain text, а мы правим HTML, нам нужно найти текстовый узел в soup и заменить его
        # Или, более просто: ищем элемент по ID в soup, и делаем replace текста
        
        # Переоткрываем soup для редактирования
        soup_edit = BeautifulSoup(modified_content, 'html.parser')
        
        # Сортируем замены с конца, чтобы не сбить порядок
        # Но у нас нет точных индексов в HTML.
        # Поэтому мы будем заменять текст внутри элементов поэлементно.
        
        # Группируем замены по ID элемента
        replacements_by_id = {}
        for r in replacements_for_file:
            if r['elem_id'] not in replacements_by_id:
                replacements_by_id[r['elem_id']] = []
            replacements_by_id[r['elem_id']].append(r)
            
        for eid, repls in replacements_by_id.items():
            elem = soup_edit.find(id=eid)
            if not elem: continue
            
            # Мы должны заменить i-е вхождение слова в тексте элемента
            # Это сложно, если есть теги внутри.
            # Попробуем str(elem), заменить нужные вхождения и вставить обратно.
            # Но repls могут быть "масла" -> "сливочного масла", "масла" -> "оливкового масла".
            # Нужно знать, какое именно "масла" менять.
            # У нас есть порядок!
            
            # Получаем все текстовые узлы или просто работаем со строкой элемента (если там немного тегов)
            elem_str = str(elem)
            
            # Функция замены n-го вхождения
            def replace_nth(string, sub, want, n):
                where = [m.start() for m in re.finditer(re.escape(sub), string)]
                if len(where) > n:
                    before = string[:where[n]]
                    after = string[where[n] + len(sub):]
                    return before + want + after
                return string
                
            # Проблема: у нас смещения из plain text (ru_match.start()), они бесполезны для HTML string.
            # Но мы знаем, что сопоставляли i-е русское слово с i-м английским.
            # Значит, если в repls есть запись для index=0, мы должны заменить 1-е вхождение слова.
            
            # Нужен счетчик: какое по счету слово "масло" в plain text мы сейчас обрабатываем.
            # В `replacements_for_file` мы добавляли их по порядку обхода `finditer`.
            # Значит, для данного ID у нас есть список замен, соответствующих порядку вхождений в тексте.
            
            # Но ВНИМАНИЕ: регулярка `finditer` искала по `ru_elem.get_text()`.
            # А заменять мы будем в `str(elem)`.
            # В `str(elem)` есть теги. Порядок слов "масло" в `str(elem)` должен (обычно) совпадать с порядком в `get_text()`, если теги не разрывают слово.
            
            # Будем считать, что порядок совпадает.
            # Нам нужно отслеживать, какие вхождения какого слова мы меняем.
            # Пример: текст "масло и масло". replacements: [{orig: масло, repl: сл.масло}, {orig: масло, repl: ол.масло}]
            # Мы должны заменить 1-е "масло" на "сл.масло", 2-е на "ол.масло".
            
            # Но мы не можем просто replace_nth, потому что после первой замены строка изменится!
            # Лучший способ: разбить строку на токены? Нет.
            
            # Попробуем заменить все сразу, используя callback? Сложно.
            # Попробуем использовать маркеры.
            
            # Или просто: идем по списку замен. Но как найти правильное вхождение?
            # Если мы меняем 1-е "масло" на "X", то 2-е "масло" (которое было вторым) станет первым (или вторым, если X не содержит "масло").
            # В нашем случае X ("сливочное масло") СОДЕРЖИТ слово "масло"!
            # Это сломает индексы.
            
            # Решение: заменять на уникальные плейсхолдеры, а потом плейсхолдеры на нужный текст.
            # Например: __BUTTER_FIX_1__, __OLIVE_FIX_2__
            
            temp_elem_str = elem_str
            # Нужно найти смещения в HTML строке. Это сложно.
            
            # Упрощение: будем считать, что в одном элементе редко бывает микс "сливочное" и "оливковое" БЕЗ уточнений.
            # Если бывает, мы можем ошибиться.
            # Но у нас есть `butter` и `oil`.
            
            # Давайте применим более безопасный метод:
            # 1. Находим все вхождения паттерна в HTML строке.
            # 2. Сопоставляем их с нашими заменами (по порядку).
            # 3. Формируем новую строку.
            
            matches = list(re.finditer(ru_oil_pattern, temp_elem_str)) # Ищем в HTML строке
            # Фильтруем те, что внутри тегов (начинаются на < и не заканчиваются >? Нет, сложнее).
            # Просто надеемся, что "масло" не встречается в атрибутах тегов (id="maslo"? вряд ли).
            
            if len(matches) != len(repls):
                 # Кол-во совпадений в HTML отличается от plain text?
                 # Значит где-то внутри тега или разрыв. Пропускаем этот элемент от греха подальше.
                 # Или применяем частичные замены.
                 # В `repls` мы сохранили ТОЛЬКО те, где `len(ru_matches) == len(en_matches)`.
                 # Если в HTML матчей больше (из-за атрибутов), это проблема.
                 # Но `repls` содержит замены только для тех слов, что нашлись в `get_text()`.
                 
                 # Ладно, давайте попробуем replace. Если уникальное слово - просто replace.
                 # Если повторяется - аккуратно.
                 
                 # Если у нас только одна замена на элемент - все просто.
                 pass

            # Идем с КОНЦА, чтобы не сбивать индексы
            # Нам нужно сопоставить `repls` (которые для plain text) с `matches` (в html).
            # Обычно они 1-в-1. 
            
            # Давайте соберем все "масло" из HTML, и если их кол-во совпадает с `repls`, заменим по индексам.
            # Но `repls` содержит замены не для всех слов, а только для тех, где мы нашли mismatch.
            # Нам нужен полный список всех "масло" в элементе, чтобы знать индекс.
            
            # Восстанавливаем полный список "масло" из `ru_elem.get_text()` (мы это уже делали в цикле).
            # `ru_matches` - это список ВСЕХ вхождений "масло" в plain text.
            # `repls` - это подмножество, привязанное к индексам `ru_matches`? 
            # Нет, сейчас `repls` это просто список. Мне нужно знать индекс в `ru_matches`.
            
            pass 
        
        # Перепишем логику замены:
        # 1. Для каждого элемента получаем список ВСЕХ "масло" (как было при анализе).
        # 2. Для каждого i-го масла решаем, нужно ли менять.
        # 3. Собираем список: (i, old_word, new_word).
        # 4. В HTML строке находим все "масло". Если их кол-во >= кол-ву в plain text, пытаемся заменить i-е.
        
    # Но так как мы не можем легко менять HTML, давайте используем `replace` с регуляркой
    # Но с учетом порядка.
    
    # ...
    # (Реализация сложная, поэтому я упрощу: буду использовать `soup.find(text=...).replace_with(...)`
    # Это работает с текстовыми узлами напрямую!
    
    # Новый подход в скрипте ниже.

def robust_fix():
    ru_dir = "temp_ru_02/OEBPS"
    en_dir = "temp_en_orig/OEBPS"
    
    ru_files = sorted(glob.glob(os.path.join(ru_dir, "*.htm")))
    
    corrected_count = 0
    report = []
    
    for ru_filepath in ru_files:
        filename = os.path.basename(ru_filepath)
        en_filepath = os.path.join(en_dir, filename)
        
        if not os.path.exists(en_filepath):
            continue
            
        with open(ru_filepath, 'r', encoding='utf-8') as f:
            ru_soup = BeautifulSoup(f.read(), 'html.parser')
        with open(en_filepath, 'r', encoding='utf-8') as f:
            en_soup = BeautifulSoup(f.read(), 'html.parser')
            
        file_changed = False
        
        for ru_elem in ru_soup.find_all(True, {"id": True}):
            elem_id = ru_elem['id']
            
            # Используем NavigableString для замены прямо в дереве
            # Находим все текстовые узлы внутри элемента
            results = ru_elem.find_all(text=re.compile(r'масл[а-я]*', re.IGNORECASE))
            if not results:
                continue

            # Для сопоставления нам нужен ПОЛНЫЙ текст элемента и сопоставление с EN
            # Чтобы понять, какой именно NavigableString соответствует какому EN слову.
            # Это сложно.
            
            # Возвращаемся к get_text().
            ru_text_full = ru_elem.get_text()
            matches = list(re.finditer(r'\b(масл[а-я]*)\b', ru_text_full, re.IGNORECASE))
            
            en_elem = en_soup.find(id=elem_id)
            if not en_elem: continue
            en_text_full = en_elem.get_text()
            en_matches = list(re.finditer(r'\b(butter|oil|lard)\b', en_text_full, re.IGNORECASE))
            
            if len(matches) != len(en_matches):
                continue
                
            # Составляем карту изменений: индекс в тексте -> на что менять
            changes = {}
            for i, match in enumerate(matches):
                word = match.group(1)
                en_match = en_matches[i]
                en_term = en_match.group(1).lower()
                en_start = en_match.start()
                
                # Анализ типа
                oil_type = None
                en_prefix = en_text_full[max(0, en_start-50):en_start].lower()
                
                if en_term == 'butter':
                    oil_type = 'butter'
                elif en_term == 'oil':
                    if 'olive' in en_prefix[-20:]: oil_type = 'olive'
                    elif 'vegetable' in en_prefix[-20:]: oil_type = 'vegetable'
                    
                # Анализ русского
                ru_start = match.start()
                ru_prefix = ru_text_full[max(0, ru_start-50):ru_start].lower()
                ru_suffix = ru_text_full[ru_start:ru_start+20].lower() # само слово + чуть дальше
                
                is_clarified = False
                if 'сливочн' in ru_prefix or 'сливочн' in ru_suffix: is_clarified = True
                if 'оливков' in ru_prefix or 'оливков' in ru_suffix: is_clarified = True
                if 'растительн' in ru_prefix: is_clarified = True
                
                if not is_clarified:
                     correction = None
                     if oil_type == 'butter':
                        if word.lower() == 'масло': correction = 'сливочное масло'
                        elif word.lower() == 'масла': correction = 'сливочного масла'
                        elif word.lower() == 'маслу': correction = 'сливочному маслу'
                        elif word.lower() == 'маслом': correction = 'сливочным маслом'
                        elif word.lower() == 'масле': correction = 'сливочном масле'
                     elif oil_type == 'olive':
                        if word.lower() == 'масло': correction = 'оливковое масло'
                        elif word.lower() == 'масла': correction = 'оливкового масла'
                        elif word.lower() == 'маслу': correction = 'оливковому маслу'
                        elif word.lower() == 'маслом': correction = 'оливковым маслом'
                        elif word.lower() == 'масле': correction = 'оливковом масле'
                     
                     if correction:
                         if word[0].isupper(): correction = correction.capitalize()
                         elif word.isupper(): correction = correction.upper()
                         
                         changes[i] = (word, correction)
            
            if not changes:
                continue
                
            # Применяем изменения к текстовым узлам
            # Идем по всем текстовым узлам, ищем слова, считаем их глобальный индекс.
            global_idx = 0
            
            for text_node in results: # results это список текстовых узлов с 'масл...'
                # В одном узле может быть несколько слов
                # Нам нужно найти их и заменить, если их global_idx в changes
                
                new_text = text_node.string
                node_matches = list(re.finditer(r'\b(масл[а-я]*)\b', new_text, re.IGNORECASE))
                
                offset_shift = 0
                for img_in_node, m in enumerate(node_matches):
                    # Текущий глобальный индекс слова "масло" в элементе
                    current_global_idx = global_idx
                    global_idx += 1 # Увеличиваем счетчик для следующего слова
                    
                    if current_global_idx in changes:
                        old_w, new_w = changes[current_global_idx]
                        
                        # Заменяем в node text
                        start = m.start() + offset_shift
                        end = m.end() + offset_shift
                        
                        # Проверка (на всякий случай)
                        if new_text[start:end] != old_w:
                             # Может быть разный регистр в поиске и в changes (хотя мы брали group(1))
                             pass
                             
                        new_text = new_text[:start] + new_w + new_text[end:]
                        offset_shift += len(new_w) - len(old_w)
                        
                        report.append(f"{filename}#{elem_id}: {old_w} -> {new_w}")
                        corrected_count += 1
                        file_changed = True
                
                if new_text != text_node.string:
                    text_node.replace_with(new_text)
            
            # Внимание: логика global_idx работает, только если soup.find_all(text=...) 
            # возвращает узлы в том же порядке, что и get_text(). Обычно да.
            
        if file_changed:
            with open(ru_filepath, 'w', encoding='utf-8') as f:
                f.write(str(ru_soup))

    print(f"Всего исправлено: {corrected_count}")
    with open("fix_report_final.txt", "w") as f:
        f.write("\n".join(report))

if __name__ == "__main__":
    robust_fix()
