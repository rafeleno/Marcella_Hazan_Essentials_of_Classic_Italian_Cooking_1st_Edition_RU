import os
import re

TEMP_DIR = "temp_epub_final_1_0"

def remove_all_asterisks():
    count_files_fixed = 0
    total_removed = 0
    
    files_to_check = []
    for root, dirs, files in os.walk(TEMP_DIR):
        for file in files:
            if file.endswith('.htm') or file.endswith('.html'):
                files_to_check.append(os.path.join(root, file))
                
    for filepath in files_to_check:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        original_content = content
        
        # Удаляем все звездочки глобально
        # Исключаем, на всякий случай, комментарии (<!-- ... -->)? Нет, в них тоже можно чистить.
        # Исключаем CSS-селекторы? В *.htm файлах стили бывают редко (обычно в CSS файлах).
        # Но если есть <style> * { ... } </style>?
        # Лучше не удалять звездочку, если за ней пробел и {
        # Но в книге выше вы видели примеры "*⅓", "½*". Там нет пробелов и фигур.
        
        # Просто global replace char '*' -> ''
        # Но учитываем, что мб нужно оставить CSS universal selector?
        # Вряд ли в книге CSS внутри HTML.
        
        content = content.replace('*', '')
        
        if content != original_content:
            diff = len(original_content) - len(content)
            count_files_fixed += 1
            total_removed += diff
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
                
    print(f"Всего исправлено файлов: {count_files_fixed}")
    print(f"Всего удалено звездочек: {total_removed}")

if __name__ == "__main__":
    remove_all_asterisks()
