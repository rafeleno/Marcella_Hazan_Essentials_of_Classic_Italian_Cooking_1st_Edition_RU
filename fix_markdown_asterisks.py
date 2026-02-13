import os
import re

TEMP_DIR = "temp_epub_final_1_0"

def fix_asterisks_in_files():
    count_files_fixed = 0
    total_asterisks_fixed = 0
    
    # 1. Сначала ищем *word* - это стандартный Markdown курсив
    #    В HTML это часто становится *1 дюйма (2.5 см)*
    #    Но мы не трогаем CSS-селекторы (типа * {})
    #    Поэтому ищем \*([^*<>\n]+)\* (без тегов и переносов строк внутри)
    
    pattern = re.compile(r'\*([^*<>\n]+?)\*')
    
    files_to_check = []
    for root, dirs, files in os.walk(TEMP_DIR):
        for file in files:
            if file.endswith('.htm') or file.endswith('.html'):
                files_to_check.append(os.path.join(root, file))
                
    for filepath in files_to_check:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        matches = pattern.findall(content)
        if matches:
            # Делаем замену
            new_content = pattern.sub(r'\1', content)
            
            if new_content != content:
                # Фильтруем случаи типа CSS hack *width
                # Но вряд ли в книге такое есть.
                
                count_files_fixed += 1
                total_asterisks_fixed += len(matches)
                # print(f"Fixed {len(matches)} asterisks in: {os.path.basename(filepath)}")
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
    
    print(f"Всего исправлено файлов: {count_files_fixed}")
    print(f"Всего удалено лишних звездочек: {total_asterisks_fixed}")

if __name__ == "__main__":
    fix_asterisks_in_files()
