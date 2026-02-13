import os
import re

TEMP_DIR = "temp_epub_final_1_0"

def fix_broken_ranges():
    count_fixed = 0
    
    files_to_check = []
    for root, dirs, files in os.walk(TEMP_DIR):
        for file in files:
            if file.endswith('.htm') or file.endswith('.html'):
                files_to_check.append(os.path.join(root, file))
                
    for filepath in files_to_check:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        original_content = content
        
        # 1. Исправление "от 1от 0" -> "от 10"
        # Паттерн: от (\d)от (\d)
        content = re.sub(r'от\s+(\d)\s*от\s+(\d)', r'от \1\2', content)
        
        # Также для "займет от 2от 5" -> "от 25"
        # И "от 1от 2" -> "от 12"
        # (Паттерн выше покрывает это: \d - одна цифра).
        
        # 2. Исправление "от X до не более Y" (склейка числа и дроби)
        # "1 ⅓" -> "1⅓" (если это диапазон)
        # Или глобально заменить "(\d) ([¼½¾⅓⅔⅛⅜⅝⅞])" -> "\1\2"
        # Это безопасно для мер веса? "1 ½ фунта" -> "1½ фунта". Да, это лучше.
        # Но осторожно, если там "1 и ½".
        
        # Паттерн: цифра + пробел + дробь
        content = re.sub(r'(\d)\s+([¼½¾⅓⅔⅛⅜⅝⅞])', r'\1\2', content)
        
        # 3. Исправление "от 1 до 1½" (которое было "от 1 до 1 ½" - исправлено выше)
        
        # 4. Проверка "от 1 [от 5 до 30]" -> (как в логе было "от 1 [от 0 до 15]")
        # Если мы исправили "от 1от 0" -> "от 10", то фраза станет "от 10 до 15".
        # Но в логе было: "займет от 1от 0 до 15".
        # Значит, исправление "от 1от 0" -> "от 10" решит проблему целиком.
        
        # 5. Дополнительно: "от (\d) от (\d)" (с пробелом)
        content = re.sub(r'от\s+(\d)\s+от\s+(\d)', r'от \1\2', content)

        if content != original_content:
            count_fixed += 1
            # print(f"Fixed ranges in: {os.path.basename(filepath)}")
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
                
    print(f"Всего исправлено файлов с битыми диапазонами: {count_fixed}")

if __name__ == "__main__":
    fix_broken_ranges()
