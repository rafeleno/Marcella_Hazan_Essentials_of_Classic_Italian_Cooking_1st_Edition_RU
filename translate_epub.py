import zipfile
import os
import shutil
import time
import re
import json
from bs4 import BeautifulSoup, NavigableString, Tag
from deep_translator import GoogleTranslator

# --- НАСТРОЙКИ ---
INPUT_FILE = 'Marcella_Hazan_Essentials_of_Classic_Italian_Cooking_1st_Edition.epub'
OUTPUT_FILE = 'Hazan_RU_Translated_v3.epub'
TEMP_DIR = 'temp_epub_translate_v3'
PROGRESS_FILE = 'translation_progress_v3.json'

SAVE_EVERY_N = 10
API_DELAY = 1.0  # Увеличил задержку для надежности

translator = GoogleTranslator(source='en', target='ru')


def load_progress() -> dict:
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {"completed_files": [], "current_file": None, "current_index": 0}


def save_progress(progress: dict):
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def post_process_terms(text: str) -> str:
    """Заменяет английские термины и меры веса на русские с метрикой"""
    # Словарь замен (регулярные выражения -> замена)
    replacements = [
        (r'\b1\s*pound\b', '1 фунт (~450 г)'),
        (r'\b2\s*pounds\b', '2 фунта (~900 г)'),
        (r'\b(\d+)\s*pounds\b', r'\1 фунтов'),
        (r'\b1\s*cup\b', '1 чашка (~240 мл)'),
        (r'\b(\d+)\s*cups\b', r'\1 чашек'),
        (r'\b1\s*tablespoon\b', '1 ст. л.'),
        (r'\b(\d+)\s*tablespoons\b', r'\1 ст. л.'),
        (r'\b1\s*teaspoon\b', '1 ч. л.'),
        (r'\b(\d+)\s*teaspoons\b', r'\1 ч. л.'),
        (r'(?i)battuto', 'баттуто'),
        (r'(?i)soffritto', 'соффритто'),
        (r'(?i)insaporire', 'инсапорире'),
        (r'(?i)al dente', 'аль денте'),
    ]
    
    result = text
    for pattern, repl in replacements:
        result = re.sub(pattern, repl, result, flags=re.IGNORECASE)
    return result

def translate_text(text: str, retry_count: int = 3) -> str:
    """Переводит текст через Google Translate, сохраняя пробелы и термины"""
    if not text or not text.strip():
        return text
    
    # Сохраняем начальные и конечные пробелы
    leading_space = ""
    trailing_space = ""
    
    match_start = re.match(r'^(\s+)', text)
    if match_start:
        leading_space = match_start.group(1)
    
    match_end = re.search(r'(\s+)$', text)
    if match_end:
        trailing_space = match_end.group(1)
    
    clean = text.strip()
    if len(clean) < 2: # Переводим даже короткие слова (от 2 букв)
        return text
    
    # Пропускаем если только спецсимволы/цифры
    if re.match(r'^[\s\d\W]*$', clean):
        return text

    for attempt in range(retry_count):
        try:
            result = translator.translate(clean)  # Переводим без пробелов
            if result:
                # Пост-обработка терминов
                final_text = post_process_terms(result)
                # Возвращаем с сохранёнными пробелами
                return leading_space + final_text + trailing_space
        except Exception as e:
            if attempt < retry_count - 1:
                time.sleep(2 ** attempt)
    
    return text


def translate_element_recursive(element):
    """
    Рекурсивно обходит элемент и переводит только текстовые узлы,
    сохраняя все теги (span, em, a, strong, etc.) на своих местах.
    Возвращает True, если был сделан хоть один перевод.
    """
    translated_any = False
    
    # Если это текстовый узел - переводим
    if isinstance(element, NavigableString) and not isinstance(element, Tag):
        original = str(element)
        # Пропускаем, если только пробелы/цифры/спецсимволы
        if not re.match(r'^[\s\d\W]*$', original.strip()) and len(original.strip()) >= 2:
            translated = translate_text(original)
            if translated and translated != original:
                element.replace_with(NavigableString(translated))
                translated_any = True
                time.sleep(API_DELAY * 0.2) # Небольшая пауза
        return translated_any

    # Если это тег - идем вглубь (рекурсия)
    if hasattr(element, 'contents'):
        # Копируем список детей, так как он может меняться при замене текста
        for child in list(element.contents):
            if translate_element_recursive(child):
                translated_any = True
    
    return translated_any

def translate_text_nodes_in_element(element):
    """Обертка для рекурсивной функции"""
    return translate_element_recursive(element)


def colorize_intro_before_images(soup):
    """
    Находит текст/теги перед картинками (вступительные слова) 
    и красит их в оранжевый (color_CA4E00), если они еще не покрашены.
    """
    # Оранжевый цвет из книги
    ORANGE_CLASS = "color_CA4E00"
    
    for img in soup.find_all('img'):
        # Ищем элемент прямо перед картинкой
        prev = img.previous_sibling
        
        # Пропускаем пустые пробелы, но запоминаем их, чтобы не потерять
        while isinstance(prev, NavigableString) and not prev.strip():
            prev = prev.previous_sibling
            
        if not prev:
            continue

        # Если это текст или тег (em, strong, b, i)
        if isinstance(prev, NavigableString) or (isinstance(prev, Tag) and prev.name in ['em', 'strong', 'b', 'i', 'span']):
            
            # Проверяем, не покрашен ли он уже (или его родитель)
            is_colored = False
            
            # Проверка самого элемента (если тег)
            if isinstance(prev, Tag) and prev.get('class') and ORANGE_CLASS in prev.get('class'):
                is_colored = True
            
            # Проверка родителя (не лежит ли он уже внутри color_CA4E00)
            if not is_colored and prev.parent and prev.parent.get('class') and ORANGE_CLASS in prev.parent.get('class'):
                is_colored = True
                
            # Если не покрашен - красим!
            if not is_colored:
                # Создаем спан с цветом
                new_span = soup.new_tag("span", attrs={"class": ORANGE_CLASS})
                
                # Заменяем элемент на спан, а элемент кладем внутрь
                prev.replace_with(new_span)
                new_span.append(prev)
                # print(f"  🎨 Окрашен элемент перед картинкой: {prev}")


