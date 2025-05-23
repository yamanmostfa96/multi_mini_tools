
from tkinter import ttk,messagebox,scrolledtext, filedialog
import customtkinter as ctk
import pandas as pd
import webbrowser
from PIL import Image
import os
import time
import sqlite3 as sq
from sqlite3 import Error
import openpyxl as px
from openpyxl.worksheet.table import TableStyleInfo
from difflib import SequenceMatcher
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import  unquote,urlparse
from datetime import datetime,timedelta, date
import sys
import uuid
import concurrent.futures
import threading




@staticmethod
def load_icone_from_path(path_, size=(20, 20)):
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


class Browser_Result(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, border_width=1, height=700, width=1100, corner_radius=0)
        self.SQL=SQL_DB()
        self.SQL.initialize_database()
        self.SQL.set_settings_web_in_cat()
        self.sheet_data=TableSheetNews(self)
        self.sheet_data.pack(fill='x')
        
        self.hint_label = ctk.CTkLabel(self, text="📢 لقراءة محتوى الخبر، انقر عليه مرتين", font=('Segoe UI', 15, 'bold'), text_color="red")
        self.hint_label.pack(fill='x')

        self.pulse_animation(size=14, growing=True, count=0)

    def pulse_animation(self, size, growing, count):
        if count >= 100:
            self.hint_label.destroy()
            return
        new_size = size + 1 if growing else size - 1
        self.hint_label.configure(font=('Segoe UI', new_size, 'bold'))
        if new_size >= 25:
            growing = False
        elif new_size <= 14:
            growing = True
        self.after(100, self.pulse_animation, new_size, growing, count + 1)

        

