import sys
sys.path.insert(0, 'backend')

from approval_store import list_recommendations

recs = list_recommendations()
print(f'list_recommendations() returned: {len(recs)} items')

for i, rec in enumerate(recs, 1):
    print(f'{i}. {rec.get("id")} - {rec.get("type")} - {rec.get("status")}')
