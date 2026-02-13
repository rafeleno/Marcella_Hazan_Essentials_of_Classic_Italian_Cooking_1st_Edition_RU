import os
import re

TEMP_DIR = "temp_epub_final_1_0"

def fix_asterisks_v2():
    count_files_fixed = 0
    
    files_to_check = []
    for root, dirs, files in os.walk(TEMP_DIR):
        for file in files:
            if file.endswith('.htm') or file.endswith('.html'):
                files_to_check.append(os.path.join(root, file))
                
    for filepath in files_to_check:
        with open(filepath, 'r', encoding='utf-8') as f:
            headers = f.read() # Читаем как текст
            
        content = headers # rename variable
        original_content = content
        
        # 1. Убираем звездочки вокруг тегов <em>, <i>, <b>, <strong>, <span>
        # *<em> -> <em>
        content = re.sub(r'\*<', '<', content) # *<tag
        content = re.sub(r'>\*', '>', content) # tag>*
        
        # 2. Убираем звездочки внутри тегов, если они в начале/конце текста
        # <em>*текст*</em> -> <em>текст</em>
        # Но это сложно регуляркой по HTML.
        # Проще: найти `> *` (начало контента) и `* <` (конец контента).
        content = re.sub(r'>\s*\*+', '>', content) # <p>*Текст
        content = re.sub(r'\*+\s*<', '<', content) # Текст*</p>
        
        # 3. Убираем звездочки вокруг цифр (наиболее частый кейс с мерами)
        # *1 дюйм* -> 1 дюйм
        content = re.sub(r'\*(\d)', r'\1', content)
        content = re.sub(r'(\d|м|г|по|до)\*', r'\1', content) # 5*, см*, и т.д.
        
        # 4. Убираем двойные звездочки ** (markdown bold)
        content = content.replace('**', '')
        
        if content != original_content:
            count_files_fixed += 1
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
                
    print(f"Исправлено файлов: {count_files_fixed}")

if __name__ == "__main__":
    fix_asterisks_v2()
