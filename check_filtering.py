import json

# Load approvals
with open('backend/data/approvals.json', 'r') as f:
    approvals = json.load(f)

# Load healing history
with open('backend/data/healing_history.json', 'r') as f:
    healing_history = json.load(f)

# Get successful healing resource IDs
successful_ids = set()
for action in healing_history:
    if action.get('status') == 'success':
        successful_ids.add(str(action.get('resource_id')))

print(f"Successful healing IDs: {successful_ids}\n")

# Check each recommendation
print("Recommendation filtering analysis:")
print("=" * 80)
for rec in approvals:
    rec_id = rec.get('id')
    resource_id = str(rec.get('resource_id', '')) if rec.get('resource_id') else None
    resource_name = rec.get('resource_name')
    
    candidates = []
    if resource_id:
        candidates.append(resource_id)
    if resource_name:
        candidates.append(resource_name)
    
    is_healed = any(cand in successful_ids for cand in candidates)
    
    print(f"\nID: {rec_id}")
    print(f"  Type: {rec.get('type')}")
    print(f"  Resource ID: {resource_id}")
    print(f"  Resource Name: {resource_name}")
    print(f"  Candidates: {candidates}")
    print(f"  HEALED: {is_healed} {'❌ FILTERED OUT' if is_healed else '✅ VISIBLE'}")
