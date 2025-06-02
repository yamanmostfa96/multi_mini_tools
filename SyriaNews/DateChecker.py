from datetime import datetime,timedelta, date



class CheckDate:
    def __init__(self, last_days):
        self.max_day = date.today()
        self.min_day= date.today() -  timedelta(days=int(last_days)) 

    # دالة لفحص التواريخ
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

   
    def check_brake_scriping(self,published_date):
        try:
            if published_date < self.min_day:
                return True
            else:
                return False
        except:
                return False

    # Mapping of Arabic to English month names
    month_mapping = {
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
    
    month_mapping_eg = {
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

    
    def stamp_date_arabic(self,arabic_date):
        arabic_date= arabic_date.replace('ن ا','نا').replace('آ','ا').replace('أ','ا')
        return arabic_date


    def convert_arabic_date(self,arabic_date):
        try:
            arabic_date = self.stamp_date_arabic(arabic_date)
            arabic_date= arabic_date.replace(' ','-')
            day, arabic_month, year = arabic_date.split('-')
            month = self.month_mapping.get(arabic_month, '')
            formatted_date_string = f"{year}-{month}-{day}"
            formatted_date = datetime.strptime(formatted_date_string, "%Y-%m-%d")
        except:
            formatted_date = datetime.strptime('1900-1-1', "%Y-%m-%d")
        return formatted_date.date()
    
    # دالة خاصة بتواريخ عنب بلدي
    def convert_arabic_date_enab(self,arabic_date):
        arabic_date = self.stamp_date_arabic(arabic_date)
        arabic_date =  arabic_date.replace(' ','-')
        arabic_month, day, year = arabic_date.split('-')
        month = self.month_mapping_eg.get(arabic_month, '')
        formatted_date_string = f"{year}-{month}-{day}"
        try: formatted_date = datetime.strptime(formatted_date_string, "%Y-%m-%d").date()
        except: formatted_date = '1900-1-1'
        return  formatted_date
    

    def convert_arabic_date_athar(self,arabic_date):
        arabic_date = self.stamp_date_arabic(arabic_date)
        arabic_date =  arabic_date.replace(' ',',').replace(',,',',')
        arabic_month, day, year = arabic_date.split(',')
        month = self.month_mapping_eg.get(arabic_month, '')
        formatted_date_string = f"{year}-{month}-{day}"
       
        try: formatted_date = datetime.strptime(formatted_date_string, "%Y-%m-%d").date()
        except: formatted_date = '1900-1-1'
        return  formatted_date


    def convert_arabic_date_sham(self,arabic_date):
        arabic_digits = "٠١٢٣٤٥٦٧٨٩"
        western_digits = "0123456789"
        translation_table = str.maketrans(arabic_digits, western_digits)
        arabic_date = arabic_date.translate(translation_table)
        arabic_date = self.stamp_date_arabic(arabic_date)
        arabic_date =  arabic_date.replace(' ',',').replace(',,',',')
        day,arabic_month,year = arabic_date.split(',')
        month = self.month_mapping_eg.get(arabic_month, '')
        formatted_date_string = f"{year}-{month}-{day}"
        try: formatted_date = datetime.strptime(formatted_date_string, "%Y-%m-%d").date()
        except: formatted_date = '1900-1-1'
        return  formatted_date
    
    def convert_arabic_date_horanfree(self,arabic_date):
        try:
            arabic_date = self.stamp_date_arabic(arabic_date)
            arabic_date= arabic_date.replace(' ','-')
            day, arabic_month, year = arabic_date.split('-')
            month = self.month_mapping_eg.get(arabic_month, '')
            formatted_date_string = f"{year}-{month}-{day}"
            formatted_date = datetime.strptime(formatted_date_string, "%Y-%m-%d")
        except:
            formatted_date = datetime.strptime('1900-1-1', "%Y-%m-%d")
        return formatted_date.date()

    def convert_arabic_date_akh(self,arabic_date):
        arabic_date = self.stamp_date_arabic(arabic_date)
        arabic_date =  arabic_date.strip().replace(' ','-')
        arabic_month, day, year = arabic_date.split('-')
        month = self.month_mapping_eg.get(arabic_month, '')
        formatted_date_string = f"{year}-{month}-{day}"
        try: formatted_date = datetime.strptime(formatted_date_string, "%Y-%m-%d").date()
        except: formatted_date = '1900-1-1'
        return  formatted_date
# END:: CheckDate  ____________________________