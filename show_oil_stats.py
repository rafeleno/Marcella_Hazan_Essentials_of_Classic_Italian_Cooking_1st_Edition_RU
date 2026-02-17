#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Финальное исправление всех упоминаний масла
Только butter → сливочное и olive oil → оливковое
"""

import json
from pathlib import Path
from collections import defaultdict

# Загружаем анализ
with open('oil_analysis.json', 'r', encoding='utf-8') as f:
    results = json.load(f)

# Статистика
print("📊 Анализ всех упоминаний 'масло':\n")
by_type = defaultdict(int)
for r in results:
    by_type[r['oil_type']] += 1

for oil_type, count in sorted(by_type.items(), key=lambda x: (x[0] is None, x[0])):
    print(f"   {oil_type}: {count}")

# Фильтруем только butter и olive_oil, которые еще не исправлены
to_fix = [r for r in results if not r['already_specified'] and r['oil_type'] in ['butter', 'olive_oil']]

print(f"\n⚠️  Требуют исправления:")
print(f"   butter → сливочное масло: {sum(1 for r in to_fix if r['oil_type'] == 'butter')}")
print(f"   olive_oil → оливковое масло: {sum(1 for r in to_fix if r['oil_type'] == 'olive_oil')}")
print(f"   ВСЕГО: {len(to_fix)}")

# Показываем примеры
print(f"\n📋 Примеры (первые 20):\n")
for i, r in enumerate(to_fix[:20], 1):
    print(f"{i}. [{r['file']}] {r['word']} ({r['oil_type']})")
    print(f"   RU: ...{r['ru_context'][:80]}...")
    print(f"   EN: {r['en_text'][:80]}...")
    print()
