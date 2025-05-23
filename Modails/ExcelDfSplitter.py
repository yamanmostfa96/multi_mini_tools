import pandas as pd 
import customtkinter as ctk
import openpyxl as px
from pathlib import Path
import os
import threading
from tkinter import filedialog, messagebox, Toplevel, Button
from tkinter import ttk
from openpyxl.worksheet.table import TableStyleInfo

from Modails.table import Table as tb

class ExcellSplitter(ctk.CTkScrollableFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.filepath =''
        self.general_data_frame=''
        self.create_widgets()


    def create_widgets(self):
        self.first_step_frame=ctk.CTkFrame(self, border_width=1, corner_radius=1,height=50)
        self.first_step_frame.pack(fill="x", padx=10, pady=10)

        self.select_file_button = ctk.CTkButton(self.first_step_frame, text="Browse Excel File",font=('Segoe UI Semibold',14), command=self.select_excel_file, width=300, height=30)
        self.select_file_button.pack(side="left", padx=2, pady=2, anchor='w', fill="x")

        self.first_step_frame.pack_propagate(False)


        self.data_sheet_frame=ctk.CTkFrame(self, border_width=0.1)

        sheet_name_lable=ctk.CTkLabel(self.data_sheet_frame, text='Select Sheet From File',height=20,corner_radius=1,width=200,font=('Segoe UI Semibold',14),anchor='ne', compound='left',justify='left' )
        sheet_name_lable.grid(row=0, column=0, pady=2, padx=0)

        self.sheet_name = ctk.CTkComboBox(self.data_sheet_frame, values=[], width=200, justify='left',
                             command=self.define_data_frame_and_update_data_sheet)
        self.sheet_name.grid(row=0, column=1, pady=2)

        column_lbl=ctk.CTkLabel(self.data_sheet_frame, text='Select Column to Split Data',height=20,corner_radius=1,width=200,font=('Segoe UI Semibold',14),anchor='ne', compound='left',justify='left' )
        column_lbl.grid(row=0, column=2, pady=2, padx=0)

        self.column_name=ctk.CTkComboBox(self.data_sheet_frame, values=[], width=200, justify='left')
        self.column_name.grid(row=0, column=3, pady=2)

        self.Split_and_save_results_btn=ctk.CTkButton(self.data_sheet_frame, text="Split and Save Results",font=('Segoe UI Semibold',14),fg_color='green',command=self.save_results, width=300, height=20)
        self.Split_and_save_results_btn.grid(row=0, column=5, pady=2, padx=20)

        self.datasheet=None
       




    
    # operations functions:___

    def select_excel_file(self):
      
        self.filepath = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        if self.filepath:
        #    try:
                self.data_sheet_frame.pack(fill="x", padx=5, pady=10)
                self.sheet_names = pd.ExcelFile(self.filepath).sheet_names
                self.sheet_name.configure(values=self.sheet_names)
                self.sheet_name.set(self.sheet_names[0])
                self.define_data_frame_and_update_data_sheet(self.sheet_name.get())
                
        #    except Exception as e:
        #        messagebox.showerror('Error', f'حصل الخطأ التالي: {e}')
           

    def define_data_frame_and_update_data_sheet(self, sheet_name):
        #try:
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

            if not self.datasheet:
                    self.datasheet = tb(self,dataframe=self.general_data_frame,with_filter=0, with_sorter=0, with_index=1,on_update_callback=0)
            
            self.datasheet.data=self.general_data_frame.copy()
            self.datasheet.load_data()
            self.datasheet.pack(side='top',fill="x", padx=5,pady=5,anchor='n')
   
        #except Exception as e:
        #   messagebox.showerror('Error', f'حصل الخطأ التالي: {e}')
    

    def save_results(self):
        self.target_folder=filedialog.askdirectory(title='حدد مجلد المخرجات')
        
        if self.target_folder:
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
            def stop_saving():
                self.stop_process = True
                self.progress_label.config(text="جارٍ الإيقاف...")
            stop_button = Button(self.progress_window, text="إيقاف", command=stop_saving)
            stop_button.pack(pady=5)

            threading.Thread(target=self.save_task, daemon=True).start()

  
    def save_task(self):
            try:
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
        
         



    def create_table(self,table_name, worksheet):
                table_style ='TableStyleMedium17'
                table = px.worksheet.table.Table(displayName=table_name, ref=worksheet.dimensions)
                table.tableStyleInfo = TableStyleInfo(name=table_style, showFirstColumn=False,
                showLastColumn=False, showRowStripes=True, showColumnStripes=False)
                worksheet.add_table(table)
    
    def save_file_as_file(self,target_folder, file_name, df):
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
               
