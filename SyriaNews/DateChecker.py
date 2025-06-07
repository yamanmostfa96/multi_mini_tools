from datetime import datetime,timedelta, date

import re


"""
كلاس فحص التواريخ واعادة تنسيقها والتأكد
من صحتها وانها ضمن النطاق المحدد في عملية الكشط 

يتم تمرير عدد الايام للجرف عند الاتصال بالكلاس
"""

class CheckDate:
    def __init__(self, last_days):
        self.max_day = date.today() 
        self.min_day= date.today() -  timedelta(days=int(last_days)) 

        self.month_mapping_1 = {
            'كانونالثاني': '01',
            'شباط': '02',
            'اذار': '03',
            'نيسان': '04',
            'ايار': '05',
            'حزيران': '06',
            'تموز': '07',
            'اب': '08',
            'ايلول': '09',
            'تشرينالاول': '10',
            'تشرينالثاني': '11',
            'كانونالاول': '12'    
                }

        self.month_mapping_2 = {
            'يناير': '01',
            'فبراير': '02',
            'مارس': '03',
            'ابريل': '04',
            'مايو': '05',
            'يونيو': '06',
            'يوليو': '07',
            'اغسطس': '08',
            'سبتمبر': '09',
            'اكتوبر': '10',
            'نوفمبر': '11',
            'ديسمبر': '12'}


    # دالة لفحص التواريخ اذا كانت ضمن النطاق المسموح بجرفه
    def check_article_date(self,published_date):
        try:
            print(published_date, self.max_day, self.min_day)
            if published_date <= self.max_day and published_date >= self.min_day:
                return False
            else:
                return True
        except Exception as e:
            print(e)
            return True

   
   # دالة لايقاف عملية الجرف في حال تخطينا النطاق المسموح به
    def check_brake_scriping(self,published_date):
        try:
            if published_date < self.min_day:
                return True
            else:
                return False
        except:
                return False


    #   #وظيفة لتحويل تاريخ نصي عربي الى نسق تاريخ منتظم
    def convert_text_date(self,text_date, format='d-m-y',):
        print(text_date)
        text_date = str(text_date)
        text_date = re.sub(r'\s+', ' ', text_date) 
        
        text_date = text_date.replace('ن ا', 'نا').replace('آ', 'ا').replace('أ', 'ا').replace(',','').replace('،','')
        text_date = text_date.strip()    
        text_date = text_date.replace(' ', '-')

        values = text_date.split('-')
        keys = format.split('-')
        parts = dict(zip(keys, values))

        day = parts.get('d', '')
        month = parts.get('m','')
        month = self.month_mapping_1.get(month) or self.month_mapping_2.get(month)
        year = parts.get('y', '')

        formatted_date_string = f"{year}-{month}-{day}"
        formatted_date = datetime.strptime(formatted_date_string, "%Y-%m-%d").date()
        print(formatted_date)
        return formatted_date



    def convert_arabic_date_sham(self,arabic_date):
        arabic_digits = "٠١٢٣٤٥٦٧٨٩"
        western_digits = "0123456789"
        translation_table = str.maketrans(arabic_digits, western_digits)
        arabic_date = arabic_date.translate(translation_table)
        return self.convert_text_date(arabic_date,'d-m-y')
       
    

    def extract_date_from_url(self,url):
        year_pattern = r'20\d{2}'
        match = re.search(year_pattern, url)
        if match:
            year = match.group()
            date = url[match.end():match.end()+6]
            return f'{year}{date}'
        else:
            return None