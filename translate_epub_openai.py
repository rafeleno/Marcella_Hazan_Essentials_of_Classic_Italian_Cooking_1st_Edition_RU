import os
import json
import zipfile
import shutil
import time
from bs4 import BeautifulSoup, NavigableString, Tag
from openai import OpenAI
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    raise ValueError("Не найден OPENAI_API_KEY в .env файле!")

# --- КОНФИГУРАЦИЯ ---
MODEL = "gpt-4o-mini"
INPUT_EPUB = "Marcella_Hazan_Essentials_of_Classic_Italian_Cooking_1st_Edition.epub"
OUTPUT_EPUB = "Hazan_RU_Final_1.0.epub"
TEMP_DIR = "temp_epub_final_1_0"
PROGRESS_FILE = "progress_final_1_0.json"
ZAMETKI_FILE = "ZAMETKI_PO_PEREVODU.md"

BATCH_SIZE_TAGS = 15  # Количество тегов в одном запросе к API

client = OpenAI(api_key=API_KEY)

def load_system_prompt():
    """Читает файл с заметками и формирует строгий системный промпт"""
    content = ""
    if os.path.exists(ZAMETKI_FILE):
        with open(ZAMETKI_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
    
    return (
        "You are a professional translator translating a classic Italian cookbook from English to Russian.\n"
        "Here are the guidelines you MUST follow:\n\n"
        f"{content}\n\n"
        "CRITICAL INSTRUCTIONS:\n"
        "1. You will receive a JSON object where keys are IDs and values are HTML strings.\n"
        "2. Translate the TEXT CONTENT of each value to Russian.\n"
        "3. DO NOT translate HTML tags, attributes, classes, or filenames.\n"
        "4. KEEP ALL HTML STRUCTURE EXACTLY AS IS.\n"
        "5. Example Input: {'1': '<p><b>Hello</b> world</p>'}\n"
        "6. Example Output: {'1': '<p><b>Привет,</b> мир</p>'}\n"
        "7. Return ONLY a valid JSON object with the same keys."
    )

SYSTEM_PROMPT = load_system_prompt()

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {"completed_files": []}

def save_progress(progress):
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

# Не используется в актуальном пайплайне
def colorize_intro_before_images(soup):
    """Красит вступительные слова перед картинками в оранжевый"""
    ORANGE_CLASS = "color_CA4E00"
    for img in soup.find_all('img'):
        prev = img.previous_sibling
        # Пропуск пробелов
        while isinstance(prev, NavigableString) and not str(prev).strip():
            prev = prev.previous_sibling
            
        if not prev:
            continue

        # Проверка и окрашивание
        if isinstance(prev, NavigableString) or (isinstance(prev, Tag) and prev.name in ['em', 'strong', 'b', 'i', 'span']):
            is_colored = False
            # Проверка самого элемента
            if isinstance(prev, Tag) and prev.get('class') and ORANGE_CLASS in prev.get('class'):
                is_colored = True
            # Проверка родителя
            if not is_colored and prev.parent and prev.parent.get('class') and ORANGE_CLASS in prev.parent.get('class'):
                is_colored = True
                
            if not is_colored:
                new_span = soup.new_tag("span", attrs={"class": ORANGE_CLASS})
                prev.replace_with(new_span)
                new_span.append(prev)

import re

def update_css(temp_dir):
    """Обновляет CSS файлы: меняет цвет ссылок на #93dafe"""
    for root, dirs, files in os.walk(temp_dir):
        for file in files:
            if file.endswith('.css'):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        css_content = f.read()
                    
                    # Замена цвета ссылок (или добавление правила)
                    # Если есть a { color: ... }, меняем. Если нет — добавляем.
                    if 'a {' in css_content or 'a:' in css_content or '.hlink' in css_content:
                        # Простая замена всех синих цветов? Нет, опасно.
                        # Добавим в конец файла принудительное правило
                        css_content += "\n\na, a:link, a:visited, .hlink { color: #3795c4 !important; text-decoration: none; }\n"
                    else:
                        css_content += "\n\na { color: #3795c4 !important; }\n"
                        
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(css_content)
                    print(f"  🎨 CSS обновлен: {file}")
                except Exception as e:
                    print(f"Ошибка обновления CSS {file}: {e}")

def clean_up_html_content(soup):
    """
    Пост-обработка HTML:
    1. Исправление Markdown курсива
    2. Умное исправление Small Caps (только если это часть слова в начале)
    3. Исправление диапазонов (1 до 2 -> от 1 до 2)
    """
    # 1. Исправление Markdown курсива и диапазонов
    for text_node in soup.find_all(string=True):
        if not isinstance(text_node, NavigableString): continue
        
        text = str(text_node)
        original_text = text
        
        # Markdown
        if '_' in text or '*' in text:
            text = re.sub(r'(?<!\w)_([^\s_][^_]*[^\s_])_(?!\w)', r'<em>\1</em>', text)
            text = re.sub(r'(?<!\w)\*([^\s\*][^\*]*[^\s\*])\*(?!\w)', r'<em>\1</em>', text)
            
        # Диапазоны (1 до 2 -> от 1 до 2; ¼ до ½ -> от ¼ до ½)
        # Ищем цифру или дробь, пробел, "до", пробел, цифру или дробь.
        # (?<!от\s) - чтобы не дублировать "от"
        # Символы дробей и цифры: [\d¼½¾⅓⅔⅛.,]+
        text = re.sub(r'(?<!от\s)([\d¼½¾⅓⅔⅛.,/]+)\s+до\s+([\d¼½¾⅓⅔⅛.,/]+(?!\s+градус))', r'от \1 до \2', text, flags=re.IGNORECASE)
        
        # Если текст изменился, обновляем ноду
        if text != original_text:
            try:
                # Если появились теги <em>, надо парсить
                if '<em>' in text:
                    new_tag = BeautifulSoup(f"<span>{text}</span>", 'html.parser')
                    text_node.replace_with(new_tag)
                    new_tag.unwrap()
                else:
                    text_node.replace_with(text)
            except:
                pass

    # 2. Умное исправление Small Caps - ОТКЛЮЧЕНО ПО ЗАПРОСУ ПОЛЬЗОВАТЕЛЯ
    # Оставляем как есть (будет переведен только текст внутри span)
    pass

def translate_batch(batch_dict):
    """Отправляет словарь {id: html} в OpenAI и возвращает переведенный словарь"""
    if not batch_dict:
        return {}
        
    try:
        json_input = json.dumps(batch_dict, ensure_ascii=False)
        
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json_input}
            ],
            temperature=0.3, # Низкая температура для точности
            response_format={"type": "json_object"}
        )
        
        result_json = response.choices[0].message.content
        return json.loads(result_json)
        
    except Exception as e:
        print(f"  ❌ Ошибка API: {e}")
        time.sleep(2) 
        return {}