class TableSheetNews(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.SQL=SQL_DB()
        self.original_data = self.SQL.get_full_data()  
        self.data = self.original_data.copy()
        self.article_container=None
        self.delete_old_news() # حذف الاخبار اقدم من 7 ايام تلقائيا
        self.show_table_summary() # عرض الجدول
        self.is_stoped=False
        

    # صميم جدول العرض -----------------------------
    def show_table_summary(self):
        self.header_set = {'SN':50,'ID': 75, 'WebSiteNameEN': 150, 'WebSiteNameAR': 125, 'CategoryEN': 150, 'CategoryAR': 150, 'NewsTitle': 550, 'NewsDatePuplish': 200,'IsRead':100}
        self.headers_=list(self.header_set.keys())
        self.sort_orders = {col: True for col in self.headers_}
        
        style = ttk.Style(self)
        style.configure("Treeview", background="black", foreground="black", rowheight=30, fieldbackground="#f9f9f9")
        style.configure("Treeview.Heading", font=('Segoe UI', 13, 'bold'),  background="#007ba0", foreground="#007ba0",  fieldbackground="#f9f9f9")
        style.map("Treeview", background=[("selected", "#007ba0")])

        # إنشاء جدول Treeview
        self.tree = ttk.Treeview(self, columns=self.headers_, show="headings", height=25)
        # ربط الاحداث
        #self.tree.bind("<<TreeviewSelect>>", self.show_contain)
        self.tree.bind("<Double-1>", self.show_contain)

        for col in self.header_set.keys():
            self.tree.heading(col, text=f"{col} ↑", anchor="center", command=lambda c=col: self.sort_column(c))

        for col,width in self.header_set.items():
            self.tree.column(col, width=width, stretch=False)
            self.tree.heading(col, text=f'↑ {col}', anchor='center') 
            self.tree.column(col, anchor="center") 
        self.tree.column("NewsTitle", anchor="e")
        
        # إضافة التمرير
        self.scroll_y = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.scroll_x = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=self.scroll_y.set, xscrollcommand=self.scroll_x.set)

   
        self.filter_frame = ctk.CTkFrame(self, fg_color='transparent')
        self.filter_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=2)
        
        self.top_btns_fram=ctk.CTkFrame(self.filter_frame,fg_color='transparent')
        self.top_btns_fram.pack(side="top", padx=2, pady=2, anchor='w', fill="x")


        delete_from_db_btn=ctk.CTkButton(self.top_btns_fram, text="تفريغ المحتويات",font=('Segoe UI', 13, 'bold'),anchor='right',fg_color='red',
                                                    command=self.delete_all_results, width=120, height=25, corner_radius=4)
        delete_from_db_btn.pack(side="left", padx=5, pady=4, anchor='e')

        set_all_read_btn =ctk.CTkButton(self.top_btns_fram, text="تحديد الكل كمقروء",font=('Segoe UI', 13, 'bold'),anchor='right',fg_color='#0bc579',
                                                    command=self.set_all_as_readed, width=120, height=25, corner_radius=4)
        set_all_read_btn.pack(side="left", padx=5, pady=4, anchor='e')


        self.cnt_avilable=ctk.CTkLabel(self.top_btns_fram, text=f'Count News: {self.original_data.shape[0]}',font=('Segoe UI',15, 'bold'),anchor='e',width=120, height=25)
        self.cnt_avilable.pack(side="left", padx=20, pady=4, anchor='e')


        to_excel_file=ctk.CTkButton(self.top_btns_fram, text="حفظ كملف اكسل",font=('Segoe UI', 13, 'bold'),anchor='right',fg_color='#0bc579',
                                                    command=self.save_to_excel, width=120, height=25, corner_radius=4)
        to_excel_file.pack(side="right", padx=5, pady=4, anchor='e')

        set_resource=ctk.CTkButton(self.top_btns_fram, text="مصادري",font=('Segoe UI', 13, 'bold'),anchor='right',fg_color='#054f99',
                                                    command=self.set_my_resource, width=120, height=25, corner_radius=4)
        set_resource.pack(side="right", padx=5, pady=4, anchor='e')

        self.get_news_btn=ctk.CTkButton(self.top_btns_fram, text="بحث عن أخبار",font=('Segoe UI', 13, 'bold'),anchor='right',fg_color='#c210bf',
                                                    command=self.Get_News, width=120, height=25, corner_radius=4)
        self.get_news_btn.pack(side="right", padx=5, pady=4, anchor='e')

        self.stop_serch=ctk.CTkButton(self.top_btns_fram, text=" ايقاف البحث",font=('Segoe UI', 13, 'bold'),anchor='right',fg_color='red',
                                                    command=self.stop_all_operations_for_serch_news, width=120, height=25, corner_radius=4)
        
        self.filter_entries = {}
        for col in self.headers_:
            if col=='SN':
                ctk.CTkLabel(self.filter_frame,text='     ', width=50).pack(side="left", padx=0, pady=2)
                continue
            entry = ctk.CTkEntry(self.filter_frame, placeholder_text=f"ʘ تصفية {col}", width=self.header_set[col]//1.3, font=('Settings/font/Cairo-Black.ttf', 9))
            entry.pack(side="left", padx=0, pady=2)
            entry.bind("<KeyRelease>", lambda event, c=col: self.apply_filter())
            self.filter_entries[col] = entry
        
        # ترتيب العناصر في الشبكة
        self.filter_frame.grid_columnconfigure(0, weight=1)
        self.tree.grid(row=1, column=0, sticky="nsew")
        self.scroll_y.grid(row=1, column=1, sticky="ns")
        self.scroll_x.grid(row=2, column=0, sticky="ew")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # تحميل البيانات إلى الجدول
        self.load_data(self.data)


    ########################  عمليات الجدول #############
    def set_my_resource(self):
        return  Resource()
    
    def delete_old_news(self):
        query=f"delete from Results where NewsDatePuplish <= date('now', '-8 day')"
        self.SQL.execute_query(query)
        

    def reset_counter(self):
        self.cnt_avilable.configure(text=f'Count News: {len(self.tree.get_children())}')
        

    def  load_data(self,data):
        """تحميل البيانات في الجدول مع تلوين الصفوف"""
        for i in self.tree.get_children():
            self.tree.delete(i)
        data['SN'] = range(1, len(data) + 1)
        data = data[['SN'] + [col for col in data.columns if col != 'SN']]
        for index, row in data.iterrows():
            tag = "evenrow" if row['SN'] % 2 == 0 else "oddrow"
            if 'غير' in row['IsRead'] :
                tag='nova'
            self.tree.insert("", "end", values=tuple(row), tags=(tag,))  
        self.tree.tag_configure("evenrow", background="#dbe7e4") 
        self.tree.tag_configure("oddrow", background="white")
        self.tree.tag_configure("nova", background="#42b84e")  
        self.reset_counter()


    def sort_column(self, col_name):
        self.data=self.original_data.copy()
        ascending = self.sort_orders[col_name]
        self.data = self.data.sort_values(by=col_name, ascending=ascending, ignore_index=True)
        self.load_data(self.data)
        arrow = "↑" if ascending else "↓"
        self.tree.heading(col_name, text=f"{col_name} {arrow}")
        self.sort_orders[col_name] = not ascending
    

    def apply_filter(self):
        """تطبيق التصفية بناءً على إدخال المستخدم"""
        self.data = self.original_data.copy()

        for col, entry in self.filter_entries.items():
            value = entry.get().strip().lower()
            if value:
                self.data = self.data[self.data[col].astype(str).str.lower().str.contains(value)]
        self.load_data(self.data) 
       

    def save_to_excel(self):
        ids= [self.tree.item(item, "values")[1] for item in self.tree.get_children()]
        ids = ",".join(map(str, ids))
        ids=f'({ids})'
        query=f""" select
                R.ID,
                C.WebSiteNameEN, C.WebSiteNameAR, C.CategoryEN, C.CategoryAR,
                R.NewsTitle, R.NewsDatePuplish,R.NewsURL, R.NewsContain, R.NewsSummary,R.NewsContainEN,
                R.NewsSummaryEN, R.Batch, R.LastUpdate
                from  
                Results R inner join cat C on R.Cat_id = C.id where R.id in {ids} """
        df=self.SQL.fetch_query_get_results_as_data_frame(query=query)
        try:
            saver=SaveResults_Excel()
            saver.save_result(dataframe=df)
            messagebox.showinfo("Done", "تم حفظ البيانات بنجاح")
        except Exception as e:
            print(e)
            messagebox.showerror("Error",f"حصل الخطأ التالي اثناء حفظ المخرجات  {e}")


    def next_article(self, event=None):
        """الانتقال إلى المقالة التالية"""
        selected_items = self.tree.selection()
        item_id = selected_items[0]
        next_item_id = self.tree.next(item_id)
        if not next_item_id:return
        self.tree.selection_set(next_item_id)
        self.tree.focus(next_item_id)
        self.tree.see(next_item_id)
        self.show_contain()


    def last_article(self, event=None):
        """الانتقال إلى المقالة السابقة"""
        selected_items = self.tree.selection()
        item_id = selected_items[0]
        last_item_id = self.tree.prev(item_id)
        if not last_item_id: return
        self.tree.selection_set(last_item_id)
        self.tree.focus(last_item_id)
        self.tree.see(last_item_id)
        self.show_contain()


    def set_all_as_readed(self):
        query= f"""update Results set IsRead = 1"""
        self.SQL.execute_query(query)
        self.original_data=self.SQL.get_full_data()
        self.apply_filter()


    def show_contain(self, event=None):
        if self.article_container:self.article_container.destroy()
        selected_items = self.tree.selection()
        if not selected_items:return
        
        item_id = selected_items[0]
        values = self.tree.item(item_id, "values")
        
        news_id = values[1]
        title = values[6]
        site_name = values[3]
        site_category = values[5]
        publish_date = f'تاريخ النشر: {values[7]}'
       
        self.SQL.update_readed(news_id)

        news_contain = self.SQL.get_news_content_by_id(news_id).replace("\n", "\n\n")
        web_id = self.SQL.get_web_id_by_news_id(news_id)
        news_url = self.SQL.get_news_url_by_id(news_id)
        
        news_contain=f'{"*"*20}\n{title}\n{"*"*20}\n{news_contain}'

        for item in self.tree.get_children():
            if int(self.tree.item(item)["values"][1]) == int(news_id):  
                current_values = list(self.tree.item(item)["values"])
                current_values[8] = "مقروء" 
                self.tree.item(item, values=tuple(current_values))
                
                tag = "evenrow" if current_values[1] % 2 == 0 else "oddrow"
                self.tree.item(item, tags=(tag,))
                self.tree.tag_configure("evenrow", background="#dbe7e4") 
                self.tree.tag_configure("oddrow", background="white")
                self.original_data.loc[self.original_data['ID'] == news_id, 'IsRead'] = 1
                break  

        self.show_message_with_scrollbar(title, news_contain, news_url, site_name, site_category, publish_date, web_id)

    def show_message_with_scrollbar(self, title, message, url, site_name, site_category, publish_date, web_id):
        # إنشاء النافذة الجديدة
        self.article_container = ctk.CTkToplevel()
        self.article_container.title(title)
        screen_width = self.article_container.winfo_screenwidth()
        screen_height = self.article_container.winfo_screenheight()
        window_width = 600
        window_height = 700
        position_x = (screen_width // 2) - (window_width // 2)
        position_y = (screen_height // 2) - (window_height // 2)
        self.article_container.geometry(f"{window_width}x{window_height}+{position_x}+{position_y}")
        self.article_container.focus_set()
        self.article_container.resizable(False, True)  # إغلاق تغيير الحجم
      
        button_frame = ctk.CTkFrame(self.article_container)
        button_frame.pack(side='top', padx=10, pady=10, fill='x')
    
        logo_ = load_icone_from_path(fr"Icons/{web_id}.png",size=(60, 60))

        ctk.CTkLabel(button_frame, text=site_name, font=('Segoe UI', 16), image=logo_, compound="top").grid(row=0, column=0, padx=10, pady=5, rowspan=3, sticky='w')

        ctk.CTkLabel(button_frame, text=site_category, font=('Segoe UI', 10)).grid(row=0, column=1, padx=5, pady=2, sticky='w')
        ctk.CTkLabel(button_frame, text=publish_date, font=('Segoe UI', 10)).grid(row=1, column=1, padx=5, pady=2, sticky='w')

        open_web = ctk.CTkButton(button_frame, text="Open In Web 🔗", command=lambda: webbrowser.open(url))
        open_web.grid(row=0, column=3, padx=10, pady=10)

        convert_to_pdf = ctk.CTkButton(button_frame, text="Save As PDF", command=lambda: self.convert_contains_to_pdf(url,title))
        convert_to_pdf.grid(row=1, column=3, padx=10, pady=10)


        next_article_btn = ctk.CTkButton(button_frame, text="التالي", font=('Segoe UI', 14), fg_color='#9d0ede',command=self.next_article)
        next_article_btn.grid(row=0, column=4, padx=10, pady=10)

        last_article_btn = ctk.CTkButton(button_frame, text="السابق", font=('Segoe UI', 14), fg_color='#9d0ede',
                                     command=self.last_article)
        last_article_btn.grid(row=1, column=4, padx=10, pady=10)

        text_area = scrolledtext.ScrolledText(self.article_container, wrap='word', font=('Segoe UI', 12), padx=10, pady=10)
        text_area.pack(expand=True, fill='both')

    
        text_area.tag_configure("rtl", justify="right")
        text_area.insert('1.0', message)
        text_area.tag_add("rtl", "1.0", "end")
        text_area.config(state='disabled')  # جعل النص غير قابل للتعديل


    
    def convert_contains_to_pdf(self,url,title):
        target=filedialog.askdirectory(title='اختر مجلد الحفظ')
        if not target:
            return
        try:
            SoupOps.convert_html_to_pdf(self, url,title, target)

            print(messagebox.showinfo("done","تم حفظ المخرجات"))
        except Exception as e:
            messagebox.showerror("خطأ",f"حصل الخطأ التالي اثنائ التحويل  {e}")
            return
        
    def update_traker_and_data(self,row):
        columns = ["ID", "WebSiteNameEN", "WebSiteNameAR", "CategoryEN", "CategoryAR",  "NewsTitle", "NewsDatePuplish", "IsRead"]
        try:
            news_to_show=row
            row_count = len(self.tree.get_children())+1
            result = (row_count,) + news_to_show
            self.original_data = pd.concat([self.original_data, pd.DataFrame([news_to_show], columns=columns)], ignore_index=True)
            self.data=self.original_data.copy()
            self.tree.insert("", "end", values=result, tags=('nova',))  
            self.tree.tag_configure("nova", background="#42b84e")
            self.reset_counter()
        except Exception as e:
            print (f'error with update_traker_and_data:{e}')
            


    def delete_all_results(self):
        ask_yes=messagebox.askyesno("حذف",f"سيتم حذف  {self.original_data.shape[0]} خبرا، هل أنت متأكد من أجراء العملية، للاستمرار اضغط ok")
        if ask_yes:
            query="delete from results"
            self.SQL.execute_query(query)
            self.data=self.load_data(self.SQL.get_full_data())
            self.reset_counter()
            messagebox.showinfo("done","تم التفريغ بنجاح")

        
    def stop_all_operations_for_serch_news(self):
        """إيقاف العمليات مع Progress Bar لمدة 5 ثوانٍ"""
        self.is_stoped = True
        progress_window = ctk.CTkToplevel()
        progress_window.title("إيقاف العمليات")
        progress_window.geometry("300x100")
        progress_window.resizable(False, False)
        progress_window.attributes("-topmost", True)
        progress_window.focus_force()
        progress_window.grab_set()
        self.stop_serch.pack_forget()
        self.get_news_btn.configure(state=ctk.DISABLED)
        self.get_news_btn.configure(text='بحث عن أخبار',state=ctk.NORMAL)
        
        label = ctk.CTkLabel(progress_window, text="جارٍ الإيقاف...", font=('Segoe UI Semibold',17))
        label.pack(pady=10)
        progress = ttk.Progressbar(progress_window, length=250, mode="determinate")
        progress.pack(pady=10)
        
        def update_progress(count=0):
            if count < 10: 
                progress["value"] = (count + 1) * 10  
                progress_window.after(500, update_progress, count + 1)
            else:
                progress_window.destroy() 
                messagebox.showinfo("تم الإيقاف", "تم إيقاف البحث بالكامل")
                self.stop_serch.pack_forget()
                self.get_news_btn.configure(state=ctk.NORMAL, text="بحث عن أخبار")
        update_progress()  
        
        
       
    def stop_sercher(self):
        return self.is_stoped
         
    
    
    def Get_News(self):
        self.is_stoped=False
        try: self.stop_serch.pack_propagate()
        except: pass
        self.stop_serch.pack(side="right", padx=5, pady=4, anchor='e')

        self.get_news_btn.configure(text='جار البحث')
        self.get_news_btn.configure(state=ctk.DISABLED)
        

        self.UUID = str(uuid.uuid4()).replace('-', '').lower()
        self.my_web_site=pd.read_json('Settings/web_settings.json')
        
        self.my_web_site = self.my_web_site[self.my_web_site["prefer"] == 1]

        self.headers = {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                }
        
        self.headers2 = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

        self.websites_map = {
            2:'Syria_TV',
            16: 'Alhal_net',
            5:'Almodon',
            13:'Alsouria_net',
            6:'Alwatan',
            7:'Atharpress',
            11:'EconomyDay',
            14:'EnabBaladi',
            8:'Eqtesad',
            3:'HalabToday',
            15:'Kassioun',
            10:'Sana',
            12:'ShamNetwork',
            17:'HoranNews',
            18:'Alkhabar',
            19:'SyriaNews',
            20:'Alikhbariah'
         }
        
        if self.my_web_site.shape[0]==0:
            messagebox.showerror("لا يوجد مراجع محددة","يرجى تحديد مرجع واحد على الأقل")
            return
        threading.Thread(target=self.fetch_all_news, daemon=True).start()

    
    def run_function(self, web_ID):
        if web_ID in self.websites_map:
            web_data=self.my_web_site[self.my_web_site['WebID'] == web_ID]
            self.fn_settings={'web_data':web_data,'headers':self.headers,'UUID':self.UUID,'update_traker_and_data':self.update_traker_and_data,'after_stop_flag': self.stop_sercher}
            scraper = GET_NEWS_FROM_WEBSITES(self.fn_settings)
            method_name = self.websites_map[web_ID]
            if hasattr(scraper, method_name):  
                getattr(scraper, method_name)() 
            else:
                print(f"⚠ الميثود '{method_name}' غير موجودة في `get_news`!")
            
    def fetch_all_news(self):
        web_id_selected = self.my_web_site['WebID'].unique().tolist()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(self.run_function, web_) for web_ in web_id_selected]
            concurrent.futures.wait(futures)
           
        self.get_news_btn.configure(text='بحث عن أخبار',state=ctk.NORMAL)

#################################################################################################################################
###############################################   SQL DB Operations class    ####################################################
#################################################################################################################################
## ________ BEGIN: resource ________::::::
       
class Resource:
    def __init__(self):
        self.json_path = 'Settings/web_settings.json'  
        self.my_resource = pd.read_json(self.json_path)
        self.face_sorce()

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
   
                logo_ = load_icone_from_path(fr"Icons/{web_id}.png",size=(50, 50))
         
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


#################################################################################################################################
###############################################   SQL DB Operations class    ####################################################
#################################################################################################################################

## ________ BEGIN: sql db class ________::::::
class SQL_DB:
    def __init__(self):
        self.conn= None
        self.db_file= fr"Data\DB.db"
        self.create_connection()
      
    def create_connection(self):
        try:
            self.conn= sq.connect(self.db_file)
        except Error as e:
            messagebox.showerror("Error Connection DB",f"حصل الخطأ التالي أثناء الاتصال بقاعدة البيانات {e}")
            return self.conn


    def get_NewsUrl_from_db(self,id):
        query=f"select R.NewsURL from  Results R inner join cat C on R.Cat_id = C.id WHERE C.WebID =  {id}"
        data=self.fetch_query_get_results_as_data_frame(query)
        data_=pd.DataFrame(data)
        if data_.shape[0] ==0:
            return []
        return data_['NewsURL'].unique().tolist()



    def execute_query(self, query, params=None):
        if not self.conn:
            self.create_connection()
        try:
            cur = self.conn.cursor()
            if params:
                cur.execute(query, params)
            else:
                cur.execute(query)
            self.conn.commit()
            return cur
        except Error as e:
            print(f'Error: {e}')
            return None
    
    def get_row_news_by_url(self, url):
        query = """
            SELECT R.ID,
            C.WebSiteNameEN, C.WebSiteNameAR, C.CategoryEN, C.CategoryAR,
            R.NewsTitle, R.NewsDatePuplish, 
            CASE WHEN R.IsRead = 0 THEN 'غير مقروء' ELSE 'مقروء' END AS IsRead
            FROM Results R 
            INNER JOIN cat C ON R.Cat_id = C.id 
            WHERE R.NewsURL = ?"""
        cur = self.execute_query(query, (url,))
        if cur:
            result = cur.fetchone()  
            return result if result else None 
        return None
 


    def insert_into_results(self, data):
        if data:
            query = """
                INSERT INTO Results 
                (Cat_id, NewsTitle, NewsContain, NewsSummary, NewsDatePuplish,
                LastUpdate, NewsContainEN, NewsSummaryEN,NewsURL,Batch,IsRead) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?);
                """
            self.execute_query(query, data)
            

    def update_into_results(self,uuid,url):
        try:
            query = f"""
                UPDATE Results
                SET [Batch] = '{uuid}', [LastUpdate] = '{datetime.now()}'
                WHERE NewsURL = '{url}';
             """
            self.execute_query(query)
        except Exception as e:
            print(e)
           

    def update_readed(self,id):
        query = f"""update Results set IsRead = 1 where id = {id}"""
        self.execute_query(query)
      

    


    def fetch_query_get_results_as_data_frame(self,query, params=None):
        cur=self.execute_query(query, params)
        if cur:
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
            results = [dict(zip(columns, row)) for row in rows]
            return pd.DataFrame(results)
        else: return None
    

    def close_connection(self):
        if self.conn:
            self.conn.close()


    def initialize_database(self):
        try:
            create_table_query = """
            CREATE TABLE IF NOT EXISTS "Results" (
                "ID"	INTEGER NOT NULL UNIQUE,
                "Cat_id"	INTEGER,
                "NewsTitle"	TEXT,
                "NewsContain"	TEXT,
                "NewsSummary"	TEXT,
                "NewsDatePuplish"	TEXT,
                "LastUpdate"	TEXT,
                "NewsContainEN"	TEXT,
                "NewsSummaryEN"	TEXT,
                "NewsURL"	TEXT,
                "Batch"	TEXT,
                "IsRead" INTEGER,
                PRIMARY KEY("ID" AUTOINCREMENT)
            );
            """
            self.execute_query(create_table_query)
            
        
            query_create_cat="""CREATE TABLE IF NOT EXISTS "Cat" (
                        "ID"	INTEGER,
                        "WebID"	INTEGER,
                        "WebSiteURL"	TEXT,
                        "WebSiteNameEN"	TEXT,
                        "WebSiteNameAR"	TEXT,
                        "CategoryAR"  TEXT,
                        "CategoryEN" TEXT,
                        "CategoryURL"	TEXT,
                        "CategoryURL_Web"	TEXT
                    )"""
            self.execute_query(query_create_cat)
            print("database set")
        except sq.Error as e:
            print(f"Error while initializing database: {e}")


    
    def set_settings_web_in_cat(self):
        data = pd.read_json('Settings/web_settings.json')
        self.execute_query("delete from cat")
        for _,row in data.iterrows():
             self.execute_query('INSERT INTO Cat (ID, WebID, WebSiteURL, WebSiteNameEN, WebSiteNameAR, CategoryURL, CategoryURL_Web, CategoryAR, CategoryEN) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (row["ID"], row["WebID"], row["WebSiteURL"], row["WebSiteNameEN"], row["WebSiteNameAR"],
                    row["CategoryURL"], row["CategoryURL_Web"], row["CategoryAR"], row["CategoryEN"]))


    def get_full_data(self):
        query= """select R.ID,
                C.WebSiteNameEN, C.WebSiteNameAR, C.CategoryEN, C.CategoryAR,
                R.NewsTitle, R.NewsDatePuplish, case when R.IsRead ==0 then "غير مقروء" else "مقروء"  end as IsRead
                from  
                Results R inner join cat C on R.Cat_id = C.id 
                order by R.NewsDatePuplish desc
                """
        return self.fetch_query_get_results_as_data_frame(query)


    def get_news_url_by_id(self,id):
        query=f"""select NewsURL from Results WHERE id ={id} """
        df=self.fetch_query_get_results_as_data_frame(query=query)
        if not df.empty:
            return df.iloc[0, 0]
    

    def get_news_content_by_id(self, id):
        query = f"SELECT NewsContain FROM Results WHERE ID = {id}"
        return self.fetch_query_get_results_as_data_frame(query).iloc[0, 0]
    

    def get_web_id_by_news_id(self,news_id):
        query = f"SELECT C.WebID FROM Results R INNER JOIN cat C ON R.Cat_id = C.ID WHERE R.ID = {news_id}"
        return self.fetch_query_get_results_as_data_frame(query).iloc[0, 0]
    


# END:: sql Operations ____________________________





#################################################################################################################################
###############################################   SaveResults Excel class    ####################################################
#################################################################################################################################


## ________ BEGIN: SaveResults Excel class   ________::::::

class SaveResults_Excel:
        def __init__(self):
            self.date_time= datetime.now().strftime("%d-%m-%Y")
        # ازالة ورقة من ملف الاكسل
        def remove_sheet(self, excel_file, sheet_name):
            wb = px.load_workbook(excel_file)
            if sheet_name in wb.sheetnames:
                wb.remove(wb[sheet_name])
            wb.save(excel_file)

        # ازالة الحشو من المحتوى
        def rmove_duplecte_contatint(self,data_frame):
            final_data = pd.DataFrame(data_frame)
            def find_common_part(text1, text2):
                matcher = SequenceMatcher(None, text1, text2)
                match = matcher.find_longest_match(0, len(text1), 0, len(text2))
                if match.size > 100:
                    return text1[match.a: match.a + match.size]
                else:
                    return None
            try:
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
        

        # انشاء جدول في ملف اكسل
        def create_table(self,table_name, worksheet):
                table_style ='TableStyleMedium18'
                table = px.worksheet.table.Table(displayName=table_name, ref=worksheet.dimensions)
                table.tableStyleInfo = TableStyleInfo(name=table_style, showFirstColumn=False,
                showLastColumn=False, showRowStripes=True, showColumnStripes=False)
                worksheet.add_table(table)

        def save_result(self, dataframe=[]):
            empty_df = pd.DataFrame()
            self.son_folder = f'Outputs\Result {self.date_time}'
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
            except Exception as e:
                print(e)
                messagebox.showerror('حدث خطأ غير متوقع اثناء حفظ المخرجات',f'\n{e}\n')
            time.sleep(1)
        
 # END:: SaveResults Excel class  ____________________________
       




#################################################################################################################################
###############################################   Soup class    ####################################################
#################################################################################################################################


## ________ BEGIN: Soup class  ________::::::


class SoupOps:
    def __init__(self):
        pass
    global header_
    header_= {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                }
        
    def extract_articale_contain(self,url_link):
        full_text =[]
        content_text=''
        try:
            article_response = requests.get(url_link, header_)
            article_response.raise_for_status()
            soup = BeautifulSoup(article_response.text, 'html.parser')
           
            full_text = [element.get_text(strip=True) for element in soup.find_all(['p'])]         
            unique_paragraphs = []
            for paragraph in full_text:
                if paragraph not in unique_paragraphs:
                    unique_paragraphs.append(paragraph)
            content_text = '\n'.join(unique_paragraphs)
        except Exception as e:
             print(e)
             content_text='خطأ في جلب المحتوى'
        return content_text


    def get_title_and_contains(self,url_link):
        full_text =[]
        content_text=''
        try:
            article_response = requests.get(url_link, header_)
            article_response.raise_for_status()
            soup = BeautifulSoup(article_response.text, 'html.parser')

            title = soup.find('meta', property='og:title')['content']
            
            full_text = [element.get_text(strip=True) for element in soup.find_all(['p'])]         
            unique_paragraphs = []
            for paragraph in full_text:
                if paragraph not in unique_paragraphs:
                    unique_paragraphs.append(paragraph)
            content_text = '\n'.join(unique_paragraphs)
        except Exception as e:
             print(e)
             content_text='خطأ في جلب المحتوى'
        return content_text,title

         
    def get_soup(self,url,title):
        time.sleep(0.2)
        response = requests.get(url, headers=header_)
        return BeautifulSoup(response.content, title)


    def  convert_html_to_pdf(self, link,title, target):
        title=str(title).replace('\\','').replace('/','').replace(':','')
        from PyQt5.QtGui import QTextDocument
        from PyQt5.QtPrintSupport import QPrinter
        from PyQt5.QtWidgets import QApplication
        app = QApplication(sys.argv)
        headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        response = requests.get(link, headers=headers)
        if response.status_code == 200:
            
            soup = BeautifulSoup(response.text, "html.parser")
            for tag in soup(["script", "style", "meta", "noscript", "iframe", "img", "video"]):
                tag.decompose()

            html_content = soup.prettify()
            document = QTextDocument()
            document.setHtml(html_content)
            printer = QPrinter()
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(f"{target}\{title}_pdf.pdf")
            document.print_(printer)


# END:: Soup class class  ____________________________
       





#################################################################################################################################
###############################################   CheckDate class    ####################################################
#################################################################################################################################

## ________ BEGIN: CheckDate class  ________::::::


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
       





#################################################################################################################################
###############################################   get_news class    ####################################################
#################################################################################################################################

## ________ BEGIN: get_news class  ________::::::
    


class  GET_NEWS_FROM_WEBSITES(SoupOps):
    def __init__(self,settings):
        self.settings=settings
        self.web_data = self.settings.get('web_data')
        self.web_id=self.web_data['WebID'].iloc[0]
        last_days=self.web_data['period'].iloc[0]
        self.sql_db=SQL_DB()
        self.DateChecker=CheckDate(last_days)
        self.UUID=self.settings.get('UUID')
        self.after_stop_flag = self.settings.get('after_stop_flag', lambda: None)
        self.url_ids= self.sql_db.get_NewsUrl_from_db(self.web_id)
        self.update_traker_and_data=self.settings.get('update_traker_and_data', lambda: None)

    def extract_date_from_url(self,url):
        year_pattern = r'20\d{2}'
        match = re.search(year_pattern, url)
        if match:
            year = match.group()
            date = url[match.end():match.end()+6]
            return f'{year}{date}'
        else:
            return None
    

    def Alhal_net(self):
        for _,row in self.web_data.iterrows():
            page_index=0
            id=row['ID']
            CategoryEN=row['CategoryEN']
            CategoryURL=row['CategoryURL']
            cat_='7al'
            if CategoryEN=='Economic':
                cat_='economy'
            count_try=0
            link_cheacker=[]
            published_date=None
            while True and count_try<15:
                try:
                    url= CategoryURL.replace('#number#',str(page_index))
                    page_index+=1
                    if self.after_stop_flag():return
                    soup =self.get_soup(url, 'html.parser')
  
                    for article in soup.find_all('a'):
                        if self.after_stop_flag():return
                        link = article.find('a', href=True)['href']
                        link = unquote(link).strip().lower()
                        link=str(link).replace('\\','').replace('../','').replace(' ','').replace('"','')

                        if cat_ not in link: continue
                        if link in link_cheacker:continue
                        link_cheacker.append(link)
                        if link in self.url_ids:
                            self.sql_db.update_into_results(self.UUID,link)
                            continue
                        if self.after_stop_flag():return
                        posted_date = self.extract_date_from_url(link)
                        published_date = datetime.strptime(posted_date, "%Y/%m/%d").date()
                        if self.DateChecker.check_brake_scriping(published_date=published_date): break
                        if self.DateChecker.check_article_date(published_date=published_date): continue
                        
                        contain,title=self.get_title_and_contains(link)

                        data=(id, title,contain,'no_summary',published_date,datetime.now(),'na','na',link, self.UUID,0)
                        self.sql_db.insert_into_results(data)

                        row_show=self.sql_db.get_row_news_by_url(link)
                        self.update_traker_and_data(row_show)

                except Exception as e:
                    count_try+=1
                    print(f'error with alhal net: {e}')
                    pass
                if  published_date:   
                    if self.DateChecker.check_brake_scriping(published_date=published_date): break # كسر while
                

# __________________________________________________________________________________________________________

    def HalabToday(self):
        for _,row in self.web_data.iterrows():
            page_index=1
            id=row['ID']
            CategoryURL=row['CategoryURL']
            count_try=0
            link_cheacker=[]
            published_date=None
            while True and count_try<15:
                if self.after_stop_flag():return
                try:
                    url =f'{CategoryURL}/page/{str(page_index)}'
                    page_index+=1

                    soup =self.get_soup(url, 'html.parser')
                    
                    for article in soup.find_all('article'):
                        if self.after_stop_flag():return
                        link_tag = article.find('h3', class_='elementor-post__title').find('a', href=True)
                        if link_tag:
                            link = link_tag['href']
                            if link in link_cheacker:continue
                            link_cheacker.append(link)
                            if link in self.url_ids:
                                self.sql_db.update_into_results(self.UUID,link)
                                continue
                            article_soup =self.get_soup(link, 'html.parser')
                            meta_tag = article_soup.find('meta', property='article:published_time')
                            if meta_tag:full_published_date = meta_tag['content']
                            else: continue
                            date_string = full_published_date[:10]
                            published_date = datetime.strptime(date_string, "%Y-%m-%d")
                            published_date = published_date.date()
                            if self.DateChecker.check_brake_scriping(published_date=published_date):break
                            if self.DateChecker.check_article_date(published_date=published_date): continue
                            title_tag = article_soup.find('title')
                            title = title_tag.text.strip() if title_tag else ''
                            if self.after_stop_flag():return
                            contain=self.extract_articale_contain(link)
                            if self.after_stop_flag():return
                            data=(id, title,contain,'no_summary',published_date,datetime.now(),'na','na',link, self.UUID,0)
                            self.sql_db.insert_into_results(data)
                            row_show=self.sql_db.get_row_news_by_url(link)
                            self.update_traker_and_data(row_show)

                except Exception as e:
                    count_try+=1
                    print(f'error with halab today:  {e}')
                    pass
                if published_date:
                    if self.DateChecker.check_brake_scriping(published_date=published_date): break

# __________________________________________________________________________________________________________


    def Almodon(self):
        for index,row in self.web_data.iterrows():
            id=row['ID']
            CategoryEN=row['CategoryEN']
            CategoryURL=row['CategoryURL']
        
            if CategoryEN=='Politics':
                authers_id=['67c32a41-5633-4ab9-bd93-e9d0b28d09f1','e59b85ea-86c4-48a1-9048-0a5828bf9b1a','03ec43b8-d589-4623-abf4-69a0d645b295']
            
            elif CategoryEN=='Economic':
                authers_id=['45406ce3-e585-4ab7-9371-002420a22c37','3c8cf665-943e-449f-9f51-9c86a9740cc5','1e9a79d5-b3bf-424d-ba37-096c3c9516c9','0e736332-385a-4bef-b3c0-c8724a797e74']

            elif CategoryEN=='Arab & International':
                authers_id=['2cbb7f07-3395-4761-8220-1652169f0eee']

            for authers in authers_id:
                    page_index=1
                    link_cheacker=[]
                    count_try=0
                    published_date=None
                    while True and count_try<15:
                        if self.after_stop_flag():return
                        try:
                            url = str(CategoryURL).replace('#number#',str(page_index)).replace('hashid',authers)
                            page_index +=1
                            soup =self.get_soup(url, 'html.parser')
                            if self.after_stop_flag():return
                            for article in soup.find_all('div', class_='left-right-wrapper'):
                                if self.after_stop_flag():return
                                link = article.find('a', href=True)['href']
                                link = fr'https://www.almodon.com{unquote(link).strip().lower()}'
                                link=str(link).replace('\\','').replace('../','').replace(' ','').replace('"','')


                                if link in link_cheacker:continue
                                link_cheacker.append(link)
                                if link in self.url_ids:
                                    self.sql_db.update_into_results(self.UUID,link)
                                    continue
                                date_span = article.find('span', class_='date')
                                published_date = date_span.get_text() if date_span else None
                                published_date= datetime.strptime(published_date, '%Y/%m/%d').date()
                                if self.DateChecker.check_brake_scriping(published_date):break
                                if self.DateChecker.check_article_date(published_date):continue
                                title= str(urlparse(link).path.split('/')[-1]).replace('-', ' ')
                                if self.after_stop_flag():return
                                contain=self.extract_articale_contain(link)
                                if self.after_stop_flag():return
                                data=(id, title,contain,'no_summary',published_date,datetime.now(),'na','na',link, self.UUID,0)
                                self.sql_db.insert_into_results(data)
                                row_show=self.sql_db.get_row_news_by_url(link)
                                self.update_traker_and_data(row_show)
                        except Exception as e:
                            count_try+=1
                            print(f'error in almodon: {e}')
                            pass   
                        if published_date:
                            if self.DateChecker.check_brake_scriping(published_date):break # كسر while
   # __________________________________________________________________________________________________________


   # __________________________________________________________________________________________________________

    def Atharpress(self):
        for index,row in self.web_data.iterrows():
            page_index=1
            id=row['ID']
            CategoryURL=row['CategoryURL']
            link_cheacker=[]
            count_try=0
            published_date=None
            while True and count_try<15:
                try:
                    if self.after_stop_flag():return
                    url=f'{CategoryURL}page/{str(page_index)}/'
                    page_index +=1
                    soup =self.get_soup(url, 'html.parser')
                    if self.after_stop_flag():return
                    for article in soup.find_all('li', class_='list-post'): 
                        if self.after_stop_flag():return
                        h2_element = article.find('h2', class_='penci-entry-title entry-title grid-title')
                        a_element = h2_element.find('a')
                        link = a_element['href']
                        title = a_element.text.strip()
                        if link in link_cheacker:continue
                        link_cheacker.append(link) 
                        if link in self.url_ids:
                            self.sql_db.update_into_results(self.UUID,link)
                            continue
                        time_element = article.find('time', class_='entry-date published')
                        datetime_value = time_element['datetime']
                        published_date = datetime_value[:10]
                        published_date= datetime.strptime(published_date.replace(' ',''), "%Y-%m-%d").date()
                        if self.DateChecker.check_brake_scriping(published_date):break
                        if self.DateChecker.check_article_date(published_date):continue
                        if self.after_stop_flag():return
                        contain=self.extract_articale_contain(link)
                        if self.after_stop_flag():return
                        data=(id, title,contain,'no_summary',published_date,datetime.now(),'na','na',link, self.UUID,0)
                        self.sql_db.insert_into_results(data)
                        row_show=self.sql_db.get_row_news_by_url(link)
                        self.update_traker_and_data(row_show)
                except Exception as e:
                    count_try+=1
                    print(f'error with Atharpress {e}')
                    pass
                if published_date:
                    if self.DateChecker.check_brake_scriping(published_date):
                        break # كسر while

 

        
 # __________________________________________________________________________________________________________

    def EconomyDay(self):
        for _,row in self.web_data.iterrows():
            page_index=1
            id=row['ID']
            CategoryURL=row['CategoryURL']
            link_cheacker=[]
            count_try=0
            published_date=None
            while True and count_try<20:
                try:
                    if self.after_stop_flag():return
                    url = f'{CategoryURL}{str(page_index)}'
                    page_index+=1
                    soup = self.get_soup(url,'html.parser')  
                    articles = soup.find_all('div', class_='categoryblog')
                    for article in articles: 
                        if self.after_stop_flag():return 
                        parent_div = article.find_parent('div')  
                        date_div = parent_div.find('div', class_='posted-date')
                        if date_div:
                            published_date = date_div.a.text.strip()
                            published_date = datetime.strptime(published_date, "%Y-%m-%d").date()
                            if self.DateChecker.check_brake_scriping(published_date):break
                            if self.DateChecker.check_article_date(published_date):continue

                        link_tag = article.find('a')
                        if link_tag and 'href' in link_tag.attrs:
                            article_link = link_tag['href']
                            article_title = link_tag.text.strip()

                        if not link_tag : continue
                        cleaned_link = unquote(article_link).strip().lower()
                        cleaned_link=str(cleaned_link).replace('\\','').replace('../','').replace(' ','').replace('"','')
                        link = f'https://www.economy2day.com/{cleaned_link}'
                        if link in link_cheacker:continue
                        link_cheacker.append(link)   
                        if link in self.url_ids:
                            self.sql_db.update_into_results(self.UUID,link)
                            continue
                        title = article_title
                        if self.after_stop_flag():return
                        contain=self.extract_articale_contain(link)
                        if self.after_stop_flag():return
                        data=(id, title,contain,'no_summary',published_date,datetime.now(),'na','na',link, self.UUID,0)
                        self.sql_db.insert_into_results(data)
                        row_show=self.sql_db.get_row_news_by_url(link)
                        self.update_traker_and_data(row_show)
                        
                except Exception as e:
                    count_try+=1
                    print(f'error with EconomyDay {e}')
                    pass

                if published_date:
                    if self.DateChecker.check_brake_scriping(published_date):
                        break # كسر while


        
      
 # __________________________________________________________________________________________________________

    def EnabBaladi(self):
        for index,row in self.web_data.iterrows():
            page_index=1
            id=row['ID']
            CategoryURL=row['CategoryURL']
            link_cheacker=[]
            count_try=0
            published_date=None
            while True and count_try<20:
                try:
                    if self.after_stop_flag(): return
                    url = f'{CategoryURL}{page_index}'
                    page_index+=1
                    soup =self.get_soup(url, 'html.parser')
                    if id == 61 :
                        articls= soup.find_all('div', class_='col-lg-3')
                    else:
                        articls= soup.find_all('article', class_='col-lg-3')
                    
                    for article in articls:
                        if self.after_stop_flag():return
                        if id==61:
                            author = article.find("p", class_="author-name").text.strip()
                            title = article.find("h3").text.strip()
                            title =f'{author}||{title}'
                            link = article.find("div", class_="item-content").find("a")["href"]
                            published_date = article.find("samp").text.strip()
                            published_date=datetime.strptime(published_date, "%d/%m/%Y")
                            published_date=published_date.date()
                        else:
                            try:
                                published_date =  article.find('div', class_='item-content').find_all('samp')[-1].text
                                published_date = published_date.replace(', ','-')
                            except: published_date = None
                            published_date =self.DateChecker.convert_arabic_date_enab(published_date) 
                            title = article.find('h3').text.strip()
                            link = article.find('div', class_='item-content').find('a', href=True)['href']
                        link = f'{unquote(link).strip().lower()}'
                        link=str(link).replace('\\','').replace('../','').replace(' ','').replace('"','') 

                        if link in link_cheacker: continue
                        link_cheacker.append(link)
                        if link in self.url_ids:
                            self.sql_db.update_into_results(self.UUID,link)
                            continue

                        if self.DateChecker.check_article_date(published_date):continue
                        if self.DateChecker.check_brake_scriping(published_date):break
                        
                        if self.after_stop_flag():return
                        contain=self.extract_articale_contain(link)
                        if self.after_stop_flag():return
                        data=(id, title,contain,'no_summary',published_date,datetime.now(),'na','na',link, self.UUID,0)
                        self.sql_db.insert_into_results(data)
                        row_show=self.sql_db.get_row_news_by_url(link)
                        self.update_traker_and_data(row_show)

                except Exception as e:
                    count_try+=1
                    print(f'error with EnabBaladi :  {e}')
                    pass
                
                if published_date:
                    if self.DateChecker.check_brake_scriping(published_date):
                        break # كسر while

       
     

# __________________________________________________________________________________________________________
    def Eqtesad(self):
        for index,row in self.web_data.iterrows():
            page_index=1
            id=row['ID']
            CategoryURL=row['CategoryURL']
            link_cheacker=[]
            count_try=0
            published_date=None
            while True and count_try<20:
                if self.after_stop_flag(): return
                try:
                    url = f'{CategoryURL}{page_index}/'
                    page_index+=1
                    if self.after_stop_flag(): return
                    soup =self.get_soup(url, 'html.parser')
                    for article in soup.find_all('div', class_='post-style2'):
                        if self.after_stop_flag():return
                        link = article.find('a', href=True)['href']
                        if link in link_cheacker:continue
                        link_cheacker.append(link)
                        if link in self.url_ids:
                            self.sql_db.update_into_results(self.UUID,link)
                            continue
                        date_tag = article.find('div', class_='date').find_all('a', title=True)[-1]
                        published_date = date_tag.text.strip()
                        published_date = self.DateChecker.convert_arabic_date(published_date)
                        if self.DateChecker.check_brake_scriping(published_date):break
                        if self.DateChecker.check_article_date(published_date):continue
                        title = article.find('h3').find('a').text.strip() 
                        if self.after_stop_flag():return
                        contain=self.extract_articale_contain(link)
                        if self.after_stop_flag():return
                        data=(id, title,contain,'no_summary',published_date,datetime.now(),'na','na',link, self.UUID,0)
                        self.sql_db.insert_into_results(data)
                        row_show=self.sql_db.get_row_news_by_url(link)
                        self.update_traker_and_data(row_show)
                except Exception as e:
                    count_try+=1
                    print(f'error with Eqtesad :  {e}')
                    pass

                if published_date:
                    if self.DateChecker.check_brake_scriping(published_date):
                        break # كسر while


# __________________________________________________________________________________________________________

    def Kassioun(self):
        for index,row in self.web_data.iterrows():
            page_index=0
            id=row['ID']
            CategoryURL=row['CategoryURL']
            link_cheacker=[]
            count_try=0
            published_date=None
            while True and count_try<20:
                if self.after_stop_flag(): return
                try:
                    url = f'{CategoryURL}{page_index}0'
                    page_index+=1
                    if self.after_stop_flag():return
                    soup =self.get_soup(url, 'html.parser')
                    for article in soup.find_all('article', class_='item-view blog-view'):
                        if self.after_stop_flag():return
                        link = unquote(article.find('a', href=True)['href']).strip().lower()
                        link = f'https://kassioun.org/{link}'
                        if link in link_cheacker:continue
                        link_cheacker.append(link)
                        if link in self.url_ids:
                            self.sql_db.update_into_results(self.UUID,link)
                            continue
                        published_date = datetime.strptime(self.extract_date_from_url(link), "%Y-%m-%d").date()
                        if self.DateChecker.check_brake_scriping(published_date):break
                        if self.DateChecker.check_article_date(published_date):continue
                        title= article.find('h2', class_='item-title').find('a').text.strip()
                        if self.after_stop_flag():return
                        contain=self.extract_articale_contain(link)
                        if self.after_stop_flag():return
                        data=(id, title,contain,'no_summary',published_date,datetime.now(),'na','na',link, self.UUID,0)
                        self.sql_db.insert_into_results(data)
                        row_show=self.sql_db.get_row_news_by_url(link)
                        self.update_traker_and_data(row_show)
               
                except Exception as e:
                    count_try+=1
                    print(f'error with Kassioun :  {e}')
                    pass    
                
                if published_date:
                    if self.DateChecker.check_brake_scriping(published_date):
                        break # كسر while

        
# __________________________________________________________________________________________________________

    def Sana(self):
        for index,row in self.web_data.iterrows():
            page_index=1
            id=row['ID']
            CategoryURL=row['CategoryURL']
            link_cheacker=[]
            count_try=0
            published_date=None
            while True and count_try<20:
                if self.after_stop_flag(): return
                try:
                    if self.after_stop_flag():return
                    url = f'{CategoryURL}&paged={page_index}'
                    page_index+=1
                    soup = self.get_soup(url,'html.parser')
                    for article in soup.find_all('article', class_='item-list'):
                        if self.after_stop_flag():return
                        link = article.find('a')['href']
                        title = unquote(article.find('a').text).strip().lower()
                        if link in link_cheacker:continue
                        link_cheacker.append(link)
                        if link in self.url_ids:
                            self.sql_db.update_into_results(self.UUID,link)
                            continue
                        article_date = article.find(class_='tie-date').text.strip()
                        published_date = datetime.strptime(article_date, "%Y-%m-%d")
                        published_date = published_date.date()
                        if self.DateChecker.check_brake_scriping(published_date):break
                        if self.DateChecker.check_article_date(published_date):continue
                        if self.after_stop_flag():return
                        contain=self.extract_articale_contain(link)
                        if self.after_stop_flag():return
                        data=(id, title,contain,'no_summary',published_date,datetime.now(),'na','na',link, self.UUID,0)
                        self.sql_db.insert_into_results(data)
                        row_show=self.sql_db.get_row_news_by_url(link)
                        self.update_traker_and_data(row_show)
                except Exception as e:
                    count_try+=1
                    print(f'error with Kassioun :  {e}')
                    pass    
                
                if published_date:
                    if self.DateChecker.check_brake_scriping(published_date):
                        break # كسر while
                  
        
    # __________________________________________________________________________________________
    def ShamNetwork(self):
        for _,row in self.web_data.iterrows():
            page_index=1
            id=row['ID']
            CategoryURL=row['CategoryURL']
            link_cheacker=[]
            count_try=0
            published_date=None
            while True and count_try<20:
                if self.after_stop_flag():
                    return
                try:
                    url= f'{CategoryURL}{str(page_index)}'
                    page_index+=1
                    art_soup =self.get_soup(url, 'html.parser')
                    articles = art_soup.find_all('div',class_='cat-item')
 
                    for article in articles:
                        if self.after_stop_flag():
                            return
                        link = article.a['href']
                        link = 'https://shaam.org' + str(link).replace('../','')
                        if link in link_cheacker:continue
                        link_cheacker.append(link)
                        if link in self.url_ids:
                            self.sql_db.update_into_results(self.UUID,link)
                            continue
                        
                        title = article.find('div', class_='item-title').text.strip()
                        date_text = article.find('span', class_='item-date').text.strip()
                        published_date= self.DateChecker.convert_arabic_date_sham(date_text)
                        if self.DateChecker.check_brake_scriping(published_date):break
                        if self.DateChecker.check_article_date(published_date):continue
                        content_paragraphs = article.find('div', class_='item-text').find_all('p')
                        if self.after_stop_flag():
                            return
                        contain = '\n'.join([paragraph.text.strip() for paragraph in content_paragraphs])
                        data=(id, title,contain,'no_summary',published_date,datetime.now(),'na','na',link, self.UUID,0)
                        self.sql_db.insert_into_results(data)
                        row_show=self.sql_db.get_row_news_by_url(link)
                        self.update_traker_and_data(row_show)

                except Exception as e:
                    count_try+=1
                    print(f'error with Kassioun :  {e}')
                    pass    
                
                if published_date:
                    if self.DateChecker.check_brake_scriping(published_date):
                        break # كسر while
                         
        
    # __________________________________________________________________________________________

    def Syria_TV(self):
        for index,row in self.web_data.iterrows():
            page_index=1
            id=row['ID']
            CategoryURL=row['CategoryURL']
            link_cheacker=[]
            count_try=0
            published_date=None
            while True and count_try<20:
                if self.after_stop_flag():return
                try:
                    url = f'{CategoryURL}?page={page_index-1}'
                    page_index+=1
                    if self.after_stop_flag():return
                    soup =self.get_soup(url, 'html.parser')

                    for article in soup.find_all('div', class_='bs-region bs-region--right'):
                        if self.after_stop_flag():
                            return
                        link = article.find('a', href=True)['href']
                        link_ =  f'{unquote(link).strip().lower()}' 

                        link = f'https://www.syria.tv{link_}'
                        if link in link_cheacker:continue
                        link_cheacker.append(link)
                        if link in self.url_ids:
                            self.sql_db.update_into_results(self.UUID,link)
                            continue

                        title = article.find("div", class_="field--name-node-title").find("a").text.strip()
                        published_date = article.find("div", class_="field--name-field-published-date").text.strip()
                        published_date = self.DateChecker.convert_arabic_date(published_date)
                        if self.DateChecker.check_brake_scriping(published_date):break
                        if self.DateChecker.check_article_date(published_date):continue
                        
                        if self.after_stop_flag(): return
                        contain=self.extract_articale_contain(link)
                        if self.after_stop_flag():return
                        data=(id, title,contain,'no_summary',published_date,datetime.now(),'na','na',link, self.UUID,0)
                        self.sql_db.insert_into_results(data)
                        row_show=self.sql_db.get_row_news_by_url(link)
                        self.update_traker_and_data(row_show)

                except Exception as e:
                    count_try+=1
                    print(f'error with Kassioun :  {e}')
                    pass    
                
                if published_date:
                    if self.DateChecker.check_brake_scriping(published_date):
                        break # كسر while

        
    # __________________________________________________________________________________________

    def HoranNews(self):
        for index,row in self.web_data.iterrows():
            page_index=1
            id=row['ID']
            CategoryURL=row['CategoryURL']
            link_cheacker=[]
            count_try=0
            published_date=None
            while True and count_try<20:
                if self.after_stop_flag():return
                try:
                    url = f'{CategoryURL}{page_index}'
                    page_index+=1
                    if self.after_stop_flag():return
                    soup =self.get_soup(url, 'html.parser')
                    for article in soup.find_all("li", class_="post-item"):
                        if self.after_stop_flag(): return
                        title_tag = article.find("h2", class_="post-title").find("a")
                        link = title_tag["href"] if title_tag else None
                        title = title_tag.text.strip() if title_tag else None
                        if link in link_cheacker:continue
                        link_cheacker.append(link)
                        if link in self.url_ids:
                            self.sql_db.update_into_results(self.UUID,link)
                            continue
                        published_date = article.find("span", class_="date")
                        published_date = published_date.text.strip().replace("،","") if published_date else None

                        published_date = self.DateChecker.convert_arabic_date_horanfree(published_date) 
    
                        if self.DateChecker.check_brake_scriping(published_date):break
                        if self.DateChecker.check_article_date(published_date):continue
                        
                        if self.after_stop_flag(): return
                        contain=self.extract_articale_contain(link)
                        if self.after_stop_flag():return
                        data=(id, title,contain,'no_summary',published_date,datetime.now(),'na','na',link, self.UUID,0)
                        self.sql_db.insert_into_results(data)
                        row_show=self.sql_db.get_row_news_by_url(link)
                        self.update_traker_and_data(row_show)

                except Exception as e:
                    count_try+=1
                    print(f'error with Kassioun :  {e}')
                    pass    
                
                if published_date:
                    if self.DateChecker.check_brake_scriping(published_date):
                        break # كسر while
     
    # __________________________________________________________________________________________

    def Alkhabar(self):
        for index,row in self.web_data.iterrows():
            page_index=1
            id=row['ID']
            CategoryURL=row['CategoryURL']
            link_cheacker=[]
            count_try=0
            published_date=None
            while True and count_try<20:
                if self.after_stop_flag():return
                try:
                    url = f'{CategoryURL}{page_index}'
                    page_index+=1
                    if self.after_stop_flag():return
                    soup =self.get_soup(url, 'html.parser')
                 
                    for article in soup.find_all("li", class_="post-item"):
                        if self.after_stop_flag(): return
                        title_tag = article.find("h2", class_="post-title").find("a")
                        link = title_tag["href"] if title_tag else None
                        title = title_tag.text.strip() if title_tag else None
                
                        if link in link_cheacker:continue
                        link_cheacker.append(link)
                        if link in self.url_ids:
                            self.sql_db.update_into_results(self.UUID,link)
                            continue

                        published_date =article.find("span", class_="date").text.strip()
                        published_date = datetime.strptime(published_date, "%Y-%m-%d").date()


                    
                        if self.DateChecker.check_brake_scriping(published_date):break
                        if self.DateChecker.check_article_date(published_date):continue
                        
                        if self.after_stop_flag(): return
                        contain=self.extract_articale_contain(link)
                        if self.after_stop_flag():return
                        data=(id, title,contain,'no_summary',published_date,datetime.now(),'na','na',link, self.UUID,0)
                        self.sql_db.insert_into_results(data)
                        row_show=self.sql_db.get_row_news_by_url(link)
                        self.update_traker_and_data(row_show)

                except Exception as e:
                    count_try+=1
                    print(f'error with Kassioun :  {e}')
                    pass    
                
                if published_date:
                    if self.DateChecker.check_brake_scriping(published_date):
                        break # كسر while
    # __________________________________________________________________________________________

    def SyriaNews(self):
        for index,row in self.web_data.iterrows():
            page_index=1
            id=row['ID']
            CategoryURL=row['CategoryURL']
            link_cheacker=[]
            count_try=0
            published_date=None
            while True and count_try<20:
                if self.after_stop_flag():return
                try:
                    url = CategoryURL.replace("*****",str(page_index))
                    page_index+=1
                    if self.after_stop_flag():return
                    soup =self.get_soup(url, 'html.parser')
                 
                    for article in soup.find_all("li", class_="search-item clearfix azr"):
                        if self.after_stop_flag(): return
                        
                        raw_link = article.find("h2", class_="search-title").a["href"]
                        raw_link=raw_link.replace("ID","ID*ID")
                        parts = raw_link.split('-ID*')
                        arabic_text = parts[0].strip() 
                        other_part = parts[1].strip()

                        link=f'https://syria.news/{arabic_text}-{other_part}'
                                    
                        title = article.find("h2", class_="search-title").a.text.strip()
                        
                        if link in link_cheacker:continue
                        link_cheacker.append(link)
                        if link in self.url_ids:
                            self.sql_db.update_into_results(self.UUID,link)
                            continue

                        published_date =article.find("div", class_="col-md-3 search-titlex").a.text.strip()
                        date_str = published_date.split("|")[0].strip()
                        date_obj = datetime.strptime(date_str, "%d.%m.%Y")  
                        published_date = date_obj.strftime("%Y-%m-%d")

                        published_date = datetime.strptime(published_date, "%Y-%m-%d").date()
                    
                        if self.DateChecker.check_brake_scriping(published_date):break
                        if self.DateChecker.check_article_date(published_date):continue
                        
                        if self.after_stop_flag(): return
                        contain=self.extract_articale_contain(link)
                        if self.after_stop_flag():return
                        data=(id, title,contain,'no_summary',published_date,datetime.now(),'na','na',link, self.UUID,0)
                        self.sql_db.insert_into_results(data)
                        row_show=self.sql_db.get_row_news_by_url(link)
                        self.update_traker_and_data(row_show)

                except Exception as e:
                    count_try+=1
                    print(f'error with Kassioun :  {e}')
                    pass    
                
                if published_date:
                    if self.DateChecker.check_brake_scriping(published_date):
                        break # كسر while

 # __________________________________________________________________________________________

    def Alikhbariah(self):
        for index,row in self.web_data.iterrows():
            page_index=1
            id=row['ID']
            CategoryURL=row['CategoryURL']
            link_cheacker=[]
            count_try=0
            published_date=None
            while True and count_try<20:
                if self.after_stop_flag():return
                try:
                    url = f'{CategoryURL}{str(page_index)}/'
                    page_index+=1
                    if self.after_stop_flag():return
                    soup =self.get_soup(url, 'html.parser')
                 
                    for article in soup.find_all("div", class_="elementor-post__text"):
                        if self.after_stop_flag(): return

                        a_tag = article.find('h3', class_='elementor-post__title').find('a')
                        title = a_tag.text.strip()
                        link = a_tag['href']
                        link= unquote(link).strip().lower()
                        date = soup.find('span', class_='elementor-post-date').text.strip().replace(",","")
                        published_date=self.DateChecker.convert_arabic_date_akh(date)

                        if link in link_cheacker:continue
                        link_cheacker.append(link)
                        if link in self.url_ids:
                            self.sql_db.update_into_results(self.UUID,link)
                            continue

                    
                        if self.DateChecker.check_brake_scriping(published_date):break
                        if self.DateChecker.check_article_date(published_date):continue
                        
                        if self.after_stop_flag(): return
                        contain=self.extract_articale_contain(link)
                        if self.after_stop_flag():return
                        data=(id, title,contain,'no_summary',published_date,datetime.now(),'na','na',link, self.UUID,0)
                        self.sql_db.insert_into_results(data)
                        row_show=self.sql_db.get_row_news_by_url(link)
                        self.update_traker_and_data(row_show)

                except Exception as e:
                    count_try+=1
                    print(f'error with Alikhbariah :  {e}')
                    pass    
                
                if published_date:
                    if self.DateChecker.check_brake_scriping(published_date):
                        break # كسر while

#################################################################################################################################
###############################################   GETNEWS class    ####################################################
#################################################################################################################################

       


       
        