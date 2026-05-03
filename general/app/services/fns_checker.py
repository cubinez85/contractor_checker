import requests
import logging
from datetime import datetime
import time
import json
import gzip
from io import BytesIO

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FNSChecker:
    """Проверка контрагентов с гибридным подходом:
    1. Быстрая проверка через egrul.itsoft.ru
    2. При ошибке или отсутствии - проверка через официальный сайт ФНС
    """
    
    def __init__(self):
        self.itsoft_url = "https://egrul.itsoft.ru"
        self.fns_url = "https://egrul.nalog.ru"
        self.session = requests.Session()
        
    def check_batch(self, inn_list):
        """
        Проверка списка ИНН
        """
        results = []
        
        for inn in inn_list:
            try:
                result = self.check_single(inn)
                results.append(result)
                # Добавляем задержку, чтобы не превысить лимиты
                time.sleep(0.5)
            except Exception as e:
                logger.error(f"Ошибка проверки ИНН {inn}: {str(e)}")
                results.append({
                    'inn': inn,
                    'status': 'error',
                    'error': str(e),
                    'check_date': datetime.now().isoformat()
                })
        
        return results
    
    def check_single(self, inn):
        """
        Проверка одного ИНН с fallback на официальный источник
        """
        logger.info(f"========== НАЧАЛО ПРОВЕРКИ ИНН {inn} ==========")
        
        # Сначала пробуем через egrul.itsoft.ru
        logger.info(f"ШАГ 1: Пробуем itsoft для ИНН {inn}")
        result = self._check_via_itsoft(inn)
        logger.info(f"РЕЗУЛЬТАТ itsoft: статус={result.get('status')}, имя={result.get('name')}")
        
        # Если результат — ошибка или "не найдено", и это ЮЛ (10 цифр)
        if result['status'] in ['error', 'inactive'] and len(str(inn)) == 10:
            logger.info(f"ШАГ 2: Сработал fallback! Пробуем официальный ФНС для ИНН {inn}")
            logger.info(f"Причина fallback: статус itsoft = {result['status']}")
            
            fns_result = self._check_via_fns_official(inn)
            
            if fns_result:
                logger.info(f"РЕЗУЛЬТАТ ФНС: статус={fns_result.get('status')}, имя={fns_result.get('name')}")
                if fns_result.get('status') == 'active':
                    logger.info(f"✅ ФНС подтвердил: ИНН {inn} действующий!")
                    return fns_result
                else:
                    logger.info(f"❌ ФНС вернул статус {fns_result.get('status')}, не active")
            else:
                logger.info(f"❌ ФНС вернул None (ошибка запроса или пустой ответ)")
        else:
            logger.info(f"ШАГ 2: Fallback не сработал (статус={result['status']}, длина={len(str(inn))})")
        
        logger.info(f"========== КОНЕЦ ПРОВЕРКИ ИНН {inn}, возвращаем результат itsoft ==========")
        return result
    
    def _check_via_itsoft(self, inn):
        """
        Проверка через бесплатный API egrul.itsoft.ru
        """
        inn = str(inn).strip()
        inn_length = len(inn)
        
        if inn_length == 10:
            entity_type = "ЮЛ"
        elif inn_length == 12:
            entity_type = "ИП"
        else:
            return {
                'inn': inn,
                'name': 'Неверный формат ИНН',
                'status': 'error',
                'error': f'Некорректная длина ИНН: {inn_length} (должно быть 10 или 12 цифр)',
                'check_date': datetime.now().isoformat()
            }
        
        url = f"{self.itsoft_url}/{inn}.json"
        
        try:
            headers = {
                'Accept-encoding': 'gzip',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = self.session.get(url, headers=headers, timeout=15)
            
            if response.status_code == 404:
                return {
                    'inn': inn,
                    'name': f'Не найдено в {"ЕГРЮЛ" if entity_type == "ЮЛ" else "ЕГРИП"}',
                    'status': 'inactive',
                    'entity_type': entity_type,
                    'error': f'{entity_type} с таким ИНН не зарегистрирован',
                    'check_date': datetime.now().isoformat()
                }
            
            response.raise_for_status()
            
            # Декомпрессия ответа
            buf = BytesIO(response.content)
            with gzip.GzipFile(fileobj=buf) as f:
                content = f.read()
            
            data = json.loads(content)
            
            if entity_type == "ЮЛ":
                return self._parse_legal_entity_itsoft(data, inn)
            else:
                return self._parse_individual_entrepreneur_itsoft(data, inn)
                
        except requests.exceptions.Timeout:
            logger.error(f"Timeout при запросе ИНН {inn}")
            return {
                'inn': inn,
                'status': 'error',
                'error': 'Превышено время ожидания ответа от сервера',
                'check_date': datetime.now().isoformat()
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка запроса для ИНН {inn}: {str(e)}")
            return {
                'inn': inn,
                'status': 'error',
                'error': f'Ошибка соединения: {str(e)}',
                'check_date': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Неизвестная ошибка при обработке ИНН {inn}: {str(e)}")
            return {
                'inn': inn,
                'status': 'error',
                'error': f'Внутренняя ошибка: {str(e)}',
                'check_date': datetime.now().isoformat()
            }
    
    def _check_via_fns_official(self, inn):
        """
        Проверка через официальный сайт ФНС (egrul.nalog.ru)
        """
        try:
            logger.info(f"Запрос к официальному API ФНС для ИНН {inn}")
            
            # Шаг 1: POST-запрос для получения ID поиска
            search_data = {
                "vyp3CaptchaToken": "",
                "page": "",
                "query": inn,
                "region": ""
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://egrul.nalog.ru',
                'Referer': 'https://egrul.nalog.ru/index.html'
            }
            
            response = self.session.post(
                self.fns_url, 
                data=search_data, 
                headers=headers, 
                timeout=15
            )
            response.raise_for_status()
            
            result = response.json()
            request_id = result.get('t')
            
            if not request_id:
                logger.warning(f"Не получен request_id для ИНН {inn}")
                return None
            
            logger.info(f"Получен request_id: {request_id[:20]}...")
            
            # Шаг 2: ждём обработки
            time.sleep(2)
            
            # Шаг 3: получаем результат
            result_url = f"{self.fns_url}/search-result/{request_id}"
            result_response = self.session.get(result_url, headers=headers, timeout=15)
            result_response.raise_for_status()
            
            data = result_response.json()
            logger.info(f"Получен ответ от ФНС, наличие rows: {'rows' in data}")
            
            # Парсим данные
            return self._parse_fns_response(data, inn)
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout при запросе к ФНС для ИНН {inn}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка запроса к ФНС для ИНН {inn}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Неизвестная ошибка при запросе к ФНС для ИНН {inn}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _parse_fns_response(self, data, inn):
        """
        Парсинг ответа от ФНС
        Обновленная версия, понимающая реальную структуру ответа
        """
        try:
            # Проверяем наличие данных
            if not data or 'rows' not in data or len(data['rows']) == 0:
                logger.warning(f"Нет данных в ответе ФНС для ИНН {inn}")
                return None
            
            row = data['rows'][0]
            
            # Извлекаем данные в соответствии с реальной структурой
            short_name = row.get('c', '')
            full_name = row.get('n', '')
            name = full_name or short_name or 'Не указано'
            
            reg_date = row.get('r', '')
            inn_from_response = row.get('i', inn)
            ogrn = row.get('o', '')
            kpp = row.get('p', '')
            director_info = row.get('g', '')
            
            # Определяем тип по полю k
            entity_type_map = {
                'ul': 'ЮЛ',
                'ip': 'ИП'
            }
            entity_type = entity_type_map.get(row.get('k', ''), 'Неизвестно')
            
            # Для ответов ФНС статус нужно определять отдельно
            # Поскольку в этом ответе нет явного поля статуса,
            # считаем, что если есть запись - организация действующая
            status = 'active'
            status_text = 'Действующее'
            
            # Проверим, есть ли признаки ликвидации в наименовании
            liquidation_markers = ['ликвидац', 'ликвидац', 'прекращ', 'ликвидировано']
            name_lower = name.lower()
            if any(marker in name_lower for marker in liquidation_markers):
                status = 'liquidating'
                status_text = 'В процессе ликвидации'
            
            result = {
                'inn': inn,
                'name': name,
                'short_name': short_name,
                'full_name': full_name,
                'status': status,
                'status_text': status_text,
                'entity_type': entity_type,
                'registration_date': reg_date,
                'ogrn': ogrn,
                'kpp': kpp,
                'director': director_info,
                'check_date': datetime.now().isoformat(),
                'source': 'fns_official'
            }
            
            logger.info(f"✅ Успешно распарсили ответ ФНС для ИНН {inn}: {name}")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка парсинга ответа ФНС для ИНН {inn}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _parse_legal_entity_itsoft(self, data, inn):
        """Парсинг данных юридического лица из itsoft"""
        try:
            name = data.get('name', {})
            full_name = name.get('fullWithOpf', 'Не указано')
            short_name = name.get('shortWithOpf', '')
            
            status_data = data.get('status', {})
            status_code = status_data.get('code', '')
            status_name = status_data.get('name', '')
            
            if 'ликвидац' in status_name.lower() or status_code in ['LIQUIDATING', '206']:
                status = 'liquidating'
            elif status_code in ['ACTIVE', '101']:
                status = 'active'
            else:
                status = 'inactive'
            
            reg_date = data.get('regDate', '')
            liquidation_date = data.get('liquidationDate', '')
            
            address_data = data.get('address', {})
            address = address_data.get('fullAddress', '')
            
            return {
                'inn': inn,
                'name': full_name or short_name or 'Не указано',
                'short_name': short_name,
                'status': status,
                'status_text': status_name,
                'entity_type': 'ЮЛ',
                'registration_date': reg_date,
                'liquidation_date': liquidation_date,
                'address': address,
                'check_date': datetime.now().isoformat(),
                'source': 'itsoft'
            }
        except Exception as e:
            logger.error(f"Ошибка парсинга данных ЮЛ для ИНН {inn}: {str(e)}")
            return {
                'inn': inn,
                'name': 'Ошибка обработки данных',
                'status': 'error',
                'entity_type': 'ЮЛ',
                'error': str(e),
                'check_date': datetime.now().isoformat(),
                'source': 'itsoft'
            }
    
    def _parse_individual_entrepreneur_itsoft(self, data, inn):
        """Парсинг данных ИП из itsoft"""
        try:
            if 'fio' in data:
                fio_data = data.get('fio', {})
                full_name = f"{fio_data.get('surname', '')} {fio_data.get('name', '')} {fio_data.get('patronymic', '')}".strip()
            else:
                name = data.get('name', {})
                full_name = name.get('fullWithOpf', 'Не указано')
            
            status_data = data.get('status', {})
            status_code = status_data.get('code', '')
            status_name = status_data.get('name', '')
            
            if 'ликвидац' in status_name.lower() or status_code in ['LIQUIDATING', '206']:
                status = 'liquidating'
            elif 'действующ' in status_name.lower() or status_code in ['ACTIVE', '101']:
                status = 'active'
            else:
                status = 'inactive'
            
            reg_date = data.get('regDate', '')
            liquidation_date = data.get('liquidationDate', '')
            
            return {
                'inn': inn,
                'name': full_name or 'ИП (данные не указаны)',
                'status': status,
                'status_text': status_name,
                'entity_type': 'ИП',
                'registration_date': reg_date,
                'liquidation_date': liquidation_date,
                'check_date': datetime.now().isoformat(),
                'source': 'itsoft'
            }
        except Exception as e:
            logger.error(f"Ошибка парсинга данных ИП для ИНН {inn}: {str(e)}")
            return {
                'inn': inn,
                'name': 'ИП (ошибка обработки)',
                'status': 'error',
                'entity_type': 'ИП',
                'error': str(e),
                'check_date': datetime.now().isoformat(),
                'source': 'itsoft'
            }
    
    def _get_status_text(self, status_code):
        """Получение текстового описания статуса"""
        status_map = {
            '01': 'Действующее',
            '02': 'В процессе ликвидации',
            '03': 'Ликвидировано',
            '04': 'В процессе реорганизации',
            '05': 'Реорганизовано',
            'ACTIVE': 'Действующее',
            'LIQUIDATING': 'В процессе ликвидации',
            'LIQUIDATED': 'Ликвидировано'
        }
        return status_map.get(str(status_code), 'Неизвестный статус')
