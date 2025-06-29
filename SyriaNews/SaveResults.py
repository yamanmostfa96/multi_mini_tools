import pandas as pd
import openpyxl as px
from openpyxl.worksheet.table import Table, TableStyleInfo
from difflib import SequenceMatcher
from datetime import datetime
import os
from pathlib import Path
from tkinter import messagebox
import time


"""
كلاس لحفظ المخرجات الى ملف اكسل


"""

class SaveResults_Excel:
        def __init__(self):
            self.date_time= datetime.now().strftime("%d-%m-%Y")
        
        
        
        # وظيفة لحذف ورقة من ملف اكسل من خلال تمرير رابط ملف الاكسل واسم الورقة
        def remove_sheet(self, excel_file, sheet_name):
            wb = px.load_workbook(excel_file)
            if sheet_name in wb.sheetnames:
                wb.remove(wb[sheet_name])
            wb.save(excel_file)
        


       # وظيفة لحذف تكرار المحتوى بسبب عملية جرف المحتوى
        def rmove_duplecte_contatint(self,data_frame):
            """
            تمرير وسيط داتا فريم
            تعيد بيانات فريم بعد إزالة التكرارات الكبيرة في النصوص

            لماذا تم استخدام هذه الوظيفة:

            بسبب ان معظم المواقع اثناء جرف المحتوى تقوم بتكرير عبارات ضمن كل خبر مثل اعلانات او تعليقات او عناوين اخبار اخرى
            وهذه النصوص تعتبر حشو لا لزمة له
            
            """
            final_data = pd.DataFrame(data_frame)


            # وظيفة للعثور على الجزء المشترك بين نصين
            def find_common_part(text1, text2):
                """
                1-matcher  يستخدم مكتبة SequenceMatcher للعثور على الجزء المشترك بين نصين
                2- إذا كان حجم الجزء المشترك أكبر من 100 حرف، يتم إرجاع هذا الجزء
                3- إذا لم يكن هناك جزء مشترك كبير، يتم إرجاع None
                 هذه الوظيفة تستخدم في معالجة النصوص للتخلص من التكرارات الكبيرة
                """
                matcher = SequenceMatcher(None, text1, text2)
                match = matcher.find_longest_match(0, len(text1), 0, len(text2))
                if match.size > 100:
                    return text1[match.a: match.a + match.size]
                else:
                    return None
            try:
                """
                حلقة لتكرار كل صف في الداتا فريم ومقارنة النصوص
                1- يتم استخدام find_common_part للعثور على الجزء المشترك بين النصوص
                2- إذا كان هناك جزء مشترك، يتم استبداله بمسافة فارغة في النصوص الأخرى
                3- يتم تقليم النصوص إلى 32000 حرف بعد إزالة الأجزاء المشتركة
                4- هذا يساعد في تقليل التكرارات الكبيرة في النصوص
                5- يتم استخدام try-except للتعامل مع أي استثناءات قد تحدث أثناء العملية
                """
                for index_, row_ in final_data.iterrows():
                    current_text = row_['content_text']
                    for index, row in final_data.iterrows():
                        if index == index_:
                            continue
                        other_text = row['content_text']
                        if current_text != other_text:
                            common_part = find_common_part(current_text, other_text)
                            if common_part:
                                final_data['content_text'] = final_data['content_text'].str.replace(common_part, '  ')
                                if len(final_data['content_text']):
                                    final_data['content_text'] = final_data['content_text'][:32000]
            except:
                return final_data
            return final_data
        



       #وظيفة انشاء تنسيق جدول للبيانات التي تم اضافتها الى ملف الاكسل
        def create_table(self,table_name, worksheet):
                table_style ='TableStyleMedium18'
                table = px.worksheet.table.Table(displayName=table_name, ref=worksheet.dimensions)
                table.tableStyleInfo = TableStyleInfo(name=table_style, showFirstColumn=False,
                showLastColumn=False, showRowStripes=True, showColumnStripes=False)
                worksheet.add_table(table)


        #وظيفة حفظ المخرجات الى ملف اكسل
        def save_result(self, dataframe=[], folder_path=None):
            empty_df = pd.DataFrame()
            self.son_folder = f'{folder_path}\Result {self.date_time}'
            excel_file_result = f'{self.son_folder}\\Result File.xlsx'
            
            if not Path(excel_file_result).exists():
                os.makedirs(self.son_folder, exist_ok=True)
               
                with pd.ExcelWriter(excel_file_result, engine='openpyxl') as writer:
                    empty_df.to_excel(writer, index=False)
            try:
                final_data=self.rmove_duplecte_contatint(dataframe)
                writer = pd.ExcelWriter(excel_file_result, engine='openpyxl', mode='w')
                workbook = writer.book
                final_data.to_excel(writer, index=False, sheet_name='Result')
                worksheet_= workbook['Result']
                try:
                    self.create_table(table_name='Result', worksheet=worksheet_)
                except:
                    pass
                workbook.save(excel_file_result)

                ask_open = messagebox.askyesno('تم', 'هل تريد فتح الملف؟')
           
                if ask_open: # فتح الملف 
                    if os.name == "nt":  
                        os.startfile(excel_file_result)
                        
            except Exception as e:
                print(e)
                messagebox.showerror('حدث خطأ غير متوقع اثناء حفظ المخرجات',f'\n{e}\n')
            time.sleep(1)
        