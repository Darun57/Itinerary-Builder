import urllib.request
import json
data = json.dumps({'request': {'destination': 'Paris', 'days': 3, 'theme': 'luxury', 'guests': 2, 'daily_island_plan': [], 'start_date': '2024-01-01', 'end_date': '2024-01-03', 'pace': 'moderate', 'activities': [], 'dietary_restrictions': []}, 'itinerary_text': '{ "days": [ { "day_number": 1, "title": "Arrival", "items": [] } ] }'}).encode('utf-8')
req = urllib.request.Request('http://127.0.0.1:8000/api/pdf/generate', data=data, headers={'Content-Type': 'application/json'})
try:
    res = urllib.request.urlopen(req)
    print(res.getcode())
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code}")
    print(e.read().decode())
