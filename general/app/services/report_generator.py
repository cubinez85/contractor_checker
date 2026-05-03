import pandas as pd
from datetime import datetime
import os
from flask import current_app

class ReportGenerator:
    def __init__(self):
        self.reports_folder = current_app.config['REPORTS_FOLDER']
        
    def generate_excel(self, results, user_email):
        """
        Генерация Excel отчета
        """
        filename = f"check_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = os.path.join(self.reports_folder, filename)
        
        # Подготовка данных для отчета
        data = []
        for r in results:
            # Определяем тип
            entity_type = r.get('entity_type', 'Неизвестно')
            inn_display = f"{r.get('inn')} ({entity_type})" if entity_type != 'Неизвестно' else r.get('inn')
            
            data.append({
                'ИНН': inn_display,
                'Наименование': r.get('name', 'Не найдено'),
                'Тип': entity_type,
                'Статус': self._translate_status(r.get('status'), entity_type),
                'Дата регистрации': r.get('registration_date', ''),
                'Дата проверки': r.get('check_date', ''),
                'Рекомендация': self._get_recommendation(r.get('status'))
            })
        
        # Создание DataFrame
        df = pd.DataFrame(data)
        
        # Сохранение в Excel
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Проверка контрагентов', index=False)
            
            # Настройка ширины колонок
            worksheet = writer.sheets['Проверка контрагентов']
            for i, col in enumerate(df.columns):
                column_width = max(df[col].astype(str).map(len).max(), len(col)) + 2
                worksheet.column_dimensions[chr(65 + i)].width = min(column_width, 50)
        
        return filepath
    
    def _translate_status(self, status, entity_type=''):
        status_map = {
            'active': 'Действующее',
            'inactive': 'Недействующее',
            'liquidating': 'В стадии ликвидации',
            'error': 'Ошибка проверки'
        }
        base_status = status_map.get(status, 'Неизвестно')
        
        # Для ИП можно добавить пометку
        if entity_type == 'ИП' and status == 'active':
            return 'Действующий ИП'
        elif entity_type == 'ИП' and status == 'inactive':
            return 'Недействующий ИП'
        elif entity_type == 'ИП' and status == 'liquidating':
            return 'ИП в стадии ликвидации'
        
        return base_status
    
    def _get_recommendation(self, status):
        if status == 'active':
            return 'Рекомендуется к сотрудничеству'
        elif status in ['inactive', 'liquidating']:
            return 'Исключить из сотрудничества'
        else:
            return 'Требуется ручная проверка'
