#!/usr/bin/env python
"""Test idle cluster detection"""
from databricks_client import get_databricks_client
from datetime import datetime

client = get_databricks_client()
clusters = client.get_all_clusters()

now = datetime.now()
idle_clusters = []

for cluster in clusters:
    if cluster.get('state') != 'RUNNING':
        continue
    
    last_activity = cluster.get('last_activity_time')
    if last_activity:
        last_activity_dt = datetime.fromtimestamp(last_activity / 1000)
        idle_minutes = (now - last_activity_dt).total_seconds() / 60
        
        if idle_minutes > 30:
            idle_clusters.append({
                'name': cluster.get('cluster_name'),
                'idle_minutes': idle_minutes,
                'last_activity': last_activity_dt
            })

print(f'Total RUNNING clusters: {len([c for c in clusters if c.get("state") == "RUNNING"])}')
print(f'Idle clusters (>30 min): {len(idle_clusters)}')
print()

if idle_clusters:
    for ic in idle_clusters:
        print(f"• {ic['name']}: {ic['idle_minutes']:.1f} minutes")
else:
    print('No clusters idle for 30+ minutes')
    print()
    print('Closest to idle threshold:')
    running = [(c.get('cluster_name'), 
               (now - datetime.fromtimestamp(c.get('last_activity_time', 0) / 1000)).total_seconds() / 60 if c.get('last_activity_time') else 0,
               c.get('state'))
              for c in clusters if c.get('state') == 'RUNNING' and c.get('last_activity_time')]
    for name, idle_mins, state in sorted(running, key=lambda x: -x[1])[:5]:
        print(f"• {name} ({state}): {idle_mins:.1f} minutes")
