import urllib.request
import json

data = json.dumps({
    'destination': 'Paris',
    'days': 3,
    'theme': 'luxury',
    'guests': 2,
    'daily_island_plan': [],
    'start_date': '2024-01-01',
    'end_date': '2024-01-03',
    'pace': 'moderate',
    'activities': [],
    'dietary_restrictions': []
}).encode('utf-8')

req = urllib.request.Request('http://127.0.0.1:8005/api/ai/generate', data=data, headers={'Content-Type': 'application/json'})
try:
    print("Sending request...")
    res = urllib.request.urlopen(req)
    print("Response code:", res.getcode())
    print(res.read().decode())
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code}")
    print(e.read().decode())
except Exception as e:
    print(f"Error: {e}")