def process_file(filepath):
    """Обрабатывает один HTML файл"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    
    # 1. Сбор элементов для перевода
    target_tags = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'div', 'span', 'td', 'th']
    elements = []
    
    for tag in soup.find_all(target_tags):
        if tag.get_text(strip=True):
            if tag.name in ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li']:
                elements.append(tag)
            elif tag.name in ['div', 'span', 'td', 'th']:
                parent_names = [p.name for p in tag.parents]
                if not any(pn in ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'] for pn in parent_names):
                     elements.append(tag)

    if not elements:
        print(f"  В файле нет текста для перевода.")
        return

    print(f"  Найдено {len(elements)} блоков.")
    
    # 3. Батчинг и перевод
    current_batch = {}
    batch_indices = [] 
    
    for i, elem in enumerate(elements):
        elem_html = str(elem) 
        current_batch[str(i)] = elem_html
        batch_indices.append(i)
        
        if len(current_batch) >= BATCH_SIZE_TAGS:
            print(f"  Перевод батча (элементы {i-len(current_batch)+1}-{i})...")
            translations = translate_batch(current_batch)
            
            for key_idx_str, html_val in translations.items():
                if key_idx_str in current_batch:
                    original_elem = elements[int(key_idx_str)]
                    
                    # Парсим полученный HTML
                    new_soup = BeautifulSoup(html_val, 'html.parser')
                    
                    # --- ПОСТ-ОБРАБОТКА (ИСПРАВЛЕНИЯ) ---
                    clean_up_html_content(new_soup)
                    # ------------------------------------
                    
                    new_tag = None
                    if new_soup.body:
                        new_tag = new_soup.body.find(recursive=False) 
                    elif new_soup.contents:
                        for content in new_soup.contents:
                            if isinstance(content, Tag):
                                new_tag = content
                                break
                    
                    if new_tag:
                        original_elem.replace_with(new_tag)
            
            current_batch = {}
            batch_indices = []
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(str(soup))
            
    if current_batch:
        print(f"  Перевод последнего батча ({len(current_batch)} шт)...")
        translations = translate_batch(current_batch)
        for key_idx_str, html_val in translations.items():
            if key_idx_str in current_batch:
                 original_elem = elements[int(key_idx_str)]
                 new_soup = BeautifulSoup(html_val, 'html.parser')
                 
                 # --- ПОСТ-ОБРАБОТКА ---
                 clean_up_html_content(new_soup)
                 # ----------------------

                 new_tag = None
                 if new_soup.body:
                     new_tag = new_soup.body.find(recursive=False)
                 elif new_soup.contents:
                     for content in new_soup.contents:
                        if isinstance(content, Tag):
                             new_tag = content
                             break
                 if new_tag:
                     original_elem.replace_with(new_tag)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(str(soup))


def main():
    print("=== ЗАПУСК OPENAI ПЕРЕВОДА (GPT-4o mini) ===")
    
    # 1. Распаковка (если нужно)
    if not os.path.exists(TEMP_DIR):
        print(f"Распаковка {INPUT_EPUB}...")
        with zipfile.ZipFile(INPUT_EPUB, 'r') as epub:
            epub.extractall(TEMP_DIR)
            
    # Обновляем CSS (даже если распаковка уже была)
    update_css(TEMP_DIR)
    
    progress = load_progress()
    
    # 2. Поиск файлов
    html_files = []
    for root, dirs, files in os.walk(TEMP_DIR):
        for file in files:
            if file.endswith('.htm') or file.endswith('.html') or file.endswith('.xhtml'):
                html_files.append(os.path.join(root, file))
    html_files.sort()
    
    total_files = len(html_files)
    
    # 3. Перевод файлов
    for idx, filepath in enumerate(html_files):
        filename = os.path.basename(filepath)
        
        if filename in progress['completed_files']:
            print(f"[{idx+1}/{total_files}] {filename} - УЖЕ ГОТОВ")
            continue
            
        print(f"[{idx+1}/{total_files}] {filename} - ОБРАБОТКА...")
        try:
            process_file(filepath)
            
            # Сохраняем прогресс сразу после файла
            progress['completed_files'].append(filename)
            save_progress(progress)
            
        except KeyboardInterrupt:
            print("\n🛑 Прервано пользователем")
            return
        except Exception as e:
            print(f"\n❌ Критическая ошибка в файле {filename}: {e}")
            # Не прерываем весь процесс, пробуем следующий файл?
            # Лучше остановиться, чтобы не портить книгу.
            # return

    # 4. Сборка EPUB
    print("\n📦 Сборка финального EPUB...")
    if os.path.exists(OUTPUT_EPUB):
        os.remove(OUTPUT_EPUB)
        
    with zipfile.ZipFile(OUTPUT_EPUB, 'w', zipfile.ZIP_DEFLATED) as epub:
        # Mimetype первым, без сжатия
        epub.write(os.path.join(TEMP_DIR, 'mimetype'), 'mimetype', compress_type=zipfile.ZIP_STORED)
        
        # Остальные файлы
        for root, dirs, files in os.walk(TEMP_DIR):
            for file in files:
                if file == 'mimetype': continue
                # Исключаем лишние системные файлы мака
                if file.startswith('.'): continue
                
                path = os.path.join(root, file)
                arcname = os.path.relpath(path, TEMP_DIR)
                epub.write(path, arcname)
                
    print(f"✅ УСПЕШНО! Файл сохранен как: {OUTPUT_EPUB}")

if __name__ == "__main__":
    main()
