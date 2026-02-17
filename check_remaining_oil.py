#!/usr/bin/env python3
import re
from pathlib import Path
from bs4 import BeautifulSoup
import sys

def check_olive_oil_gaps():
    print("🔍 Ищу пропущенные 'масло' (EN: olive oil, RU: без 'оливковое') в Hazan_RU_Final_1.0.epub\n")

    ru_dir = Path("temp_check_1_0/OEBPS")
    en_dir = Path("temp_en_check/OEBPS")

    count = 0
    
    # Паттерн для "масло" (без учета регистра)
    pattern_oil = re.compile(r'\bмасл[а-яё]*\b', re.IGNORECASE)

    for ru_file in sorted(ru_dir.glob("*.htm")):
        en_file = en_dir / ru_file.name
        if not en_file.exists():
            continue
        
        with open(ru_file, 'r', encoding='utf-8') as f:
            ru_soup = BeautifulSoup(f.read(), 'html.parser')
        
        with open(en_file, 'r', encoding='utf-8') as f:
            en_soup = BeautifulSoup(f.read(), 'html.parser')
        
        for el in ru_soup.find_all(id=True):
            ru_text = el.get_text()
            matches = list(pattern_oil.finditer(ru_text))
            
            if not matches:
                continue

            # Ищем английский аналог
            en_el = en_soup.find(id=el.get('id'))
            if not en_el:
                continue
                
            en_text = en_el.get_text()
            
            # Проверяем условие
            if "olive oil" in en_text.lower():
                # Проверяем, есть ли уже уточнение "оливковое" в этом куске текста
                if "оливков" not in ru_text.lower():
                    # Выводим контекст
                    print(f"[{ru_file.name}#{el.get('id')}]")
                    print(f"  RU: {ru_text.strip()[:100]}...")
                    print(f"  EN: {en_text.strip()[:100]}...")
                    count += 1
    
    print(f"\n✅ Найдено {count} мест для исправления.")

if __name__ == "__main__":
    check_olive_oil_gaps()
