import os
import re

TEMP_DIR = "temp_epub_final_1_0"

def find_ranges():
    # Паттерн: "от [число] до [не более] [число]"
    # Число = \d+ (целое), \d+[.,]\d+ (дробное), [¼½¾⅓⅔⅛⅜⅝⅞] (символ дроби)
    number_pattern = r'(?:\d+(?:[\.,]\d+)?|[¼½¾⅓⅔⅛⅜⅝⅞])'
    
    # Ищем: "от X до Y" или "от X до не более Y"
    # (?: ... ) - non-capturing group
    regex = r'(от\s+' + number_pattern + r'\s+до\s+(?:не\s+более\s+)?' + number_pattern + r')'
    
    files_to_check = []
    for root, dirs, files in os.walk(TEMP_DIR):
        for file in files:
            if file.endswith('.htm') or file.endswith('.html'):
                files_to_check.append(os.path.join(root, file))
                
    count_found = 0
    
    print("\n🔍 РЕЗУЛЬТАТЫ ПОИСКА:\n" + "="*50)
    
    for filepath in files_to_check:
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
            
        # Убираем HTML-теги для чистоты поиска контекста (грубо)
        # text_clean = re.sub(r'<[^>]+>', ' ', text) 
        # Но лучше искать в сыром, а потом чистить контекст
        
        # Находим все совпадения с итератором
        for match in re.finditer(regex, text, re.IGNORECASE):
            phrase = match.group(1)
            start, end = match.span()
            
            # Контекст: берем кусок вокруг
            # Чтобы взять слова, проще взять срез символов, а потом разбить split()
            
            context_start = max(0, start - 100)
            context_end = min(len(text), end + 100)
            
            pre_text = text[context_start:start]
            post_text = text[end:context_end]
            
            # Чистим от тегов внутри контекста (чтобы слова были словами)
            pre_words = re.sub(r'<[^>]+>', ' ', pre_text).split()
            post_words = re.sub(r'<[^>]+>', ' ', post_text).split()
            
            # Берем 3 последних "слова" до и 4 первых "слова" после
            pre_snippet = ' '.join(pre_words[-3:]) if pre_words else ""
            post_snippet = ' '.join(post_words[:4]) if post_words else ""
            
            print(f"📄 ... {pre_snippet} [{phrase}] {post_snippet} ...")
            # print(f"    (File: {os.path.basename(filepath)})")
            count_found += 1
            
    if count_found == 0:
        print("Ничего не найдено.")
    else:
        print("="*50 + f"\nВсего найдено: {count_found}")

if __name__ == "__main__":
    find_ranges()
