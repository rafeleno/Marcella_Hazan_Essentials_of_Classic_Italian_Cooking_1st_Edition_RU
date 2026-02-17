#!/usr/bin/env python3
import os
import json
import zipfile
import shutil
import time
from bs4 import BeautifulSoup, NavigableString, Tag
from openai import OpenAI
from dotenv import load_dotenv

# --- НАСТРОЙКИ ---
MODEL = "gpt-4o-mini"
INPUT_EPUB = "Marcella_Hazan_Essentials_of_Classic_Italian_Cooking_1st_Edition.epub"
OUTPUT_EPUB = "Hazan_RU_Final_0.3.epub"
TEMP_DIR = "temp_full_translate_v4" # Обновляем папку для чистоты
PROGRESS_FILE = "progress_v4.json"
ZAMETKI_FILE = "ZAMETKI_PO_PEREVODU.md"
BATCH_SIZE = 20  # Начинаем с 20, как вы и хотели

# Загрузка API ключа
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY)

def load_system_prompt():
    rules = ""
    if os.path.exists(ZAMETKI_FILE):
        with open(ZAMETKI_FILE, 'r', encoding='utf-8') as f:
            rules = f.read()
            
    return (
        "You are translating a classic Italian cookbook from English to Russian.\n"
        "STRICT GUIDELINES from the user:\n"
        f"{rules}\n\n"
        "CRITICAL INSTRUCTIONS:\n"
        "1.  **Oil -> 'Оливковое масло'** (ALWAYS, unless context implies butter).\n"
        "2.  **Butter -> 'Сливочное масло'** (ALWAYS).\n"
        "    - Example: 'Sauté in oil and butter' -> 'Пассеруйте в оливковом масле и сливочном масле'.\n"
        "3.  **Correct typos:** 'игееук' -> 'сливочное масло'.\n"
        "4.  **Format:** Receive JSON {id: html_string}, return JSON {id: translated_html_string}.\n"
        "5.  **Preserve HTML:** Do NOT translate tags (<b>, <i>, <span class='small'>), only text inside them.\n"
        "6.  **No Markdown:** Do NOT use ** or _ in output, use HTML tags <b>/<i> if needed.\n"
        "7.  **Tone:** Professional, respectful, warm (female author).\n"
    )

SYSTEM_PROMPT = load_system_prompt()

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r') as f: return json.load(f)
        except: pass
    return {"completed": []} # id -> True

def save_progress(p):
    with open(PROGRESS_FILE, 'w') as f: json.dump(p, f, indent=2)

def translate_batch_recursive(batch, attempt_count=0):
    """
    Рекурсивная функция перевода с логикой сплита.
    Если батч не переводится, разбиваем его на 2 части и пробуем их отдельно.
    """
    if not batch: return {}
    
    batch_json = json.dumps(batch, ensure_ascii=False)
    
    # 1. Попытка перевода текущего батча (3 попытки)
    for i in range(3):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": batch_json}
                ],
                temperature=0.3, # Низкая температура для точности
                response_format={"type": "json_object"}
            )
            data = json.loads(response.choices[0].message.content)
            
            # Проверка: вернулись ли все ключи
            # (не обязательно, но желательно)
            return data
            
        except Exception as e:
            err_msg = str(e)
            print(f"   ⚠️ Ошибка API (попытка {i+1}): {err_msg}")
            
            # Если ошибка контекста (слишком длинный промпт), сразу сплитим
            if "context_length_exceeded" in err_msg:
                break 
                
            time.sleep(2)
    
    # 2. Если не удалось перевести целиком -> СПЛИТ
    if len(batch) <= 1:
        print(f"   ❌ Не удалось перевести элемент {list(batch.keys())[0]} даже поштучно. Пропуск.")
        return {} # Возвращаем пустой результат для этого элемента (останется EN)

    print(f"   ✂️ Сплит батча ({len(batch)} -> {len(batch)//2} + {len(batch) - len(batch)//2})...")
    
    items = list(batch.items())
    mid = len(items) // 2
    part1 = dict(items[:mid])
    part2 = dict(items[mid:])
    
    res1 = translate_batch_recursive(part1)
    res2 = translate_batch_recursive(part2)
    
    # Объединяем результаты
    result = {}
    result.update(res1)
    result.update(res2)
    return result


