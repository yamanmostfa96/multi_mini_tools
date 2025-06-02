import pandas as pd 
import numpy as np
import os
from tkinter import Tk,filedialog, messagebox,Label,IntVar,Radiobutton,Button
from PIL import Image
import customtkinter as ctk
import pyperclip
  # إخفاء نافذة tkinter الرئيسية

from Modails.TkSheetTable import TableSheet


class ConverterToJson(ctk.CTkScrollableFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, height=1000)
        

        self.filepath =''
        self.general_data_frame=''

        #FIRST STEP
        self.first_step_frame=ctk.CTkFrame(self, border_color='white', border_width=1, corner_radius=1)
        self.first_step_frame.pack(fill="x", padx=10, pady=10)

        first_lable=ctk.CTkLabel(self.first_step_frame, text='الخطوة الأولى اختيار ملف اكسل',
                                     fg_color="#3d6bd6",height=35,corner_radius=1,
                                    font=('Segoe UI Semibold',18),anchor='ne', compound='left',justify='left' )
        first_lable.pack(fill="x", padx=5, pady=10)

        self.select_file_button = ctk.CTkButton(self.first_step_frame, text="Browse Excel File",font=('Segoe UI Semibold',14), command=self.select_excel_file, width=300, height=30)
        self.select_file_button.pack(pady=10)
        
        self.data_sheet_frame=ctk.CTkFrame(self.first_step_frame, border_width=0.1)
        
        sheet_name_lable=ctk.CTkLabel(self.data_sheet_frame, text='اختر ورقة للمعاينة',height=20,corner_radius=1,width=200,
                                    font=('Segoe UI Semibold',14),anchor='ne', compound='left',justify='left' )
        sheet_name_lable.grid(row=0, column=0, pady=2, padx=0)

        self.sheet_name = ctk.CTkComboBox(self.data_sheet_frame, values=[], width=200,justify='left',
                             command=self.define_data_frame_and_update_data_sheet)
        self.sheet_name.grid(row=0, column=1, pady=2)


        self.datasheet = TableSheet(self.data_sheet_frame, data=(), width=1000, hight=350, header=[], column_widths=[100], align_center=[0])
        
        
        #SECONDE STEP

        self.second_step_frame=ctk.CTkFrame(self, border_color='white', border_width=2, corner_radius=1)
        
        second_lable=ctk.CTkLabel(self.second_step_frame, text=' الخطوة الثانية اختر شكل الجيسون',
                                     fg_color='#3d6bd6',height=35,corner_radius=1,
                                    font=('Segoe UI Semibold',18),anchor='ne', compound='left',justify='left' )
        second_lable.pack(fill="x", padx=5, pady=10)

        self.optionmenu = ctk.CTkComboBox(self.second_step_frame, values=["1.Liner Key, String Values", "2.Liner Key, Defined Values",
                                                                            "3.Liner Rows, String Values","4.Liner Rows, Defined Values,"],
                                         command=self.convert_json_reader)
        self.optionmenu.set("1.Liner Key, String Values")
        self.optionmenu.pack(fill='x', padx=5, pady=5)


        self.frame_json_read=ctk.CTkFrame(self.second_step_frame, fg_color='#28282a')
        self.frame_json_read.pack(fill="x", padx=5, pady=2)

        self.copy_button = ctk.CTkButton(self.frame_json_read,text='≡ Copy To Clipbord',font=('arial',11),
                                     bg_color='transparent', command=self.copy_to_clipboard, width=150, height=30,
                                     corner_radius=5)
        self.copy_button.grid(row=0,column=0)

        self.extract_to_json = ctk.CTkButton(self.frame_json_read,text='↓ Extract To Json',font=('arial',11),
                                     bg_color='transparent', command=self.Extract_to_json_file, width=150, height=30,
                                     corner_radius=5)
        self.extract_to_json.grid(row=0, column=1)


        self.json_reader = ctk.CTkTextbox(self.frame_json_read,width=1000, height=200,text_color='white', bg_color='#28282a', fg_color='#28282a', font=('tohama', 12))
        self.json_reader.grid(row=1, column=0, columnspan=10)
        self.json_reader.insert("end", "Here Is Json...")
        self.json_reader.configure(state='disabled')




    #OPERATION METHODS

    def define_data_frame_and_update_data_sheet(self, sheet_name):
        try:
            self.general_data_frame = pd.read_excel(self.filepath, sheet_name=sheet_name, dtype=str)
            self.general_data_frame.dropna(how='all')
            self.general_data_frame.replace(pd.NA,'', inplace=True)
            data=self.general_data_frame.values.tolist()
            self.datasheet.set_header(self.general_data_frame.columns.tolist())
            self.datasheet.load_data(data)
            self.convert_json_reader()

        except Exception as e:
            messagebox.showerror('Error', f'حصل الخطأ التالي: {e}')


    def select_excel_file(self):
        self.filepath = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        if self.filepath:
            try:
                self.data_sheet_frame.pack(fill="x", padx=5, pady=10)
                self.datasheet.grid(row=2, column=0,padx=10, columnspan=2)
                self.second_step_frame.pack(fill="x", padx=10, pady=10)

                self.sheet_names = pd.ExcelFile(self.filepath).sheet_names
                self.sheet_name.configure(values=self.sheet_names)
                self.sheet_name.set(self.sheet_names[0])
                self.define_data_frame_and_update_data_sheet(self.sheet_name.get())
            except Exception as e:
                messagebox.showerror('Error', f'حصل الخطأ التالي: {e}')

    


    def convert_data_frame_to_json(self):
        indent = self.optionmenu.get()
        if '2' in indent or '4' in indent:
            row_data = pd.read_excel(self.filepath, sheet_name=self.sheet_name.get())
        else:
            row_data = pd.read_excel(self.filepath, sheet_name=self.sheet_name.get(), dtype=str)
        
        
        row_data.replace("", np.nan, inplace=True)
        row_data.dropna(how='all', inplace=True)
        row_data.dropna(axis=1, how='all', inplace=True)
 
        
        json_data = ""
        if '1' in indent or '2' in indent:
            json_data = row_data.to_json(orient='records', force_ascii=False, indent=2)
            
        elif  '3' in indent or '4' in indent:
            json_data = '[\n'
            for i, record in row_data.iterrows():
                json_record = record.to_json(force_ascii=False)
                if i < len(row_data) - 1:
                    json_data += f'    {json_record},\n'
                else:
                    json_data += f'    {json_record}\n'
            json_data += ']'
        
        return json_data.replace('null,','"",')
          


    def convert_json_reader(self, *args):
        json_data = self.convert_data_frame_to_json()
        self.json_reader.configure(state='normal')
        self.json_reader.delete(1.0, 'end')
        self.json_reader.insert("end",json_data)
        self.json_reader.yview_moveto(0)
        self.json_reader.configure(state='disabled')


    def copy_to_clipboard(self):
        text_to_copy = self.json_reader.get("1.0", "end-1c")
        pyperclip.copy(text_to_copy)
        messagebox.showinfo('Done','Json Coped To Clipbord')

    
    def Extract_to_json_file(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            file_name = f"{folder_path}/{os.path.splitext(os.path.basename(self.filepath))[0]}_json.json"
            json_data = self.convert_data_frame_to_json()
            try:
                with open(file_name, 'w', encoding='utf-8') as file:
                    file.write(json_data)
                messagebox.showinfo('Success', f'File saved successfully as {file_name}')
            except Exception as e:
                messagebox.showerror('Error', f'Error occurred while saving file: {e}')
