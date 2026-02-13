import os
import re
from bs4 import BeautifulSoup, NavigableString

TEMP_DIR = "temp_epub_translate_openai"

def process_file(filepath):
    """
    Пост-обработка HTML файлов для улучшения диапазонов:
    1. Убираем курсив с 'от' и 'до', если они были добавлены случайно (<em>от</em>).
    2. Заменяем конструкцию 'от X до Y' на 'X–Y' (тире), особенно для цифр и дробей.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    changed = False

    # 1. Убираем курсив 'от' и 'до' (<em>от</em> -> от)
    for em in soup.find_all('em'):
        if em.get_text(strip=True).lower() in ['от', 'до']:
            em.replace_with(em.get_text())
            changed = True
            
    # 2. Регулярные выражения для замены текста в NavigableString
    # Паттерн: "от" (опционально) + пробел + число/дробь + пробел + "до" + пробел + число/дробь
    # Символы дробей: ¼½¾⅓⅔⅛
    # Числа: \d+([.,]\d+)?
    
    num_pattern = r'(?:\d+(?:[.,]\d+)?|[¼½¾⅓⅔⅛]|1[¼½¾⅓⅔⅛])' # Число или дробь (или "1 с чем-то")
    
    # Паттерн 1: "от X до Y" -> "X–Y"
    # (?i) - регистронезависимо
    # (?<!\w) - граница слова перед "от"
    range_regex = re.compile(r'(?i)(?<!\w)от\s+(' + num_pattern + r')\s+до\s+(' + num_pattern + r')')
    
    # Паттерн 2: "На от X до Y порций" -> "На X–Y порций" (уже покроется выше, но проверим)
    
    for text_node in soup.find_all(string=True):
        if not isinstance(text_node, NavigableString): continue
        if not text_node.parent or text_node.parent.name in ['script', 'style']: continue
        
        text = str(text_node)
        original_text = text
        
        # Исправление диапазонов
        # "от 1 до 2" -> "1–2"
        # "от ¼ до ½" -> "¼–½"
        matches = range_regex.findall(text)
        if matches:
            # Замена
            new_text = range_regex.sub(r'\1–\2', text)
            
            # Доп. чистка: если осталось "На 1–2", это ок.
            # Если было "с от 1 до 2", станет "с 1–2". Это идеально.
            
            if new_text != text:
                text_node.replace_with(new_text)
                changed = True

    if changed:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        print(f"  ✅ Исправлен: {os.path.basename(filepath)}")

def main():
    print(f"🧹 Запуск пост-обработки диапазонов в {TEMP_DIR}...")
    count = 0
    for root, dirs, files in os.walk(TEMP_DIR):
        for file in files:
            if file.endswith('.htm') or file.endswith('.html') or file.endswith('.xhtml'):
                process_file(os.path.join(root, file))
                count += 1
    print(f"🏁 Обработано {count} файлов.")

if __name__ == "__main__":
    main()
