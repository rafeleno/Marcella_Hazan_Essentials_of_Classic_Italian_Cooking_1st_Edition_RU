import os
import re
import json
import time
from bs4 import BeautifulSoup, NavigableString, Tag
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY)

TEMP_DIR = "temp_epub_final_1_0"
MODEL = "gpt-4o-mini"
# MODEL = "gpt-4o" # Если нужно лучшее качество, но дороже

# Обновленный промпт для перевода любых текстовых блоков
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
    """Проверяет, содержит ли текст английские буквы и мало кириллицы"""
    if not text: return False
    text = text.strip()
    latin = len(re.findall(r'[a-zA-Z]', text))
    cyrillic = len(re.findall(r'[а-яА-ЯёЁ]', text))
    
    if latin > 0 and cyrillic == 0: return True
    if latin > 10 and latin > cyrillic * 5: return True # Преимущественно английский
    return False

def translate_batch(batch, batch_index=0):
    if not batch: return {}
    size = len(batch)
    
    # СТРАТЕГИЯ "FAIL FAST":
    # Если батч большой (> 5), пробуем 1 раз и сразу делим при ошибке.
    # Если батч маленький (<= 5), пробуем 3 раза (упорствуем).
    if size > 5:
        max_retries = 1
        retry_delay = 0 
    else:
        max_retries = 3
        retry_delay = 3

    for attempt in range(max_retries):
        try:
            if size > 5:
                print(f"  ⚡️ Проба батча #{batch_index} ({size} эл.)...")
            else:
                print(f"  ⏳ Перевод батча #{batch_index} ({size} эл.) - Попытка {attempt + 1}/{max_retries}...")
            
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
            if not content:
                 raise Exception("Empty response")
            return json.loads(content)
            
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            # Если последняя попытка провалилась - выходим из цикла и идем в Split
            
    # Если мы здесь, значит все попытки провалились.
    # SPLIT LOGIC (Divide & Conquer)
    if size > 1:
        mid = size // 2
        print(f"  🔪 Разделение батча #{batch_index} ({size} -> {mid} + {size-mid})...")
        
        keys = list(batch.keys())
        part1 = {k: batch[k] for k in keys[:mid]}
        part2 = {k: batch[k] for k in keys[mid:]}
        
        # Рекурсивный вызов (добавляем суффикс к индексу для логов)
        res1 = translate_batch(part1, f"{batch_index}.1")
        res2 = translate_batch(part2, f"{batch_index}.2")
        
        result = {}
        result.update(res1)
        result.update(res2)
        return result
    else:
        # Если splitting уже некуда (1 элемент) и попытки кончились - Фейл
        key = list(batch.keys())[0]
        print(f"  💀 Элемент {key} НЕ УДАЛОСЬ перевести после {max_retries} попыток.")
        return {}

def process_files():
    files_to_check = []
    for root, dirs, files in os.walk(TEMP_DIR):
        for file in files:
            if file.endswith('.htm') or file.endswith('.html'):
                files_to_check.append(os.path.join(root, file))
    
    all_batches = {}
    current_batch = {}
    batch_counter = 0

    print("🔎 Поиск ВСЕХ непереведенных блоков...")

    target_tags = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'div', 'span']
    
    for filepath in files_to_check:
        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')

        found_tags = soup.find_all(target_tags)
        
        for i, tag in enumerate(found_tags):
            # Пропускаем контейнеры (если внутри есть другие блочные теги)
            if tag.find(['p', 'div', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                continue
                
            text = tag.get_text(strip=True)
            if not text or len(text) < 2: continue
            if text.isdigit(): continue
            
            if is_english(text):
                 uid = f"{filepath}::{i}"
                 current_batch[uid] = str(tag)
                 
                 if len(current_batch) >= 20: # Безопасный батч (20 элементов)
                     batch_counter += 1
                     print(f"\n🚀 Перевод батча #{batch_counter} ({len(current_batch)} элементов)...")
                     trans = translate_batch(current_batch, batch_index=batch_counter)
                     all_batches.update(trans)
                     current_batch = {}
                         
    if current_batch:
        batch_counter += 1
        print(f"\n🚀 Перевод последнего батча #{batch_counter} ({len(current_batch)} элементов)...")
        trans = translate_batch(current_batch, batch_index=batch_counter)
        all_batches.update(trans)
        
    print(f"Всего блоков для перевода: {len(all_batches)}")
    
    # Применение изменений
    for filepath in files_to_check:
        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        
        changed = False
        found_tags = soup.find_all(target_tags) 
        
        for i, tag in enumerate(found_tags):
            uid = f"{filepath}::{i}"
            if uid in all_batches:
                new_html = all_batches[uid]
                temp_soup = BeautifulSoup(new_html, 'html.parser')
                real_new_tag = temp_soup.find(recursive=False) or temp_soup
                
                if real_new_tag:
                    tag.replace_with(real_new_tag)
                    changed = True
                    
        if changed:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(str(soup))
            print(f"✅ Допереведен: {os.path.basename(filepath)}")

if __name__ == "__main__":
    process_files()
