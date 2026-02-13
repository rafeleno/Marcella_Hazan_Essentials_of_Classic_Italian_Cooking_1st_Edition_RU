import os
import re
from bs4 import BeautifulSoup

TEMP_DIR = "temp_epub_final_1_0"

FRACTIONS = {
    '¼': 0.25, '½': 0.5, '¾': 0.75,
    '⅓': 0.33, '⅔': 0.67,
    '⅛': 0.125, '⅜': 0.375, '⅝': 0.625, '⅞': 0.875
}

def parse_value(val_str):
    """Парсит строку '1½' или '2' или '¼' в float."""
    val_str = val_str.strip()
    total = 0.0
    
    # Ищем целое число
    integer_match = re.match(r'^(\d+)', val_str)
    if integer_match:
        total += int(integer_match.group(1))
        val_str = val_str[len(integer_match.group(1)):]
        
    # Ищем дробь
    for char, float_val in FRACTIONS.items():
        if char in val_str:
            total += float_val
            
    return total if total > 0 else None

def cm_str(inches):
    """Конвертирует в см и форматирует."""
    cm = inches * 2.54
    # Округляем до разумных значений
    if cm < 1: return f"{cm:.1f} см" # 0.6 см
    if abs(cm - round(cm)) < 0.1: return f"{int(round(cm))} см" # 5 см
    return f"{cm:.1f} см" # 4.5 см

def process_files():
    files_to_check = []
    for root, dirs, files in os.walk(TEMP_DIR):
        for file in files:
            if file.endswith('.htm') or file.endswith('.html'):
                files_to_check.append(os.path.join(root, file))
    
    # Regex: Группа 1 = число/дробь, Группа 2 = "дюйм...", Lookahead на отсутствие открывающей скобки
    # (?!...) - negative lookahead, чтобы не матчить, если уже есть (
    
    # Но regex с заменой проще делать через функцию sub.
    # Паттерн: (\d+(?:\s*[¼½¾⅓⅔⅛⅜⅝⅞])?|[¼½¾⅓⅔⅛⅜⅝⅞])(\s*дюйм[а-я]*)
    
    pattern = re.compile(r'(\d+(?:\s*[¼½¾⅓⅔⅛⅜⅝⅞])?|[¼½¾⅓⅔⅛⅜⅝⅞])(\s*дюйм[а-я]*)')
    
    count_fixed = 0
    
    for filepath in files_to_check:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        def replacer(match):
            val_str = match.group(1)
            suffix = match.group(2)
            full_match = match.group(0)
            
            # Проверяем, что идет ПОСЛЕ матча
            start, end = match.span()
            # Берем 10 символов после
            post_context = content[end:end+10]
            
            # Если уже есть скобка с цифрой или "см", пропускаем
            if re.match(r'\s*\(\d', post_context) or re.match(r'\s*\(\s*\d', post_context):
                return full_match
                
            # Иначе считаем
            inches = parse_value(val_str)
            if inches:
                cm = cm_str(inches)
                nonlocal count_fixed
                count_fixed += 1
                # print(f"  Fixing: {full_match} -> {full_match} ({cm})")
                return f"{full_match} ({cm})"
            return full_match

        new_content = pattern.sub(replacer, content)
        
        if new_content != content:
            # print(f"Fixed file: {os.path.basename(filepath)}")
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
    print(f"Всего добавлено метрических переводов: {count_fixed}")

if __name__ == "__main__":
    process_files()
