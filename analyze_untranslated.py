import os
import re
from bs4 import BeautifulSoup

TEMP_DIR = "temp_epub_final_1_0"

def is_english(text):
    if not text: return False
    text = text.strip()
    latin = len(re.findall(r'[a-zA-Z]', text))
    cyrillic = len(re.findall(r'[а-яА-ЯёЁ]', text))
    if latin > 0 and cyrillic == 0: return True
    if latin > 10 and latin > cyrillic * 5: return True 
    return False

def count_untranslated():
    total_blocks = 0
    total_files = 0
    files_to_check = []
    
    for root, dirs, files in os.walk(TEMP_DIR):
        for file in files:
            if file.endswith('.htm') or file.endswith('.html'):
                files_to_check.append(os.path.join(root, file))
    
    for filepath in files_to_check:
        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            
        found_tags = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'div', 'span'])
        file_blocks = 0
        
        for tag in found_tags:
            if tag.find(['p', 'div', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']): continue
            text = tag.get_text(strip=True)
            if not text or len(text) < 2: continue
            if text.isdigit(): continue
            
            if is_english(text):
                file_blocks += 1
                total_blocks += 1
                
        if file_blocks > 0:
            total_files += 1
            # print(f"{os.path.basename(filepath)}: {file_blocks} блоков")
            
    print(f"\n📊 АНАЛИЗ ЗАВЕРШЕН:")
    print(f"  Всего найдено непереведенных блоков: {total_blocks}")
    print(f"  В {total_files} файлах (из {len(files_to_check)})")
    
    # Расчет батчей:
    batch_20 = (total_blocks + 19) // 20
    batch_30 = (total_blocks + 29) // 30
    batch_50 = (total_blocks + 49) // 50
    
    print(f"\nСКОЛЬКО БАТЧЕЙ ПОТРЕБУЕТСЯ:")
    print(f"  При размере 20: ~{batch_20} батчей")
    print(f"  При размере 30: ~{batch_30} батчей")
    print(f"  При размере 50: ~{batch_50} батчей")

if __name__ == "__main__":
    count_untranslated()
