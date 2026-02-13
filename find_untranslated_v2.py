import os
import re
import json
import time
from bs4 import BeautifulSoup, Tag
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY)

TEMP_DIR = "temp_epub_final_1_0"
MODEL = "gpt-4o-mini"
BATCH_SIZE = 20 # По запросу

SYSTEM_PROMPT = """
You are a professional translator translating a classic Italian cookbook from English to Russian.
Your task is to translate the provided text blocks from English to Russian.

RULES:
1. Translate contextually and accurately.
2. Use strict culinary terminology:
   - "Sauté" -> "Пассеровать" (vegetables) or "Обжаривать" (meat).
   - "Simmer" -> "Томить" or "Варить на медленном огне".
   - "Braise" -> "Тушить".
   - "Deglaze" -> "Деглазировать".
3. Metric Conversion:
   - "1 pound" -> "1 фунт (450 г)".
   - "1 inch" -> "1 дюйм (2.5 см)".
   - Ranges: Use em-dash "1–2" (not "1 to 2").
4. Keep HTML tags exactly as they are.
5. Return JSON with translations.
"""

def is_english(text):
    if not text: return False
    text = text.strip()
    latin = len(re.findall(r'[a-zA-Z]', text))
    cyrillic = len(re.findall(r'[а-яА-ЯёЁ]', text))
    if latin > 0 and cyrillic == 0: return True
    if latin > 10 and latin > cyrillic * 5: return True 
    return False

def translate_batch(batch, batch_label=""):
    if not batch: return {}
    size = len(batch)
    
    # Fail Fast Strategy
    if size > 5:
        max_retries = 1
        retry_delay = 0 
    else:
        max_retries = 3
        retry_delay = 3

    for attempt in range(max_retries):
        try:
            if size > 5:
                print(f"    ⚡️ Проба ({size} эл.)...")
            else:
                print(f"    ⏳ Попытка {attempt + 1}/{max_retries} ({size} эл.)...")
            
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": json.dumps(batch, ensure_ascii=False)}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            if not content: raise Exception("Empty response")
            return json.loads(content)
            
        except Exception as e:
            print(f"    ❌ Ошибка: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)

    # Split Logic
    if size > 1:
        mid = size // 2
        print(f"    🔪 Разделение ({size} -> {mid} + {size-mid})...")
        keys = list(batch.keys())
        part1 = {k: batch[k] for k in keys[:mid]}
        part2 = {k: batch[k] for k in keys[mid:]}
        
        res1 = translate_batch(part1, f"{batch_label}.1")
        res2 = translate_batch(part2, f"{batch_label}.2")
        
        result = {}
        result.update(res1)
        result.update(res2)
        return result
    else:
        key = list(batch.keys())[0]
        print(f"    💀 Элемент {key} НЕ ПЕРЕВЕДЕН.")
        return {}

def process_file(filepath):
    """Обрабатывает один файл: находит, переводит батчами, СОХРАНЯЕТ."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
    except Exception as e:
        print(f"Ошибка чтения {filepath}: {e}")
        return

    # Находим блоки
    found_tags = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'div', 'span'])
    candidates = [] # (index, tag)
    
    for i, tag in enumerate(found_tags):
        if tag.find(['p', 'div', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']): continue
        text = tag.get_text(strip=True)
        if not text or len(text) < 2: continue
        if text.isdigit(): continue
        
        if is_english(text):
            candidates.append((i, tag))
            
    if not candidates:
        return # Нет работы

    print(f"\n📄 Файл: {os.path.basename(filepath)} ({len(candidates)} блоков)")
    
    # Разбиваем на батчи по BATCH_SIZE
    file_translations = {}
    
    for start_idx in range(0, len(candidates), BATCH_SIZE):
        chunk = candidates[start_idx : start_idx + BATCH_SIZE]
        batch_data = {}
        
        for (i, tag) in chunk:
            uid = f"idx_{i}"
            batch_data[uid] = str(tag)
            
        print(f"  🚀 Батч {start_idx // BATCH_SIZE + 1} (элементы {start_idx}-{start_idx+len(chunk)})...")
        translations = translate_batch(batch_data)
        file_translations.update(translations)
        
        # МОЖНО СОХРАНЯТЬ ПОСЛЕ КАЖДОГО БАТЧА (для супер-надежности)
        # Но тогда надо перезагружать soup каждый раз? Или менять soup в памяти и сохранять.
        # Меняем soup в памяти:
        for (i, tag) in chunk:
            uid = f"idx_{i}"
            if uid in translations:
                new_html = translations[uid]
                temp_soup = BeautifulSoup(new_html, 'html.parser')
                real_new_tag = temp_soup.find(recursive=False) or temp_soup
                if real_new_tag:
                    tag.replace_with(real_new_tag)
        
        # Сохраняем файл ПОСЛЕ КАЖДОГО БАТЧА
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        print(f"  💾 Прогресс сохранен в {os.path.basename(filepath)}")

def main():
    files_to_check = []
    for root, dirs, files in os.walk(TEMP_DIR):
        for file in files:
            if file.endswith('.htm') or file.endswith('.html'):
                files_to_check.append(os.path.join(root, file))
                
    files_to_check.sort() # Для порядка
    
    print(f"Найдено {len(files_to_check)} файлов для проверки.")
    
    for fp in files_to_check:
        process_file(fp)

if __name__ == "__main__":
    main()
