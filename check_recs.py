import json

with open('backend/data/approvals.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f'Total recommendations: {len(data)}')
print(f'Unique IDs: {len(set(r.get("id") for r in data))}')
print('\nAll IDs:')
for i, rec in enumerate(data, 1):
    print(f'{i}. {rec.get("id", "NO_ID")} - {rec.get("type")} - {rec.get("title", "NO TITLE")[:50]}')
