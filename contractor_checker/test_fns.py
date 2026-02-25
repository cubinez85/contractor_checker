import requests
import json
import time
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_fns(inn):
    """Прямой тест API ФНС"""
    
    print(f"\n=== ТЕСТИРОВАНИЕ ИНН {inn} ===\n")
    
    session = requests.Session()
    
    # Шаг 1: POST-запрос
    url = "https://egrul.nalog.ru/"
    data = {
        "vyp3CaptchaToken": "",
        "page": "",
        "query": inn,
        "region": ""
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*'
    }
    
    print(f"POST {url}")
    print(f"Data: {data}")
    
    try:
        response = session.post(url, data=data, headers=headers, timeout=15)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        
        result = response.json()
        request_id = result.get('t')
        print(f"Request ID: {request_id}")
        
        if not request_id:
            print("❌ Нет request_id")
            return
        
        # Шаг 2: ждём
        print("Ждём 2 секунды...")
        time.sleep(2)
        
        # Шаг 3: GET-запрос результата
        result_url = f"https://egrul.nalog.ru/search-result/{request_id}"
        print(f"GET {result_url}")
        
        result_response = session.get(result_url, headers=headers, timeout=15)
        print(f"Status: {result_response.status_code}")
        print(f"Response: {result_response.text[:500]}")
        
        data = result_response.json()
        
        if data and 'rows' in data and len(data['rows']) > 0:
            print("\n✅ НАЙДЕНО!")
            row = data['rows'][0]
            print(f"Наименование: {row.get('c', 'Н/Д')}")
            print(f"ИНН: {row.get('i', 'Н/Д')}")
            print(f"Дата: {row.get('r', 'Н/Д')}")
            print(f"Статус: {row.get('s', 'Н/Д')}")
        else:
            print("\n❌ НЕ НАЙДЕНО")
            
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fns("7706413348")
