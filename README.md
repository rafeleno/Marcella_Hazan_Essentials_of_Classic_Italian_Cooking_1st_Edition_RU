# 📖 Hazan RU — «Основы классической итальянской кухни» на русском

> Открытый инструментарий для машинного перевода и пост-обработки EPUB-книги  
> **Marcella Hazan — Essentials of Classic Italian Cooking (1st Edition)**

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Status](https://img.shields.io/badge/Статус-В%20разработке-orange)]()
[![EPUB](https://img.shields.io/badge/Формат-EPUB-lightgrey?logo=bookstack)]()

---

## 🍝 О проекте

Этот репозиторий содержит полный конвейер для автоматического перевода англоязычного EPUB «Essentials of Classic Italian Cooking» Марчеллы Хазан на **русский язык** с сохранением:

- оригинальной структуры и форматирования HTML внутри EPUB
- всех стилей, тегов, изображений и цветовых классов книги
- корректных склонений и терминологии итальянской кухни
- американских мер с метрическим эквивалентом в скобках

Перевод выполняется через **Google Translate API** (библиотека `deep-translator`) с многоуровневой пост-обработкой: исправлением терминологии, единиц измерения, масел, диапазонов, заголовков и форматирования.

---

## ✨ Возможности

| Возможность                    | Описание                                                     |
| ------------------------------ | ------------------------------------------------------------ |
| 🔄 **Инкрементальный перевод** | Состояние сохраняется в JSON — можно прерывать и продолжать  |
| 🏗️ **HTML-aware**              | Переводятся только текстовые узлы, теги остаются нетронутыми |
| 🧂 **Терминология**            | Словарь итальянских кулинарных терминов и техник             |
| ⚖️ **Конвертация мер**         | фунты → г, чашки → мл, °F → °C, дюймы → см                   |
| 🧈 **Исправление масел**       | «масло» → «сливочное масло» с учётом всех падежей            |
| 🎨 **Сохранение стилей**       | CSS-классы (в т.ч. `color_CA4E00`) сохраняются               |
| 📊 **Аудит качества**          | Скрипты анализа непереведённых, дублей, артефактов           |
| 📦 **EPUB-упаковка**           | Корректная сборка по стандарту (mimetype без сжатия)         |

---

## 📁 Структура репозитория

```
HAZAN/
├── 📄 translate_epub.py              # Главный скрипт перевода (Google Translate + пост-обработка)
├── 📄 main.py                        # Простой скрипт замены по словарю (v1, прототип)
├── 📄 full_translate_v3.py           # Полный перевод v3 (OpenAI)
├── 📄 full_translate_v4.py           # Полный перевод v4 (с прогрессом)
├── 📄 generate_version_03.py         # Генерация версии 0.3
│
├── 🔍 Анализ и аудит
│   ├── analyze_untranslated.py       # Поиск непереведённых фрагментов
│   ├── analyze_unfixed.py            # Анализ неисправленных мест
│   ├── audit_final_epub.py           # Полный аудит итогового EPUB
│   ├── find_english_fragments.py     # Поиск оставшегося английского текста
│   └── auto_fix_metrics.py          # Автоисправление метрических единиц
│
├── 🧈 Исправление масел (Butter/Oil)
│   ├── check_butter_translation.py  # Анализ ошибок перевода "butter"
│   ├── fix_butter_translation.py    # Исправление v1
│   ├── fix_butter_translation_final.py # Исправление финальное
│   ├── fix_all_oil.py               # Исправление переводов "oil"
│   └── butter_translation_issues.json # База проблемных мест (765 записей)
│
├── 🛠️ Прочие фиксы
│   ├── fix_header_caps.py           # Исправление регистра заголовков
│   ├── fix_broken_ranges.py         # Исправление диапазонов (1–2, а не "с 1 до 2")
│   ├── fix_markdown_asterisks.py    # Убирает markdown-разметку из HTML
│   ├── remove_duplicate_headers.py  # Удаление дублей заголовков
│   └── restore_italian_subtitles.py # Восстановление итальянских подзаголовков
│
├── 📚 Документация
│   ├── ZAMETKI_PO_PEREVODU.md       # Золотой стандарт стиля и терминологии
│   ├── BUGS_AND_FIXES.md            # Известные баги и их решения
│   ├── BUTTER_FIX_REPORT.md         # Отчёт об исправлении переводов масла
│   └── BUTTER_FIX_REPORT_v0.4.md   # Отчёт v0.4
│
├── 📦 Версии EPUB
│   ├── Marcella_Hazan_...epub       # Оригинал (EN)
│   ├── Hazan_RU_Final_0.1.epub      # Версия 0.1
│   ├── Hazan_RU_Final_0.2.0.epub    # Версия 0.2.0
│   ├── Hazan_RU_Final_0.2.1.epub    # Версия 0.2.1
│   └── Hazan_RU_Final_0.3.epub      # Текущая стабильная версия ✅
│
└── 📈 Прогресс и отчёты
    ├── progress_v4.json             # Прогресс перевода v4
    ├── oil_fix_report.json          # Отчёт исправлений масел
    └── FINAL_OIL_REPORT.txt        # Финальный отчёт по маслам
```

---

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
pip install beautifulsoup4 lxml deep-translator
```

### 2. Положите оригинальный файл в папку

```bash
# Книга должна называться:
Marcella_Hazan_Essentials_of_Classic_Italian_Cooking_1st_Edition.epub
```

### 3. Запуск перевода

```bash
python translate_epub.py
```

Скрипт автоматически:

- распакует EPUB
- переведёт все HTML-файлы поглавно
- сохранит прогресс каждые 10 элементов
- соберёт готовый `Hazan_RU_Translated.epub`

> 💡 **Можно прервать** `Ctrl+C` — при следующем запуске продолжит с того же места.

---

## ⚙️ Конфигурация

В файле `translate_epub.py` настройте константы:

```python
INPUT_FILE   = 'Marcella_Hazan_...epub'  # Входной EPUB
OUTPUT_FILE  = 'Hazan_RU_Translated.epub' # Выходной EPUB
API_DELAY    = 1.0   # Задержка между запросами (сек)
SAVE_EVERY_N = 10    # Сохранять прогресс каждые N элементов
```

---

## 📐 Золотой стандарт перевода

Подробные правила в [`ZAMETKI_PO_PEREVODU.md`](ZAMETKI_PO_PEREVODU.md). Ключевые принципы:

### Единицы измерения

```
2 pounds  →  2 фунта (900 г)
1 cup     →  1 чашка (~240 мл)
350°F     →  175°C (350°F)
1 inch    →  1 дюйм (2.5 см)
```

### Диапазоны — через тире

```
❌  "с 1 до 2 ложками"
✅  "1–2 ложки"
```

### Масла — строго

```
butter  →  сливочное масло (все падежи)
oil     →  оливковое масло
```

### Термины — транслитерация

```
Battuto    →  баттуто
Soffritto  →  соффритто
Al dente   →  аль денте
```

---

## 🗺️ Дорожная карта

- [x] Прототип замены по словарю (`main.py`)
- [x] Полный перевод через Google Translate с сохранением HTML
- [x] Пост-обработка терминов и единиц измерения
- [x] Исправление переводов «butter» (526/765 мест, ~69%)
- [x] Исправление форматирования масел (oil/butter)
- [x] Удаление markdown-артефактов из HTML
- [x] Восстановление итальянских подзаголовков
- [x] Аудит непереведённых фрагментов
- [ ] Улучшенный перевод через OpenAI GPT (в работе)
- [ ] Ручная вычитка и редактура
- [ ] Верификация всех метрических конверсий
- [ ] Публикация финальной версии v1.0

---

## 🤝 Вклад в проект

Проект открыт для участия! Особенно приветствуется:

- 🔍 **Ручная вычитка** рецептов и исправление ошибок перевода
- 📝 **Пополнение глоссария** в `ZAMETKI_PO_PEREVODU.md`
- 🐛 **Репорты багов** и предложения по скриптам
- 🌐 **Улучшение качества** машинного перевода

Пожалуйста, создайте Issue или Pull Request.

---

## ⚠️ Правовой дисклеймер

Этот репозиторий содержит **только инструменты для обработки EPUB**. Оригинальная книга _Essentials of Classic Italian Cooking_ является интеллектуальной собственностью автора и издателя. Использование скриптов предполагает, что у вас есть легально приобретённая копия книги.

Перевод создаётся исключительно для **личного использования** и не предназначен для распространения.

---

## 📜 Лицензия

MIT License — см. файл [LICENSE](LICENSE).

---

<div align="center">
  <i>Сделано с любовью к итальянской кухне 🇮🇹 и уважением к Марчелле Хазан</i>
</div>

---

---

# 📖 Hazan RU — "Essentials of Classic Italian Cooking" in Russian

> An open-source toolkit for machine translation and post-processing of the EPUB  
> **Marcella Hazan — Essentials of Classic Italian Cooking (1st Edition)**

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Status](https://img.shields.io/badge/Status-In%20Progress-orange)]()
[![EPUB](https://img.shields.io/badge/Format-EPUB-lightgrey?logo=bookstack)]()

---

## 🍝 About

This repository contains a complete pipeline for automatically translating Marcella Hazan's _Essentials of Classic Italian Cooking_ from English into **Russian**, while preserving:

- The original HTML structure and formatting inside the EPUB
- All styles, tags, images, and CSS color classes
- Correct Russian declensions and Italian culinary terminology
- American units of measurement with metric equivalents in parentheses

Translation is powered by the **Google Translate API** (via `deep-translator`) with a multi-stage post-processing pipeline: terminology correction, unit conversion, oil/butter disambiguation, range formatting, heading case normalization, and HTML artifact cleanup.

---

## ✨ Features

| Feature                        | Description                                                         |
| ------------------------------ | ------------------------------------------------------------------- |
| 🔄 **Incremental translation** | Progress saved to JSON — pause and resume at any time               |
| 🏗️ **HTML-aware parsing**      | Only text nodes are translated; all tags remain untouched           |
| 🧂 **Terminology glossary**    | Italian culinary terms and cooking technique translations           |
| ⚖️ **Unit conversion**         | pounds → g, cups → ml, °F → °C, inches → cm                         |
| 🧈 **Butter/Oil fix**          | "масло" → "сливочное масло" with all Russian declension forms       |
| 🎨 **Style preservation**      | CSS classes (incl. `color_CA4E00`) are fully preserved              |
| 📊 **Quality audit**           | Scripts to find untranslated text, duplicate headers, and artifacts |
| 📦 **EPUB packaging**          | Correct assembly per EPUB spec (mimetype stored uncompressed)       |

---

## 📁 Repository Structure

```
HAZAN/
├── 📄 translate_epub.py              # Main translation script (Google Translate + post-processing)
├── 📄 main.py                        # Simple dictionary-based replacement (v1 prototype)
├── 📄 full_translate_v3.py           # Full translation v3 (OpenAI)
├── 📄 full_translate_v4.py           # Full translation v4 (with progress tracking)
├── 📄 generate_version_03.py         # Version 0.3 generator
│
├── 🔍 Analysis & Audit
│   ├── analyze_untranslated.py       # Find untranslated fragments
│   ├── analyze_unfixed.py            # Analyze remaining unfixed items
│   ├── audit_final_epub.py           # Full audit of the final EPUB
│   ├── find_english_fragments.py     # Locate remaining English text
│   └── auto_fix_metrics.py          # Auto-fix metric unit conversions
│
├── 🧈 Butter/Oil Fixes
│   ├── check_butter_translation.py  # Detect "butter" translation errors
│   ├── fix_butter_translation.py    # Fix script v1
│   ├── fix_butter_translation_final.py # Final fix script
│   ├── fix_all_oil.py               # Fix "oil" translations
│   └── butter_translation_issues.json # Database of problem spots (765 records)
│
├── 🛠️ Other Fixes
│   ├── fix_header_caps.py           # Normalize heading capitalization
│   ├── fix_broken_ranges.py         # Fix ranges ("1–2" instead of "from 1 to 2")
│   ├── fix_markdown_asterisks.py    # Remove markdown artifacts from HTML
│   ├── remove_duplicate_headers.py  # Remove duplicate headings
│   └── restore_italian_subtitles.py # Restore Italian subtitles
│
├── 📚 Documentation
│   ├── ZAMETKI_PO_PEREVODU.md       # Golden standard style guide & glossary
│   ├── BUGS_AND_FIXES.md            # Known bugs and solutions
│   ├── BUTTER_FIX_REPORT.md         # Butter translation fix report
│   └── BUTTER_FIX_REPORT_v0.4.md   # Fix report v0.4
│
├── 📦 EPUB Versions
│   ├── Marcella_Hazan_...epub       # Original (EN)
│   ├── Hazan_RU_Final_0.1.epub      # Version 0.1
│   ├── Hazan_RU_Final_0.2.0.epub    # Version 0.2.0
│   ├── Hazan_RU_Final_0.2.1.epub    # Version 0.2.1
│   └── Hazan_RU_Final_0.3.epub      # Current stable release ✅
│
└── 📈 Progress & Reports
    ├── progress_v4.json             # Translation progress v4
    ├── oil_fix_report.json          # Oil fix report
    └── FINAL_OIL_REPORT.txt        # Final oil processing report
```

---

## 🚀 Quick Start

### 1. Install dependencies

```bash
pip install beautifulsoup4 lxml deep-translator
```

### 2. Place the source file in the directory

```bash
# The book must be named:
Marcella_Hazan_Essentials_of_Classic_Italian_Cooking_1st_Edition.epub
```

### 3. Run the translation

```bash
python translate_epub.py
```

The script will automatically:

- Unpack the EPUB
- Translate all HTML files chapter by chapter
- Save progress every 10 elements
- Build the final `Hazan_RU_Translated.epub`

> 💡 **Safe to interrupt** with `Ctrl+C` — the next run will continue from where it left off.

---

## ⚙️ Configuration

Edit the constants in `translate_epub.py`:

```python
INPUT_FILE   = 'Marcella_Hazan_...epub'   # Source EPUB
OUTPUT_FILE  = 'Hazan_RU_Translated.epub' # Output EPUB
API_DELAY    = 1.0    # Delay between API requests (seconds)
SAVE_EVERY_N = 10     # Save progress every N elements
```

---

## 📐 Translation Style Guide

Full rules in [`ZAMETKI_PO_PEREVODU.md`](ZAMETKI_PO_PEREVODU.md). Key principles:

### Units of Measurement

```
2 pounds  →  2 фунта (900 г)
1 cup     →  1 чашка (~240 мл)
350°F     →  175°C (350°F)
1 inch    →  1 дюйм (2.5 см)
```

### Ranges — em dash, not "from...to"

```
❌  "с 1 до 2 ложками"
✅  "1–2 ложки"
```

### Oils — strict disambiguation

```
butter  →  сливочное масло (all declension forms)
oil     →  оливковое масло
```

### Italian Terms — transliteration

```
Battuto    →  баттуто
Soffritto  →  соффритто
Al dente   →  аль денте
```

---

## 🗺️ Roadmap

- [x] Dictionary-based replacement prototype (`main.py`)
- [x] Full HTML-aware translation via Google Translate
- [x] Post-processing of terms and units
- [x] Butter translation fix (526/765 spots, ~69%)
- [x] Oil/butter disambiguation
- [x] Markdown artifact removal from HTML
- [x] Italian subtitle restoration
- [x] Untranslated fragment audit
- [ ] Improved translation via OpenAI GPT (in progress)
- [ ] Manual proofreading and editorial review
- [ ] Full verification of metric conversions
- [ ] Final v1.0 release

---

## 🤝 Contributing

The project is open for contributions! Especially welcome:

- 🔍 **Manual proofreading** of recipes and translation corrections
- 📝 **Glossary additions** to `ZAMETKI_PO_PEREVODU.md`
- 🐛 **Bug reports** and script improvement suggestions
- 🌐 **Machine translation quality** improvements

Please open an Issue or a Pull Request.

---

## ⚠️ Legal Disclaimer

This repository contains **only tools for processing EPUB files**. The original book _Essentials of Classic Italian Cooking_ is the intellectual property of the author and publisher. Use of these scripts assumes you own a legally purchased copy of the book.

The translation is created strictly for **personal use** and is not intended for distribution.

---

## 📜 License

MIT License — see [LICENSE](LICENSE).

---

<div align="center">
  <i>Made with love for Italian cuisine 🇮🇹 and deep respect for Marcella Hazan</i>
</div>
