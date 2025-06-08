import customtkinter as ctk
import pandas as pd
from tkinter import messagebox
import os
from PIL import Image


## ________ BEGIN: resource ________::::::
"""
كلاس تعيين المصادر وتخزينها ضمن ملف الاعداداتٍ


"""


class Resource:
    def __init__(self):
        self.json_path = 'Settings/web_settings.json'  # مسار داتاست لحفظ التغيرات على الاعدادت
        self.my_resource = pd.read_json(self.json_path) # قراءة الاعداتا كداتا فريم
        self.face_sorce()



    # وظيفة بناء الواجهة التفاعلية
    def face_sorce(self):

        self.select_resource = ctk.CTkToplevel()
        self.select_resource.title("اختيار المصادر")
        self.select_resource.geometry("500x700")  
        self.select_resource.resizable(False, False)
        self.select_resource.focus_set()
        self.select_resource.grab_set()
        

        self.save_my_resource=ctk.CTkButton(self.select_resource, text='حفظ',font=('Segoe UI Semibold',17),command=self.save_preferences)
        self.save_my_resource.pack(fill='x', pady=10,padx=10)

        ctk.CTkLabel(self.select_resource, text='اختر اقصى مدى للحصول على الأخبار من مصادرها',font=('Segoe UI Semibold',17)).pack(fill='x', pady=5,padx=5)
        
        self.allow_period=['Last 2 days', 'Last 5 days', 'Last 7 days', 'Last 15 days' ]
        self.period_var = ctk.StringVar(value=self.allow_period[1])
        select_period=ctk.CTkComboBox(self.select_resource,values=self.allow_period,variable=self.period_var, font=('Segoe UI Semibold',17))
        select_period.pack(fill='x', pady=5,padx=2)
      

        self.SELECT_WEB_FRAME = ctk.CTkScrollableFrame(self.select_resource,label_text='Select To Scrip',
                                                       label_font=('Segoe UI Semibold',17) ,
                                                       width=400, height=600, border_width=2, corner_radius=1 
                                                    ,scrollbar_button_color='#8B8392', )
        self.SELECT_WEB_FRAME.pack(fill=ctk.BOTH, expand=False, padx=10, pady=50, ipadx=10)

        self.web_checkboxes = {}
        self.site_name_var = {}


        def update_site_status(site):
            all_checked = all(var.get() for var in self.web_checkboxes[site].values())
            any_checked = any(var.get() for var in self.web_checkboxes[site].values())
            self.site_name_var[site].set(all_checked if any_checked else False)

        def toggle_site(site):
            is_checked = self.site_name_var[site].get()
            for category_var in self.web_checkboxes[site].values():
                category_var.set(is_checked)

        row_index = 0

        # حلقة لبناء شيكبوكس لكل موقع
        for _, row in self.my_resource.iterrows():
            site_name_EN = row["WebSiteNameEN"]
            site_name_AR = row["WebSiteNameAR"]
            web_id = row["WebID"]
            category_nameEN = row["CategoryEN"]
            category_nameAR = row["CategoryAR"]
            cat_id = row['ID']
            prefer=row['prefer']
            
            if site_name_EN not in self.web_checkboxes:
                self.site_name_var[site_name_EN] = ctk.BooleanVar()
                ctk.CTkCheckBox(
                    self.SELECT_WEB_FRAME,
                    text=f"{site_name_EN} - {site_name_AR}",
                    variable=self.site_name_var[site_name_EN],
                    width=200, height=25, checkbox_width=25, checkbox_height=25,
                    corner_radius=3, border_width=2, fg_color='#0685aa',
                    font=("Segoe UI Semibold", 20),
                    command=lambda site=site_name_EN: toggle_site(site)
                ).grid(row=row_index, column=0, pady=10, padx=10, sticky="w")
   
                logo_ = self.load_icone_from_path(fr"Icons/{web_id}.png",size=(50, 50))
         
                ctk.CTkLabel(self.SELECT_WEB_FRAME, text='', image=logo_, compound="left").grid(row=row_index, column=1, pady=5, padx=10)
                self.web_checkboxes[site_name_EN] = {}
                row_index += 1

            category_var = ctk.BooleanVar(value=(prefer == 1))
            self.web_checkboxes[site_name_EN][cat_id] = category_var
            ctk.CTkCheckBox(
                self.SELECT_WEB_FRAME,
                text=f"{category_nameEN} / {category_nameAR}",
                variable=category_var,
                width=200, height=17, checkbox_width=17, checkbox_height=17,
                corner_radius=4, border_width=1, fg_color='#12bcca',
                font=("Segoe UI", 12),
                command=lambda site=site_name_EN: update_site_status(site),
            ).grid(row=row_index, column=0, pady=5, padx=25, sticky="w")

            row_index += 1

    #وظيفة لتحميل صورة من مسارها بشكل صحيح
    def load_icone_from_path(self,path_, size=(20, 20)):
        try:
            if not os.path.exists(path_):
                raise FileNotFoundError(f"File not found: {path_}")
            icone = Image.open(path_)
            icone = icone.resize(size)
            ctk_image = ctk.CTkImage(light_image=icone, size=size)
            return ctk_image

        except FileNotFoundError:
            default_icone = Image.new("RGB", size, color="gray")
            return ctk.CTkImage(light_image=default_icone, size=size)  


    # وظيفة لتحديث التفضيلات الجديدة
    def save_preferences(self):
        selected_period = self.period_var.get()
        if '2' in selected_period:
            selected_period=2
        elif '15' in selected_period:
            selected_period=15
        elif '5' in selected_period:
            selected_period=5
        elif '7' in selected_period:
            selected_period=7
        else: selected_period =5

        for _, row in self.my_resource.iterrows():
            site_name_EN = row["WebSiteNameEN"]
            cat_id = row["ID"]
            if site_name_EN in self.web_checkboxes and cat_id in self.web_checkboxes[site_name_EN]:
                self.my_resource.loc[self.my_resource["ID"] == cat_id, "prefer"] = int(self.web_checkboxes[site_name_EN][cat_id].get())
                self.my_resource.loc[self.my_resource["ID"] == cat_id, "period"] = selected_period
        self.my_resource.to_json(self.json_path, orient='records', indent=4, force_ascii=False)
       
        messagebox.showinfo("Done","تم حفظ المصادر بنجاح")

