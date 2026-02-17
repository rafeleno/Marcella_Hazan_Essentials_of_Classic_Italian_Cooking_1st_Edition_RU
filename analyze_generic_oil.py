#!/usr/bin/env python3
import re
from pathlib import Path
from bs4 import BeautifulSoup

def analyze_generic_oil():
    print("🔍 Анализ 'oil' -> 'масло' (без уточнений) в Hazan_RU_Final_1.0.epub\n")

    ru_dir = Path("temp_check_1_0/OEBPS")
    en_dir = Path("temp_en_check/OEBPS")
    
    count = 0
    
    for ru_file in sorted(ru_dir.glob("*.htm")):
        en_file = en_dir / ru_file.name
        if not en_file.exists(): continue
        
        with open(ru_file, 'r', encoding='utf-8') as f:
            ru_soup = BeautifulSoup(f.read(), 'html.parser')
        with open(en_file, 'r', encoding='utf-8') as f:
            en_soup = BeautifulSoup(f.read(), 'html.parser')

        for el in ru_soup.find_all(id=True):
            ru_text = el.get_text()
            if "масло" not in ru_text.lower(): continue
            
            # Проверяем, есть ли уже уточнение
            if "сливочн" in ru_text.lower() or "оливков" in ru_text.lower() or "растительн" in ru_text.lower():
                continue

            en_element = en_soup.find(id=el.get('id'))
            if not en_element: continue
            en_text = en_element.get_text().lower()

            # Ищем 'oil' как отдельное слово, исключая 'olive oil', 'vegetable oil'
            # (ведь 'olive oil' мы уже проверили, оно везде переведено как 'оливковое')
            if re.search(r'\boil\b', en_text) and "olive" not in en_text and "vegetable" not in en_text:
                 if count < 10: # Показываем первые 10
                     print(f"[{ru_file.name}#{el.get('id')}]")
                     print(f"  RU: {ru_text.strip()[:100]}...")
                     print(f"  EN: {en_text.strip()[:100]}...")
                 count += 1

    print(f"\nTotal potential generic 'oil' -> 'масло': {count}")

if __name__ == "__main__":
    analyze_generic_oil()