def translate_html_file(filepath: str, file_num: int, total_files: int, progress: dict) -> bool:
    """Переводит HTML файл, сохраняя форматирование"""
    filename = os.path.basename(filepath)
    print(f"\n[{file_num}/{total_files}] {filename}")
    
    if filename in progress["completed_files"]:
        print(f"  ⏭️  Пропуск (уже переведён)")
        return True
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            with open(filepath, 'r', encoding='latin-1') as f:
                content = f.read()
        except Exception as e:
            print(f"  [!] Ошибка чтения: {e}")
            return False
    
    soup = BeautifulSoup(content, 'lxml')
    
    # Находим элементы для перевода
    text_elements = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'td', 'th', 'figcaption', 'title'])
    
    if not text_elements:
        print(f"  Пропуск (нет текста)")
        progress["completed_files"].append(filename)
        save_progress(progress)
        return False
    
    print(f"  Найдено {len(text_elements)} элементов")
    
    start_index = 0
    if progress["current_file"] == filename:
        start_index = progress["current_index"]
        print(f"  ↪️  Продолжение с элемента {start_index}")
    
    progress["current_file"] = filename
    translated_count = 0
    
    for i, element in enumerate(text_elements):
        if i < start_index:
            continue
        
        if (i + 1) % 20 == 0 or i == start_index:
            print(f"  📝 Элемент {i + 1}/{len(text_elements)}...")
        
        # Переводим текстовые узлы ВНУТРИ элемента, сохраняя структуру
        if translate_text_nodes_in_element(element):
            translated_count += 1
        
        # Промежуточное сохранение
        if (i + 1) % SAVE_EVERY_N == 0:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(str(soup))
            progress["current_index"] = i + 1
            save_progress(progress)
        
        time.sleep(API_DELAY)
    
    # Финальное сохранение
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    
    progress["completed_files"].append(filename)
    progress["current_file"] = None
    progress["current_index"] = 0
    save_progress(progress)
    
    print(f"  ✅ Переведено {translated_count} элементов")
    return True


def create_epub(output_name: str):
    if os.path.exists(output_name):
        os.remove(output_name)
    
    with zipfile.ZipFile(output_name, 'w', zipfile.ZIP_DEFLATED) as z:
        mimetype_path = os.path.join(TEMP_DIR, 'mimetype')
        if os.path.exists(mimetype_path):
            z.write(mimetype_path, 'mimetype', compress_type=zipfile.ZIP_STORED)
        
        for root, dirs, files in os.walk(TEMP_DIR):
            for file in files:
                if file == 'mimetype':
                    continue
                filepath = os.path.join(root, file)
                arcname = os.path.relpath(filepath, TEMP_DIR)
                z.write(filepath, arcname)
    
    print(f"  ✓ Создан: {output_name}")


def main():
    print("=" * 60)
    print("ПЕРЕВОД EPUB С СОХРАНЕНИЕМ ФОРМАТИРОВАНИЯ")
    print("=" * 60)
    
    progress = load_progress()
    
    need_extract = True
    if os.path.exists(TEMP_DIR) and (progress["completed_files"] or progress["current_file"]):
        print(f"\n🔄 Найден прогресс!")
        print(f"   Готово файлов: {len(progress['completed_files'])}")
        if progress["current_file"]:
            print(f"   Текущий: {progress['current_file']}, элемент {progress['current_index']}")
        need_extract = False
    
    if need_extract:
        if os.path.exists(TEMP_DIR):
            shutil.rmtree(TEMP_DIR)
        os.makedirs(TEMP_DIR)
        
        print(f"\n📦 Распаковка {INPUT_FILE}...")
        try:
            with zipfile.ZipFile(INPUT_FILE, 'r') as z:
                z.extractall(TEMP_DIR)
            print("  ✓ OK")
        except FileNotFoundError:
            print(f"  ✗ Файл не найден!")
            return
        
        progress = {"completed_files": [], "current_file": None, "current_index": 0}
        save_progress(progress)
    
    html_files = []
    for root, dirs, files in os.walk(TEMP_DIR):
        for file in files:
            if file.endswith(('.html', '.xhtml', '.htm')):
                html_files.append(os.path.join(root, file))
    html_files.sort()
    
    remaining = len(html_files) - len(progress["completed_files"])
    print(f"\n📄 Всего: {len(html_files)} | Осталось: {remaining}")
    print(f"\n🔄 Перевод (с сохранением стилей)...")
    print("💡 Ctrl+C для паузы. Запусти снова для продолжения.\n")
    
    translated_files = 0
    start_time = time.time()
    
    for i, filepath in enumerate(html_files, 1):
        if translate_html_file(filepath, i, len(html_files), progress):
            translated_files += 1
    
    elapsed = time.time() - start_time
    print(f"\n✓ Переведено: {translated_files}/{len(html_files)}")
    print(f"⏱️  Время: {elapsed/60:.1f} мин")
    
    print(f"\n📦 Финальная сборка...")
    create_epub(OUTPUT_FILE)
    
    shutil.rmtree(TEMP_DIR)
    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)
    
    print("\n" + "=" * 60)
    print(f"🎉 ГОТОВО! {OUTPUT_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()
