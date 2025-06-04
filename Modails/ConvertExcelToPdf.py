import os
import customtkinter as ctk
from tkinter import filedialog
import openpyxl as px
import xlwings as xw
from tkinter import messagebox
import threading



class ConverterXlsPdf(ctk.CTkScrollableFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stop_flag = False
        # قائمة لتخزين المتغيرات الخاصة بكل مجلد وملف
        self.folder_vars = []
        self.file_vars = []

        # حقل إدخال المجلد الأب
        self.folder_frame = ctk.CTkFrame(self)
        self.folder_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(self.folder_frame, text="Select Parent Folder:").pack(side="left")

        self.folder_entry = ctk.CTkEntry(self.folder_frame, width=300)
        self.folder_entry.pack(side="left", padx=10)

        self.folder_button = ctk.CTkButton(self.folder_frame, text="Browse", command=self.select_folder)
        self.folder_button.pack(side="left")

        # أزرار لتحديد وإلغاء تحديد جميع الملفات

        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.pack(fill="x", padx=10, pady=10)

        self.select_all_button = ctk.CTkButton(self.button_frame, text="Select All", command=self.select_all_files, width=75)
        self.select_all_button.pack(side="left", padx=5)

        self.deselect_all_button = ctk.CTkButton(self.button_frame, text="Deselect All", command=self.deselect_all_files, width=75)
        self.deselect_all_button.pack(side="left", padx=5)


        self.export_button = ctk.CTkButton(self.button_frame, text="Export to PDF", width=100,fg_color='#087246', command=self.start_convert)
        self.export_button.pack(side="left", padx=5)


        self.stop_command = ctk.CTkButton(self.button_frame, text="Stop",fg_color='#E44C4C',  width=50,command=self.stop_convert)
        self.stop_command.pack(side="right", padx=5)

        # إطار لعرض المجلدات والملفات
        self.root_frame = ctk.CTkScrollableFrame(self, width=580, height=500, border_width=2, corner_radius=1)
        self.root_frame.pack(padx=10, pady=10,ipadx=10, fill="both", expand=True)



    #وظيفة تحويل  مسار ملف الاكسل الى pdf
    def convert_selectd_path_to_pdf(self):
        """
        1- الحصول على مسارات الملفات المحددة
        2- إيقاف واجهة المستخدم أثناء المعالجة
        3- حساب عدد الأوراق في جميع ملفات الإكسل
        4- إنشاء شريط تقدم عام
        5- فتح كل ملف إكسل وتحويل كل ورقة إلى ملف PDF
        6- تحديث شريط التقدم بعد كل ورقة مكتملة
        7- إعادة تفعيل واجهة المستخدم بعد الانتهاء من المعالجة
        """
     
        excel_file_data = self.get_files_selected_path() # 1
        if len(excel_file_data)==0: 
            messagebox.showerror('Error','Please Select Files\nالرجاء اختيار ملفات لتحويلها اولا')
            return 
        
        self.off_wed() # 2
        count_papers=self.count_sheets_in_excel_files(excel_file_data) #3
        counter_completed_sheet =0
        counter_file=0

        Father_progress_bar = ctk.CTkProgressBar(self.button_frame, orientation="horizontal", height=8, width=50, mode="determinate",corner_radius = 3, progress_color='#4C9BE4')
        lable_Father_progress_bar=ctk.CTkLabel(self.button_frame, text='0%',font=("Bahnschrift", 20))
        Father_progress_bar.pack(padx=5, pady=10, fill="x",side="left", expand=True)
        Father_progress_bar.set(0)
        lable_Father_progress_bar.pack(padx=1, pady=4, fill="x",side="left", expand=True)
        
        #5
        for file_path in excel_file_data:
            file_path =file_path.replace(fr'\\','/')
            folder_path = os.path.dirname(file_path)
            file_name = os.path.basename(file_path)
            target_pdf_folder = fr'{folder_path}\PDF Files'
            if not os.path.exists(target_pdf_folder):
                os.makedirs(target_pdf_folder)
            try:
                if self.stop_flag:
                    try:
                        if 'workbook_pdf' in locals():
                            workbook_pdf.close()
                        app_pdf.quit()
                    except:pass
                    messagebox.showinfo('Stopped','تم ايقاف العملية')
                    return
                app_pdf = xw.App(visible=False)
                workbook_pdf = app_pdf.books.open(file_path)
                file_name = file_name.replace('.xlsx', '')
                # تحويل كل ورقة ضمن الملف المحدد لتحويل الى ملفات بي دي اف
                for sheet in workbook_pdf.sheets:
                    pdf_file = fr"{target_pdf_folder}\{file_name}_{sheet.name}.pdf"
                    sheet.to_pdf(pdf_file, show=False, quality='standard')
                    counter_completed_sheet+=1
                    Father_progress_bar.set(counter_completed_sheet/count_papers)
                    lable_Father_progress_bar.configure(text=f"{int(counter_completed_sheet/count_papers*100)}%")
                counter_file+=1
            except Exception as err: # اكسبشن لطباعة اي خطأ قد يحصل في هذه المرحلة وتوقف العملية
                print(err)
                break
            finally:
                try:
                    if 'workbook_pdf' in locals():
                        workbook_pdf.close()
                    app_pdf.quit()
                except:pass
        self.on_wed()    
        messagebox.showinfo("Done","Complete") 
    

    # وظيفة تشغيل الازار اثناء التنفيذ
    def on_wed(self):
        self.stop_command.configure(state="disabled")
        self.export_button.configure(state="normal")
        self.deselect_all_button.configure(state="normal")
        self.select_all_button.configure(state="normal")

    # وظيفة ايقاف الازار اثناء التنفيذ
    def off_wed(self):
        self.stop_command.configure(state="normal")
        self.export_button.configure(state="disabled")
        self.deselect_all_button.configure(state="disabled")
        self.select_all_button.configure(state="disabled")


    def stop_convert(self):
        self.stop_flag = True 
        self.on_wed()
    

    # وظيفة لبدء التنفيذ في خيط منفصل
    def start_convert(self):
        self.stop_flag = False
        self.thread = threading.Thread(target=self.convert_selectd_path_to_pdf)
        self.thread.start()
        

    # وظيفة لحساب عدد الأوراق في جميع ملفات الإكسل المحددة
    def count_sheets_in_excel_files(self,file_paths):
        counter=0
        for file_path in file_paths:
            try:
                workbook = px.load_workbook(file_path)
                sheet_names = workbook.sheetnames
                counter+=len(sheet_names)
            except:
                continue
        return counter

    # وظيفة لتبديل حالة تحديد الملفات داخل مجلد معين
    def toggle_files(self,folder_frame,folder_name, select_all):
        for widget in folder_frame.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                for file_checkbox in widget.winfo_children():
                    if isinstance(file_checkbox, ctk.CTkCheckBox):
                        file_name = file_checkbox.cget("text").lower()
                        folder_name=folder_name
                        if 'Processed_data'.lower() in file_name:
                            continue
                        file_checkbox.select() if select_all else file_checkbox.deselect()

    # وظيفة لتحديد أو إلغاء تحديد جميع الملفات في المجلدات
    def select_all_files(self):
        for folder_frame,folder_name, folder_var in self.folder_vars:
            folder_var.set(True)
            self.toggle_files(folder_frame,folder_name, True)


    # وظيفة لإلغاء تحديد جميع الملفات في المجلدات
    def deselect_all_files(self):
        for folder_frame,folder_name, folder_var in self.folder_vars:
            folder_var.set(False)
            self.toggle_files(folder_frame,folder_name, False)


    # وظيفة للحصول على مسارات الملفات المحددة
    """
    1- إنشاء قائمة فارغة لتخزين مسارات ملفات Excel المحددة
    2- التكرار عبر كل مجلد وملف
    3- التحقق من حالة الـ CheckBox لكل ملف
    4- إذا كان الـ CheckBox محددًا، إضافة مسار الملف الكامل إلى القائمة
    5- إرجاع قائمة مسارات الملفات المحددة
    """
    def get_files_selected_path(self):
        excel_file_data = [] #1
        for folder_frame,name,varname in self.folder_vars: #2
            for widget in folder_frame.winfo_children():
                if isinstance(widget, ctk.CTkFrame):
                    for file_checkbox in widget.winfo_children():
                        if isinstance(file_checkbox, ctk.CTkCheckBox):#3
                            file_var = file_checkbox.cget("variable")
                            # احصل على مسار ملف Excel باستخدام اسم المتغير النصي
                            for var, path_var in self.file_vars:
                                if var == file_var:
                                    file_excel_path = path_var.get()
                            if file_var.get():  # التحقق من حالة الـ CheckBox
                                excel_file_data.append(file_excel_path)  # إضافة مسار الملف الكامل   
        return excel_file_data #5



     # وظيفة لاختيار مجلد الأب
    def select_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.folder_entry.delete(0, ctk.END)
            self.folder_entry.insert(0, folder_path)
            self.list_folders_and_files(folder_path)

    # وظيفة لعرض المجلدات والملفات في واجهة المستخدم من المجلد الذي تم اختياره
    """
    1- مسح جميع العناصر الموجودة في root_frame
    2- إنشاء قاموس لتخزين المجلدات والملفات
    3- استخدام os.walk للبحث في المجلد المحدد عن ملفات Excel
    4- إنشاء واجهة مستخدم لكل مجلد وملف
    5- إضافة CheckBox لكل مجلد وملف
    6- عرض عدد الملفات في رسالة معلومات

    """
    def list_folders_and_files(self,folder_path):
        for widget in self.root_frame.winfo_children():
            widget.destroy()
        self.folder_dict = {}
        for root, dirs, files in os.walk(folder_path):
            excel_files = [f for f in files if f.endswith('.xlsx') or f.endswith('.xls')]
            if excel_files:
                self.folder_dict[root] = excel_files     
                
        for folder, files in self.folder_dict.items():
            folder_frame = ctk.CTkFrame(self.root_frame)
            folder_frame.pack(fill="x", padx=5, pady=10)

            self.folder_var = ctk.BooleanVar()
            self.folder_checkbox = ctk.CTkCheckBox(folder_frame, text=os.path.basename(folder), checkbox_height=25, checkbox_width=25,border_width=2,corner_radius=3,font=("Bahnschrift", 15),
                                            variable=self.folder_var, command=lambda var=self.folder_var,folder_name=folder, frame=folder_frame: self.toggle_files(frame,folder_name, var.get()))
            self.folder_checkbox.pack(anchor="w")
            self.folder_vars.append((folder_frame,folder, self.folder_var))

            file_list_frame = ctk.CTkFrame(folder_frame)
            file_list_frame.pack(fill="x", padx=20)

            for file in files:
                self.file_var = ctk.BooleanVar()
                self.file_excel_path=ctk.StringVar(value=os.path.join(folder, file))
                self.file_checkbox = ctk.CTkCheckBox(file_list_frame, text=file, variable=self.file_var, checkbox_height=20, checkbox_width=20,border_width=1,corner_radius=2,font=("Bahnschrift", 12))
                self.file_checkbox.pack(anchor="w", padx=4)
                self.file_vars.append((self.file_var, self.file_excel_path))
        
        count_files=len(self.file_vars)
        messagebox.showinfo('Done',f'Total Files {count_files}')