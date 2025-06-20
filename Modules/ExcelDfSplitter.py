import pandas as pd 
import customtkinter as ctk
import openpyxl as px
import os
import threading
from tkinter import filedialog, messagebox, Toplevel, Button, ttk
from openpyxl.worksheet.table import TableStyleInfo


from Modules.table import Table as tb # استدعاء كلاس اظهار الجدول على الشاشة


class ExcellSplitter(ctk.CTkScrollableFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


        self.filepath =''
        self.general_data_frame=''
        self.datasheet=None


        self.create_widgets() # الاتصال بوظيفة بناء الواجهة الرسومية


    # وظيفة بناء الواجهة الرسومية:
    def create_widgets(self):
        self.first_step_frame=ctk.CTkFrame(self, border_width=1, corner_radius=1,height=50)
        self.first_step_frame.pack(fill="x", padx=10, pady=10)

        self.select_file_button = ctk.CTkButton(self.first_step_frame, text="Browse Excel File",
                                        font=('Segoe UI Semibold',14), 
                                        command=self.select_excel_file, width=300, height=30)
        
        self.select_file_button.pack(side="left", padx=2, pady=2, anchor='w', fill="x")


        self.first_step_frame.pack_propagate(False) # منع تغيير حجم الإطار بناءً على المحتوى


        self.data_sheet_frame=ctk.CTkFrame(self, border_width=0.1)


        ctk.CTkLabel(self.data_sheet_frame, text='Select Sheet From File',height=20,
                     corner_radius=1,width=200,font=('Segoe UI Semibold',14),
                     anchor='ne', compound='left',justify='left').grid(row=0, column=0, pady=2, padx=0)


        self.sheet_name = ctk.CTkComboBox(self.data_sheet_frame, values=[], width=200, justify='left',
                             command=self.define_data_frame_and_update_data_sheet)
        self.sheet_name.grid(row=0, column=1, pady=2)


        ctk.CTkLabel(self.data_sheet_frame, text='Select Column to Split Data',
                     height=20,corner_radius=1,width=200,font=('Segoe UI Semibold',14),
                     anchor='ne', compound='left',justify='left' ).grid(row=0, column=2, pady=2, padx=0)


        self.column_name=ctk.CTkComboBox(self.data_sheet_frame, values=[], width=200, justify='left',
                                          command=self.update_count_files_in_screen)
        self.column_name.grid(row=0, column=3, pady=2)


        self.total_file_to_create=ctk.CTkLabel(self.data_sheet_frame, text='',
                     width=100,font=('Segoe UI Semibold',14),
                     anchor='ne', compound='left',justify='left')
        self.total_file_to_create.grid(row=0, column=5, pady=2)


        self.Split_and_save_results_btn=ctk.CTkButton(self.data_sheet_frame, text="Split and Save Results",
                                                      font=('Segoe UI Semibold',14),fg_color='green',
                                                      command=self.save_results, width=300, height=20)
        self.Split_and_save_results_btn.grid(row=0, column=6, pady=2, padx=20)

        

    def update_count_files_in_screen(self, col=None):

        self.count_files_to_sp = self.general_data_frame[self.column_name.get()].unique().tolist()
        self.total_file_to_create.configure(text=f'{len(self.count_files_to_sp)} Files ')


    
# operations functions:___  العمليات على البيانات  _____________

    # وظيفة اختيار ملف Excel:

    def select_excel_file(self):
        """"
        1- اختيار ملف Excel من خلال نافذة حوار.
        2- تفعيل فريم الجدول
        3- قراءة أسماء الأوراق في الملف وتحديث قائمة الاختيار.
        4- تحديث الكومبوكس الخاص بأسماء الأعمدة بناءً على الورقة المحددة.
        5- تحديد الورقة الأولى بشكل افتراضي.
        6- استدعاء الدالة لتحديث البيانات في الجدول بناءً على الورقة المحددة.
        7- اكسبشن لاظهار خطأ برسالة وايقاف العملية
        """
        self.filepath = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")]) 
        if self.filepath:
            try:
                self.data_sheet_frame.pack(fill="x", padx=5, pady=10)
                self.sheet_names = pd.ExcelFile(self.filepath).sheet_names
                self.sheet_name.configure(values=self.sheet_names)
                self.sheet_name.set(self.sheet_names[0])
                self.define_data_frame_and_update_data_sheet(self.sheet_name.get())
            except Exception as e:
                messagebox.showerror('Error', f'حصل الخطأ التالي: {e}')
                return
           

    # وظيفة تعريف DataFrame وتحديث ورقة البيانات:
    def define_data_frame_and_update_data_sheet(self, sheet_name):
        """
            1-ازالة جدول البيانات من الشاشة في حال كان موجود سابقا والغاء تعريف المتغير الذي يحمله
            2- تعريف متغير عام لحمل بيانات الورقة المحددة
            3- حذف الصفوف الفارغة من الداتا فريم
            4- استبدال القيم الفارغة بلاشيئ
            5- تخزين عنواين الداتا فريم ضمن قائمة نصية
            6- تحديث الكومبوكس باسماء الاعمدة
            7- تعيين القيمة الافتراضية باول عمود للكومبوكس
            8- اذا لم يكن جدول البيانات للعرض مجهز فيتم تجهيزه
            9- تعيين بيانات الجدول من خلال نسخ بيانات العامة المعرفة
            10- تحميل البيانات الى الجدول لعرضها على الشاشة
            11- عرض الجدول في الفريم الخاص به
            12- اكسبشن لاظهار خطأ برسالة وايقاف العملية
            tb: هو كلاس مخصص لعرض البيانات في شكل جدول، وهو مستورد من ملف table.py
            
        """
        try:
            try:
                self.datasheet.pack_forget()
            except:
                pass
            self.datasheet=None
            self.general_data_frame = pd.read_excel(self.filepath, sheet_name=sheet_name, dtype=str)
            self.general_data_frame.dropna(how='all')
            self.general_data_frame.replace(pd.NA,'', inplace=True)
            columns_list = [str(col) for col in self.general_data_frame.columns] 
            self.column_name.configure(values=columns_list)
            self.column_name.set(columns_list[0])

            self.count_files_to_sp = self.general_data_frame[columns_list[0]].unique().tolist()
            

            if not self.datasheet:
                    self.datasheet = tb(self,dataframe=self.general_data_frame,with_filter=0,
                                        with_sorter=0, with_index=1,on_update_callback=0)
            
            self.datasheet.data=self.general_data_frame.copy()
            self.datasheet.load_data()
            self.datasheet.pack(side='top',fill="x", padx=5,pady=5,anchor='n')

            self.total_file_to_create.configure(text=f'{len(self.count_files_to_sp)}  Files ')
   
        except Exception as e:
           messagebox.showerror('Error', f'حصل الخطأ التالي: {e}')
    



    # وظيفة حفظ النتائج:
    def save_results(self):
        self.target_folder=filedialog.askdirectory(title='حدد مجلد المخرجات')
        
        if self.target_folder:
            """
            في حال تحديد مجلد مخرجات يتم بناء واجهة على الشاشة تحتوي بروغريس بار لقياس
            التقدم في عملية الحفظ، وزر لإيقاف العملية في حال الحاجة لذلك.
            """
            self.progress_window = Toplevel(self)
            self.progress_window.title("جاري حفظ الملفات")
            self.progress_window.geometry("300x120")
            self.progress_window.focus_force()
            self.progress_window.grab_set()
            self.progress_label = ttk.Label(self.progress_window, text="جاري الحفظ...")
            self.progress_label.pack(pady=5)
            self.progress_bar = ttk.Progressbar(self.progress_window, length=250, mode="determinate")
            self.progress_bar.pack(pady=5)
            self.stop_process = False
            # وظيفة داخلية للايقاف
            def stop_saving():
                self.stop_process = True
                self.progress_label.config(text="جارٍ الإيقاف...")

            stop_button = Button(self.progress_window, text="إيقاف", command=stop_saving)
            stop_button.pack(pady=5)
            # بدء عملية الحفظ في خيط منفصل لتجنب تجميد الواجهة
            threading.Thread(target=self.save_task, daemon=True).start()

    # وظيفة فريعة لحفظ المخرجات والتي يتم استدعاءها من وظبفة الحفظ الاساسية
    def save_task(self):
            try:
                """
                1- نسخ البيانات العامة للورقة التي تم اختيارها
                الحصول على قائمة فريدة بالقيم للعمود الذي تم اختياره للفصل على اساسه.2-
                3- تعيين الحد الأقصى للبروغريس بار إلى عدد الملفات التي سيتم حفظها.
                4- حلقة تكرار لكل قيمة فريدة من العمود
                5- تحديد اسم الملف وفقا لاسم القيمة مع تنظيفها
                6- تصفية البيانات وفقا لهذه القيمة
                7- استدعاء دالة حفظ البيانات المفلترة في ملف جديد
                8- تحديث شريط التقدم
                9- اكسبشن لعرض خطأ 
                10- اغلاق النافذة عند الانتهاء
                """
                df = self.general_data_frame.copy()
                column_for_split = df[self.column_name.get()].unique().tolist()
                
                total_files = len(column_for_split)
                self.progress_bar["maximum"] = total_files 
                
                for index, value in enumerate(column_for_split):
                    if self.stop_process:
                        self.progress_label.config(text="تم الإيقاف")
                        return
                    file_name = str(value).replace('/', '_').replace('\\', '_').replace(':', '_')
                    file_name=file_name[0:50]
                    df_filtered = df[df[self.column_name.get()] == value]
                    self.save_file_as_file(self.target_folder, file_name, df_filtered)
                    self.progress_bar["value"] = index + 1 
                    self.progress_window.update_idletasks()  
                messagebox.showinfo("Success", "تم حفظ الملفات بنجاح")
            except Exception as e:
                messagebox.showerror("Error", f"حصل الخطأ التالي: {e}")
            finally:
                self.progress_window.destroy()  # إغلاق نافذة التقدم بعد انتهاء العملية
        
         


    # وظيفة انشاء جدول في ورقة الاكسل
    def create_table(self,table_name, worksheet):
                table_style ='TableStyleMedium17'
                table = px.worksheet.table.Table(displayName=table_name, ref=worksheet.dimensions)
                table.tableStyleInfo = TableStyleInfo(name=table_style, showFirstColumn=False,
                showLastColumn=False, showRowStripes=True, showColumnStripes=False)
                worksheet.add_table(table)
    

    # وظيفة حفظ البيانات الى ملف اكسل جديد في المجلد الخاص به
    def save_file_as_file(self,target_folder, file_name, df):
        """
        taget_folder: هو المجلد الذي سيتم حفظ الملفات فيه.
        file_name: هو اسم الملف الذي سيتم حفظ البيانات فيه.
        df: هو DataFrame الذي يحتوي على البيانات التي سيتم حفظها.

        1- انشاء مجلد فرعي داخل المجلد الاب في حال لم يكن موجود
        2- تحديد مسار ملف الاكسل 
        3-  فتح ملف الاكسل باستخدام باندا و اوبن باي اكسل وحفظ المخرجات اليه ضمن محاول واكسبشن
        """
        self.son_folder = os.path.join(target_folder, 'Outputs_Splite_Files')
        os.makedirs(self.son_folder, exist_ok=True) 

        Excel_target = os.path.join(self.son_folder, f'{file_name}.xlsx')
        
        try:
            with pd.ExcelWriter(Excel_target, engine='openpyxl', mode='w') as writer:
                    df.to_excel(writer, index=False, sheet_name='Result')
                    try:
                        self.create_table(table_name='Result', worksheet=writer.sheets['Result'])
                    except Exception as e:
                        print(f"⚠️ تحذير: فشل إنشاء الجدول - {e}")
        except Exception as e:
                print(f"❌ خطأ في حفظ الملف {Excel_target}: {e}")
               
