#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import glob
import os
from bs4 import BeautifulSoup
import re
import json

def get_context(text, match_start, match_end, num_words=8):
    """
    Возвращает контекст (8 слов до и после)
    """
    before = text[:match_start].split()
    after = text[match_end:].split()
    
    before_ctx = " ".join(before[-num_words:])
    after_ctx = " ".join(after[:num_words])
    
    return f"...{before_ctx} [TARGET] {after_ctx}..."

def find_oil_discrepancies():
    ru_dir = "temp_ru_02/OEBPS"
    en_dir = "temp_en_orig/OEBPS"
    
    report_data = []
    
    # Паттерны
    ru_oil_pattern = re.compile(r'\b(масл[а-я]*)\b', re.IGNORECASE)
    en_oil_pattern = re.compile(r'\b(butter|oil)\b', re.IGNORECASE)

    # Список файлов
    ru_files = sorted(glob.glob(os.path.join(ru_dir, "*.htm")))
    
    count_butter_fixed = 0
    count_olive_fixed = 0
    
    for ru_filepath in ru_files:
        filename = os.path.basename(ru_filepath)
        en_filepath = os.path.join(en_dir, filename)
        
        if not os.path.exists(en_filepath):
            continue
            
        with open(ru_filepath, 'r', encoding='utf-8') as f:
            ru_soup = BeautifulSoup(f.read(), 'html.parser')
            
        with open(en_filepath, 'r', encoding='utf-8') as f:
            en_soup = BeautifulSoup(f.read(), 'html.parser')
            
        # Итерируемся по элементам с ID (параграфы, заголовки, списки)
        # Это якоря для сопоставления
        for ru_elem in ru_soup.find_all(True, {"id": True}):
            elem_id = ru_elem['id']
            
            # Ищем "масло" в русском тексте элемента
            ru_text = ru_elem.get_text()
            ru_matches = list(ru_oil_pattern.finditer(ru_text))
            
            if not ru_matches:
                continue
                
            # Ищем соответствующий английский элемент
            en_elem = en_soup.find(id=elem_id)
            if not en_elem:
                continue
                
            en_text = en_elem.get_text()
            en_matches = list(en_oil_pattern.finditer(en_text))

            # Попытка сопоставить по порядку
            # Если количество совпадений отличается, это сложно, но попробуем
            # В большинстве случаев: 1 "масло" -> 1 "butter/oil"
            
            # Проходим по всем русским "масло"
            # Для каждого пытаемся найти английское соответствие
            # Эвристика: сопоставляем i-е русское с i-м английским (если их кол-во совпадает)
            # Если не совпадает - пропускаем (слишком опасно автоматизировать)
            
            if len(ru_matches) == len(en_matches):
                for i, ru_match in enumerate(ru_matches):
                    ru_word = ru_match.group(1)
                    ru_context_full = ru_text[max(0, ru_match.start()-50):min(len(ru_text), ru_match.end()+50)]
                    
                    en_match = en_matches[i]
                    en_word_full = en_text[max(0, en_match.start()-50):min(len(en_text), en_match.end()+50)]
                    en_term = en_match.group(1).lower()
                    
                    # Проверяем контекст английского
                    # Если там 'olive oil' или 'butter' - это бинго
                    
                    real_oil_type = None
                    
                    # Смотрим контекст английского слова (чуть шире, чем само слово)
                    en_context_snippet = en_text[max(0, en_match.start()-20):min(len(en_text), en_match.end()+20)].lower()
                    
                    if 'butter' in en_context_snippet:
                        real_oil_type = 'butter'
                    elif 'olive oil' in en_context_snippet:
                        real_oil_type = 'olive'
                    elif 'vegetable oil' in en_context_snippet:
                         real_oil_type = 'vegetable' # Нейтральное
                    elif 'oil' in en_term:
                        # generic oil
                        real_oil_type = 'oil'
                    
                    # Теперь проверяем русское слово на наличие уточнения
                    is_clarified = False
                    ru_context_snippet = ru_text[max(0, ru_match.start()-20):min(len(ru_text), ru_match.end()+20)].lower()
                    
                    if 'сливочн' in ru_context_snippet:
                        is_clarified = True
                    if 'оливков' in ru_context_snippet:
                        is_clarified = True
                    if 'растительн' in ru_context_snippet:
                        is_clarified = True

                    # Логика исправления
                    correction_needed = False
                    correction_text = ""
                    
                    if not is_clarified:
                        if real_oil_type == 'butter':
                            correction_needed = True
                            # Определяем форму слова для замены
                            # масло -> сливочное масло
                            # масла -> сливочного масла
                            # маслу -> сливочному маслу
                            # маслом -> сливочным маслом
                            # масле -> сливочном масле
                            if ru_word.lower() == 'масло': correction_text = 'сливочное масло'
                            elif ru_word.lower() == 'масла': correction_text = 'сливочного масла'
                            elif ru_word.lower() == 'маслу': correction_text = 'сливочному маслу'
                            elif ru_word.lower() == 'маслом': correction_text = 'сливочным маслом'
                            elif ru_word.lower() == 'масле': correction_text = 'сливочном масле'
                            # С сохранением регистра первой буквы
                            if ru_word[0].isupper():
                                correction_text = correction_text.capitalize()
                            
                            count_butter_fixed += 1

                        elif real_oil_type == 'olive':
                            correction_needed = True
                            if ru_word.lower() == 'масло': correction_text = 'оливковое масло'
                            elif ru_word.lower() == 'масла': correction_text = 'оливкового масла'
                            elif ru_word.lower() == 'маслу': correction_text = 'оливковому маслу'
                            elif ru_word.lower() == 'маслом': correction_text = 'оливковым маслом'
                            elif ru_word.lower() == 'масле': correction_text = 'оливковом масле'
                            if ru_word[0].isupper():
                                correction_text = correction_text.capitalize()
                            
                            count_olive_fixed += 1

                    if correction_needed:
                        report_data.append({
                            "file": filename,
                            "id": elem_id,
                            "ru_word": ru_word,
                            "ru_context": get_context(ru_text, ru_match.start(), ru_match.end()),
                            "en_word": en_term,
                            "en_context": get_context(en_text, en_match.start(), en_match.end()),
                            "correction": correction_text,
                            "type": real_oil_type
                        })

    # Сохраняем отчет в JSON
    with open("oil_fix_report.json", "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
        
    # Выводим текстовый отчет
    print(f"Найдено {len(report_data)} мест для исправления.")
    print(f"Butter -> Сливочное: {count_butter_fixed}")
    print(f"Olive Oil -> Оливковое: {count_olive_fixed}")

if __name__ == "__main__":
    find_oil_discrepancies()