def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    # Собираем переводимые элементы
    tags = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'td', 'div', 'span', 'figcaption'])
    
    elements_to_translate = []
    for tag in tags:
        if not tag.get_text(strip=True): continue
        if tag.name in ['div', 'span', 'td']:
            if tag.find(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li']): continue
        elements_to_translate.append(tag)

    if not elements_to_translate: return

    print(f"  Найдено {len(elements_to_translate)} блоков.")
    
    batch = {}
    indices = {} # id -> tag_reference
    
    # Используем count для ключей
    count = 0 
    
    for tag in elements_to_translate:
        key = str(count)
        batch[key] = str(tag) 
        indices[key] = tag
        count += 1
        
        if len(batch) >= BATCH_SIZE:
            print(f"  Перевод батча ({len(batch)} элементов)...")
            translations = translate_batch_recursive(batch)
            
            # Применение переводов
            for k, val in translations.items():
                if k in indices and val:
                    try:
                        new_tag = BeautifulSoup(val, 'html.parser').find()
                        if new_tag: indices[k].replace_with(new_tag)
                    except: pass
            
            batch = {}
            indices = {}

    # Остаток
    if batch:
        print(f"  Перевод остатка ({len(batch)} элементов)...")
        translations = translate_batch_recursive(batch)
        for k, val in translations.items():
            if k in indices and val:
                try:
                    new_tag = BeautifulSoup(val, 'html.parser').find()
                    if new_tag: indices[k].replace_with(new_tag)
                except: pass

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(str(soup))

def main():
    print(f"🚀 СТАРТ ПОЛНОГО ПЕРЕВОДА v4 (SPLIT LOGIC) -> {OUTPUT_EPUB}")
    
    if os.path.exists(TEMP_DIR):
        print("📂 Использую существующую временную папку (продолжение)")
    else:
        print("📦 Распаковка оригинала...")
        with zipfile.ZipFile(INPUT_EPUB, 'r') as z: z.extractall(TEMP_DIR)

    # Чистка CSS
    for root, _, files in os.walk(TEMP_DIR):
        for f in files:
            if f.endswith('.css'):
                p = os.path.join(root, f)
                with open(p, 'a') as cf: cf.write("\na { color: #3795c4 !important; text-decoration: none; }\n")

    progress = load_progress()
    files = []
    for root, _, fs in os.walk(TEMP_DIR):
        for f in fs:
            if f.endswith(('.html', '.htm', '.xhtml')): files.append(os.path.join(root, f))
    files.sort()
    
    print(f"📂 Всего файлов: {len(files)}")
    
    for i, fp in enumerate(files):
        fname = os.path.basename(fp)
        if fname in progress['completed']:
            print(f"⏭️  [{i+1}/{len(files)}] {fname} готов")
            continue
            
        print(f"🔄 [{i+1}/{len(files)}] Перевод {fname}...")
        try:
            process_file(fp)
            progress['completed'].append(fname)
            save_progress(progress)
        except Exception as e:
            print(f"❌ Ошибка {fname}: {e}")

    # Упаковка
    print(f"📦 Сборка {OUTPUT_EPUB}...")
    if os.path.exists(OUTPUT_EPUB): os.remove(OUTPUT_EPUB)
    
    cwd = os.getcwd()
    os.chdir(TEMP_DIR)
    os.system(f"zip -0 -X ../{OUTPUT_EPUB} mimetype")
    os.system(f"zip -r -q ../{OUTPUT_EPUB} META-INF OEBPS -x '*.DS_Store'")
    if os.path.exists("Haza_9780307958303_epub_opf_r1.opf"): 
        os.system(f"zip -r -q ../{OUTPUT_EPUB} *.opf *.ncx")
    os.chdir(cwd)
    
    print("🏁 ГОТОВО! Можете закрывать.")

if __name__ == "__main__":
    main()
