#!/usr/bin/env python3
import zipfile
import re
from bs4 import BeautifulSoup

def audit_epub():
    epub_path = "Hazan_RU_Final_0.5.epub"
    print(f"🕵️‍♂️ Аудит файла: {epub_path}\n")
    
    try:
        zf = zipfile.ZipFile(epub_path)
    except FileNotFoundError:
        print("❌ Файл не найден!")
        return

    # 1. Проверка mimetype (должен быть без переноса строки)
    try:
        mimetype = zf.read("mimetype").decode("utf-8")
        if mimetype.strip() != "application/epub+zip":
             print(f"⚠️  Mimetype странный: '{mimetype}'")
        if "\n" in mimetype:
             print("⚠️  Mimetype содержит перенос строки (может не открываться в некоторых ридерах)")
        else:
             print("✅ Mimetype корректен")
    except KeyError:
        print("❌ Mimetype отсутствует!")

    # 2. Сканирование контента
    english_pattern = re.compile(r'\b(the|and|with|that|this|for|are|from)\b', re.IGNORECASE)
    technical_pattern = re.compile(r'(\[\[|\]\]|__|\{|\})') # Скобки, подчеркивания
    
    count_en = 0
    count_tech = 0
    
    file_list = zf.namelist()
    html_files = [f for f in file_list if f.endswith(".htm") or f.endswith(".html")]
    
    print(f"\n🔍 Сканирование {len(html_files)} HTML файлов...\n")
    
    for filename in html_files:
        content = zf.read(filename).decode("utf-8")
        soup = BeautifulSoup(content, 'html.parser')
        text = soup.get_text()
        
        # Ищем английские слова
        en_matches = list(english_pattern.finditer(text))
        if en_matches:
            # Фильтруем ложные срабатывания (например, в ссылках или коде, хотя мы берем get_text)
            # Часто "and" может быть частью имени или бренда.
            # Покажем первые 3 для примера
            print(f"⚠️  Возможно непереведенный текст в {filename}:")
            for m in en_matches[:3]:
                ctx = text[max(0, m.start()-20):min(len(text), m.end()+20)].replace('\n', ' ')
                print(f"   ...{ctx}...")
            count_en += len(en_matches)

        # Ищем технические артефакты
        tech_matches = list(technical_pattern.finditer(text))
        if tech_matches:
            print(f"⚠️  Технические символы в {filename}:")
            for m in tech_matches[:3]:
                ctx = text[max(0, m.start()-20):min(len(text), m.end()+20)].replace('\n', ' ')
                print(f"   ...{ctx}...")
            count_tech += len(tech_matches)
            
    print("-" * 50)
    print(f"ИТОГО:")
    print(f"🇬🇧 Подозрительных английских слов: {count_en}")
    print(f"🤖 Технических артефактов: {count_tech}")

if __name__ == "__main__":
    audit_epub()
