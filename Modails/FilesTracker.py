import os
import customtkinter as ctk
import pandas as pd
from datetime import datetime
import shutil
from tkinter import filedialog, messagebox, Tk, ttk
import threading
from docx import Document  
import comtypes.client
from PIL import Image
import urllib.parse
import xlwings as xw
import openpyxl as px
import zipfile



from Modails.table import Table as tb


class FilesTracker(ctk.CTkScrollableFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.main_face() # استدعاء وظيفة بناء الواجهة الرسومية
    

 
    # تحميل الصور من المسار
    def load_image_from_path(self, image_path, size=(20, 20)):
        try:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"File not found: {image_path}")

            image = Image.open(image_path)
            return ctk.CTkImage(light_image=image, dark_image=image, size=size)

        except FileNotFoundError:
            default_image = Image.new("RGB", size, color="gray")
            return ctk.CTkImage(light_image=default_image, dark_image=default_image, size=size)
    
    
    
    
    #الواجهة
    def main_face(self):


        self.selector_frame=ctk.CTkFrame(self, height=20,width=500, border_color='white', border_width=1, corner_radius=1)
        self.selector_frame.pack(fill="x", padx=5,pady=5)

        self.folder_Browes_button = ctk.CTkButton(self.selector_frame,width=150, text="Browse Folder", command=self.select_folder)
        self.folder_Browes_button.pack(side="left", padx=5,pady=5)

        self.total_files=ctk.CTkLabel(self.selector_frame, text='',font=('Bahnschrift',17))

        self.export_data_to_excel_file = ctk.CTkButton(self.selector_frame,width=100,fg_color='#54045e',
                                                    text="Export Tracker To Excel", command=self.export_trac_to_excel)

        self.data_sheet_frame=ctk.CTkFrame(self, height=350,width=700, border_color='white', border_width=1, corner_radius=1)

        self.operation_btns=ctk.CTkFrame(self, height=100,width=700, border_color='white', border_width=1, corner_radius=1)


        self.copy_file_to_folder=ctk.CTkButton(self.operation_btns,width=100,height=50,font=('Bahnschrift',13),
                                                image=self.load_image_from_path(fr"Icons\CopyfilesToFolder.png",(50,50)),compound="top",
                                                corner_radius=0,fg_color="transparent",bg_color="transparent", hover_color="#9588ba",border_width=0,
                                                text="Copy Files to Folder", command=self.copy_files_to_folder)
        self.copy_file_to_folder.grid(row=0, column=0, padx=5, pady=5)


        self.convert_doc_to_pdf=ctk.CTkButton(self.operation_btns,width=100,height=50,font=('Bahnschrift',13),
                                              image=self.load_image_from_path(fr"Icons\convert_doc_to_pdf.png",(75,50)), compound="top",
                                              corner_radius=0,fg_color="transparent",bg_color="transparent", hover_color="#9588ba",border_width=0,
                                              text="Convert Word To PDF", command=self.convert_docs_to_pdf)
        self.convert_doc_to_pdf.grid(row=0, column=1, padx=5, pady=5)


        self.convert_xlsx_to_pdf=ctk.CTkButton(self.operation_btns,width=100,height=50,font=('Bahnschrift',13),
                                              image=self.load_image_from_path(fr"Icons\ExcelToPdf.png",(75,50)), compound="top",
                                              corner_radius=0,fg_color="transparent",bg_color="transparent", hover_color="#9588ba",border_width=0,
                                              text="Convert Excel To PDF", command=self.conver_xlsx_to_pdf)
        self.convert_xlsx_to_pdf.grid(row=0, column=3, padx=5, pady=5)


        self.zepper_btn=ctk.CTkButton(self.operation_btns,width=100,height=50,font=('Bahnschrift',13),
                                              image=self.load_image_from_path(fr"Icons\zip_files.png",(50,50)), compound="top",
                                              corner_radius=0,fg_color="transparent",bg_color="transparent", hover_color="#9588ba",border_width=0,
                                              text="Compress Files by zipper", command=self.ziper_files)
        self.zepper_btn.grid(row=0, column=4, padx=5, pady=5)






    # العمليات -------------------


    # وظيفة اختيار مجلد 
    def select_folder(self):
        folder_path= filedialog.askdirectory()
        if folder_path:
            #try:
                self.total_files.pack(side="left", padx=5,pady=5)
                self.export_data_to_excel_file.pack(side="left", padx=5,pady=5)
                row_data= self.get_file_info(folder_path)
                self.files_tracker_data=pd.DataFrame(row_data)
                self.define_data_frame_and_update_data_sheet()
                messagebox.showinfo('Done','تم جمع معلومات الملفات في المجلد المحدد')
            #except Exception as e:
            #    messagebox.showerror('Error',f'حصل الخطأ التالي {e}')
            #    return


    # تعريف البيانات وتحديث جدول العرض
    def define_data_frame_and_update_data_sheet(self):
            try:
                if hasattr(self, 'datasheet'):
                    self.datasheet.destroy()
                self.operation_btns.pack_forget()
            except:pass

            self.data_sheet_frame.pack(fill="x", padx=5,pady=5)
            self.operation_btns.pack(fill="x", padx=5,pady=5)

            df=self.files_tracker_data

            self.datasheet =tb(self.data_sheet_frame,df,columns_width=[500,200,150,150,150,600],
                                align_center=[2] ,on_update_callback=self.update_total_files)
            
            self.datasheet.pack(fill="x", padx=5,pady=5)
            self.datasheet.load_data()
            self.df_filtered=df.copy()


    # وظيفة لتحديث عدد الملفات الموجودة بالجدول
    def update_total_files(self,count):
        self.total_files.configure(text=f'Count Files: {count}')
    

    # وظيفة للحصول على معلومات الملفات من المجلد المحددوتخزينها بقاموس
    def get_file_info(self,directory):
        file_info_dict = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                if '$RECYCLE.BIN' in file_path: # تخطي الملفات المحذوفة من المجلد
                    continue
                file_size = os.path.getsize(file_path) 
                file_creation_time = os.path.getctime(file_path) 
                file_extension = os.path.splitext(file)[1]
                creation_time_readable = datetime.fromtimestamp(file_creation_time).strftime('%Y-%m-%d %H:%M:%S')
                
                file_info_dict.append({
                    'File Name':file,
                    'Folder Name':os.path.basename(root) ,
                    'Extension': str(file_extension).replace('.',''),
                    'size': self.converter_size(file_size),
                    'Creation Time': creation_time_readable,
                    'Full Path': file_path})
        return file_info_dict
    

    # وظيفة لإنشاء جدول في ملف Excel
    def create_table(self,table_name, worksheet):
        from openpyxl.worksheet.table import TableStyleInfo
        table_style ='TableStyleMedium18'
        table = px.worksheet.table.Table(displayName=table_name, ref=worksheet.dimensions)
        table.tableStyleInfo = TableStyleInfo(name=table_style, showFirstColumn=False,
        showLastColumn=False, showRowStripes=True, showColumnStripes=False)
        worksheet.add_table(table)

    # وظيفة لتصدير البيانات إلى ملف Excel
    def export_trac_to_excel(self):
        import subprocess
        ask_folder_target = filedialog.askdirectory(title="اختر المجلد لحفظ ملف Excel")
        if not ask_folder_target:
            return
        excel_file_result = f'{ask_folder_target}\\Results_Tracker_myFiles.xlsx'
       
        try:
            writer = pd.ExcelWriter(excel_file_result, engine='openpyxl', mode='w')
            workbook = writer.book
            self.datasheet.data.to_excel(writer, index=False, sheet_name='Result')
            worksheet= workbook['Result']
            try:
                self.create_table(table_name='Result', worksheet=worksheet)
            except:pass
            workbook.save(excel_file_result)
            ask_open = messagebox.askyesno('تم', 'تم استخراج التراكر إلى ملف Excel باسم "Results_Tracker_myFiles.xlsx"\nهل تريد فتح الملف؟')
           
            if ask_open: # فتح الملف بعد الاستخراجس
                if os.name == "nt":  
                    os.startfile(excel_file_result)
                elif os.name == "posix":
                    subprocess.run(["xdg-open" if "linux" in os.uname().sysname.lower() else "open", excel_file_result])
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء حفظ الملف:\n{e}")
    


    # وظيفة لتحويل حجم الملف الى تنسيق مقروء
    def converter_size(self, size):
        size = int(size)

        if size >= 1024**3:
            return str(round(size / 1024**3, 2)) + ' GB'
        
        elif size >= 1024**2:
            return str(round(size / 1024**2, 2)) + ' MB'
        
        elif size >= 1024:
            return str(round(size / 1024, 1)) + ' KB'
    
        else:
            return str(size) + ' Bytes'


    # وظيفة لإيقاف تنفيذ العمليات الجارية
    def stop_command(self):
        self.stop_command_pool=True


    # وظيفة لفتح نافذة التقدم وتشغيل الوظيفة الداخلية ضمن خيط منفصل
    def run_progress_par_with_operation(self,title,target, args):
        self.stop_command_pool=False
        self.progress_window = Tk()
        self.progress_window.title(title)
        self.progress_window.geometry("400x200")  
        self.progress_window.resizable(False, False)

        progress_label = ttk.Label(self.progress_window, text="Runings...")
        progress_label.pack(padx=10, pady=5)

        self.progress_bar = ttk.Progressbar(self.progress_window, length=300, mode="determinate")
        self.progress_bar.pack(padx=10, pady=5)

        self.information_progress = ttk.Label(
        self.progress_window, text="", anchor='w', justify='left', 
        font=('Segoe UI',10))
        self.information_progress.pack(fill='x', padx=10, pady=5) 

        stop_button = ctk.CTkButton(self.progress_window, text="Stop", 
                                    command=self.stop_command, width=75, corner_radius=4, fg_color='red')
        stop_button.pack(pady=10)
        threading.Thread(target=target, args=args).start()
        self.progress_window.mainloop()



    # وظيفة اب لنسخ ملفات الى مجلد معين
    def copy_files_to_folder(self):
        target_folder = filedialog.askdirectory(title="Select Target Folder")
        if target_folder:
            path_data = self.datasheet.data.copy()
            path_list = path_data['Full Path'].to_list()
            self.run_progress_par_with_operation("Copy Progress",self.copy_files_thread,args=(target_folder,path_list) )

    # وظيفة فرعية لنسخ الملفات
    def copy_files_thread(self, target_folder, path_list):
        total_files = len(path_list)
        for index, file_path in enumerate(path_list):
            if self.stop_command_pool:break
            file_name = os.path.basename(file_path)
            target_path = os.path.join(target_folder, file_name)
            counter = 1
            while os.path.exists(target_path):
                name, extension = os.path.splitext(file_name)
                target_path = os.path.join(target_folder, f"{name}_{counter}{extension}")
                counter += 1
            try:
                self.information_progress.configure(text=f'File Name: {file_name}\n {index+1} Out of {total_files}')
                shutil.copy(file_path, target_path)
            except Exception as e:
                print(f"Error copying {file_name}: {e}")
            self.progress_bar['value'] = (index + 1) / total_files * 100
            self.progress_window.update_idletasks()
        if self.stop_command_pool:
            messagebox.showinfo("Stopped", "File copy operation was stopped.")
        else:
            messagebox.showinfo("Completed", "All files have been copied successfully.")
        self.progress_window.destroy()

  

    # وظيفة لتحويل ملفات Word إلى PDF
    def convert_docs_to_pdf(self):
        path_data = self.datasheet.data.copy()  
        path_data_filtered = path_data[path_data['Extension'].str.lower().isin(['doc', 'docx'])]
        if path_data_filtered.shape[0]==0:
            messagebox.showinfo("تنويه",f'لا يوجد ملفات ورد في القائمة لتحويلها')
            return
        else:
            ask_yes= messagebox.askyesno("رسالة",f"تم ايجاد {path_data_filtered.shape[0]} ملفا قابل للتحويل، هل تريد تحويلها الى pdf")
        if not ask_yes:
            return
        target_folder = filedialog.askdirectory(title="Select Target Folder")
        if target_folder:
            
            path_list = path_data_filtered['Full Path'].to_list()
            self.run_progress_par_with_operation("Converts Word To PDF",self.convert_doc_to_pdf_thread,args=(target_folder,path_list) )


    # وظيفة فرعية لتحويل ملفات Word إلى PDF في خيط منفصل
    def convert_doc_to_pdf_thread(self, target_folder, path_list):
        total_files = len(path_list)
        for index, file_path in enumerate(path_list):

            if self.stop_command_pool:break
            file_path = urllib.parse.unquote(file_path)
            file_name = os.path.basename(file_path)
            name, extension = os.path.splitext(file_name)
            if extension.lower() == '.docx' or extension.lower() =='.doc':
                target_path = os.path.join(target_folder, f"{name}.pdf") 
                counter = 1
                while os.path.exists(target_path):
                    target_path = os.path.join(target_folder, f"{name}_{counter}.pdf")
                    counter += 1  
                try:
                    self.information_progress.configure(text=f'File Name: {file_name}\n {index+1} Out of {total_files}')
                    self.convert_single_doc_to_pdf(file_path, target_path)
                except Exception as e:
                    print(f"Error converting {file_name}: {e}")
            self.progress_bar['value'] = (index + 1) / total_files * 100
            self.progress_window.update_idletasks()

        if self.stop_command_pool:
            messagebox.showinfo("Stopped", "Document conversion was stopped.")
        else:
            messagebox.showinfo("Completed", "All documents have been successfully converted to PDF.")
        
        self.progress_window.destroy()


    # وظيفة فرعية لفتح ملف ورد وتحويله الى بي دي اف لاستخدماه بوظيفة التحويل
    def convert_single_doc_to_pdf(self, doc_path, pdf_path):
        try:
            doc_path=str(doc_path).replace("/","\\")
            word = comtypes.client.CreateObject('Word.Application')
            word.Visible = False
            doc = word.Documents.Open(doc_path)
            doc.SaveAs(pdf_path, FileFormat=17)
            doc.Close()
            word.Quit()
        except Exception as e:
            print(f"Error converting {doc_path}: {e}")
            try:
                doc.Close()
            except:
                pass 
            try:
                word.Quit()
            except:
                pass 
    


    # وظيفة اب لتحويل ملفات الاكسل الى بي دي اف
    def conver_xlsx_to_pdf(self):
        path_data = self.datasheet.data.copy()  
        path_data_filtered = path_data[path_data['Extension'].str.lower().isin(['xls', 'xlsx'])]
        if path_data_filtered.shape[0]==0:
            messagebox.showinfo("تنويه",f'لا يوجد ملفات ورد في القائمة لتحويلها')
            return
        else:
            path_list = path_data_filtered['Full Path'].to_list()
            
            ask_yes= messagebox.askyesno("رسالة",f"تم ايجاد {len(path_list)} ملفا قابل للتحويل  هل تريد تحويلها")
        if not ask_yes:
            return
        target_folder = filedialog.askdirectory(title="Select Target Folder")
        if target_folder:
            self.run_progress_par_with_operation("Converts Excel Files To PDF",self.convert_xlsx_to_pdf_thread,args=(target_folder,path_list) )
    

    # وظيفة لحساب عدد الأوراق في ملفات Excel
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
    
    # وظيفة تحويل ملفات الاكسل ضمن خيط منفصل مع الواجهة
    def convert_xlsx_to_pdf_thread(self, target_folder, path_list):
        total_files = len(path_list)
        counter_completed_sheet = 0 
        self.count_sheet_in_files=self.count_sheets_in_excel_files(path_list)
        app_pdf = xw.App(visible=False) 
        try:
            for index, file_path in enumerate(path_list):
                if self.stop_command_pool:
                    break
                file_path = urllib.parse.unquote(file_path)
                file_name = os.path.basename(file_path)
                name, extension = os.path.splitext(file_name)
                if extension.lower() in ['.xlsx', '.xls']:
                    try:
                        workbook_pdf = app_pdf.books.open(file_path)
                        for sheet in workbook_pdf.sheets:
                            pdf_file = os.path.join(target_folder, f"{name}_{sheet.name}.pdf")
                            sheet.to_pdf(pdf_file, show=False, quality='standard')
                            counter_completed_sheet += 1 
                            self.information_progress.configure(text=f'File Name:  {file_name}\nsheet name: ({sheet.name})\n Completed: {total_files} Out of {total_files}')
                        workbook_pdf.close() 
                    except Exception as e:
                        print(f"Error converting {file_name}: {e}")
                        continue  
                self.progress_bar['value'] = counter_completed_sheet / self.count_sheet_in_files * 100
                self.progress_window.update_idletasks()
            if self.stop_command_pool:
                messagebox.showinfo("Stopped", "Document conversion was stopped.")
            else:
                messagebox.showinfo("Completed", f"All {total_files} files have been successfully converted to PDF.")
        finally:
            app_pdf.quit()
            self.progress_window.destroy()
    


    # وظيفة ضغط الملفات 
    def ziper_files(self):
        path_data_filtered = self.datasheet.data.copy()  
        if path_data_filtered.shape[0]==0:
            messagebox.showinfo("تنويه",f'لا يوجد ملفات ورد في القائمة لضغطها')
            return
        path_list = path_data_filtered['Full Path'].to_list()
        
        self.ziper_window = ctk.CTkToplevel()
        self.ziper_window.title("Compress Files")
        self.ziper_window.geometry("400x600")
        self.ziper_window.resizable(False, False)
        self.ziper_window.attributes("-topmost", True)
        self.ziper_window.focus_force()
        self.ziper_window.grab_set()

        ttk.Label(self.ziper_window, text="Set Name:").pack(padx=10, pady=5)
        self.zip_name_entry = ctk.CTkEntry(self.ziper_window, width=300)
        self.zip_name_entry.pack(padx=10, pady=5)

        self.zip_select_target_folder_btn = ctk.CTkButton(self.ziper_window, text="Select Target Folder To Save Result", command=self.select_target_folder)
        self.zip_select_target_folder_btn.pack(padx=10, pady=5)

        self.zip_Compress_btn = ctk.CTkButton(self.ziper_window, text="Compress Files", 
                                     command=lambda: threading.Thread(target=self.ziper_files_thread, args=(path_list, self.zip_name_entry), daemon=True).start())
        self.zip_Compress_btn.pack(padx=10, pady=5)


        self.zipper_progress_bar = ttk.Progressbar(self.ziper_window, length=300, mode="determinate")
        self.zipper_progress_bar.pack(padx=10, pady=5)

        self.zipper_information_progress = ttk.Label(self.ziper_window, text="", anchor='w', justify='left',font=('Segoe UI',10))
        self.zipper_information_progress.pack(fill='x', padx=10, pady=5) 
    
        self.ziper_window.mainloop()

    # وظيفة لتعطيل أزرار الضغط على الملفات المضغوطة
    def zip_btn_off(self):
        self.zip_name_entry.configure(state=ctk.DISABLED)
        self.zip_Compress_btn.configure(state=ctk.DISABLED)
        self.zip_select_target_folder_btn.configure(state=ctk.DISABLED)
    
    # وظيفة لتمكين أزرار الضغط على الملفات المضغوطة
    def zip_btn_on(self):
        self.zip_name_entry.configure(state=ctk.NORMAL)
        self.zip_Compress_btn.configure(state=ctk.NORMAL)
        self.zip_select_target_folder_btn.configure(state=ctk.NORMAL)

    # وظيفة لتحديد مجلد لحفظ الملف المضغوط
    def select_target_folder(self):
        self.zepper_target_folder= filedialog.askdirectory(title="اختر المجلد لحفظ الملف المضغوط")
        if self.zepper_target_folder:
            messagebox.showinfo("Done","تم تحديد مجلد المخرجات")

    # وظيفة لضغط الملفات في خيط منفصل
    def ziper_files_thread(self, path_list, name_entry):
        try:
            self.zip_btn_off()
            total_files = len(path_list)
            zip_name = name_entry.get()
            if not zip_name:
                messagebox.showwarning("تنبيه", "الرجاء إدخال اسم الملف المضغوط.")
                return
            if not self.zepper_target_folder:
                messagebox.showwarning("تنبيه", "الرجاء اختيار المجلد لحفظ الملف المضغوط.")
                return
            zip_path = os.path.join(self.zepper_target_folder, f"{zip_name}.zip")
            if not os.path.exists(self.zepper_target_folder):
                os.makedirs(self.zepper_target_folder)
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                counter = 0 
                for file_path in path_list:
                    file_path=file_path.replace("/","\\")
                    file_name = os.path.basename(file_path)
                    if os.path.isfile(file_path):
                        zipf.write(file_path, arcname=file_name.split("/")[-1])
                        counter += 1
                        self.zipper_information_progress.configure(text=f'File Name: {file_name} \nCompleted: {counter} Out of {total_files}')
                        self.zipper_progress_bar['value'] = counter / total_files * 100
                        self.ziper_window.update_idletasks()
            messagebox.showinfo("تم", f"تم ضغط {total_files} ملفًا بنجاح إلى {zip_path}")
            self.zip_btn_on()
        except Exception as e:
            self.zip_btn_on()
            messagebox.showerror("خطأ", f"حدث خطأ أثناء ضغط الملفات: {e}")

            
        
        
    
        
        
        