import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import pandas as pd
import uuid
import threading
import concurrent.futures
import webbrowser
import os
from PIL import Image



#### get class
from SyriaNews.DbOperations import SQL_DB
from SyriaNews.SoupOperations import SoupOps
from SyriaNews.GetNews import GET_NEWS_FROM_WEBSITES


class news(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, border_width=1, height=700, width=1100, corner_radius=0)
        self.SQL=SQL_DB()
        self.SQL.initialize_database()
        self.SQL.set_settings_web_in_cat()


        self.main_frame = ctk.CTkFrame(self, fg_color='transparent')
        self.main_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=2)


        self.hint_label = ctk.CTkLabel(self, text="📢 لقراءة محتوى الخبر، انقر عليه مرتين", font=('Segoe UI', 15, 'bold'), text_color="red")
        self.hint_label.grid(row=2, column=0, sticky="ew", padx=5, pady=2)
        self.pulse_animation(size=14, growing=True, count=0)


        self.original_data = self.SQL.get_full_data()  
        self.data = self.original_data.copy()
        self.article_container=None
        self.delete_old_news() # حذف الاخبار اقدم من 7 ايام تلقائيا
        

        
        self.show_table_summary() # عرض الجدول
        self.is_stoped=False


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


    # تصميم جدول العرض -----------------------------
    def show_table_summary(self):
        self.header_set = {'SN':50,'ID': 75, 'WebSiteNameEN': 150, 'WebSiteNameAR': 125, 'CategoryEN': 150, 'CategoryAR': 150, 'NewsTitle': 550, 'NewsDatePuplish': 200,'IsRead':100}
        self.headers_=list(self.header_set.keys())
        self.sort_orders = {col: True for col in self.headers_}
        
        style = ttk.Style(self.main_frame)
        style.configure("Treeview", background="black", foreground="black", rowheight=30, fieldbackground="#f9f9f9")
        style.configure("Treeview.Heading", font=('Segoe UI', 13, 'bold'),  background="#007ba0", foreground="#007ba0",  fieldbackground="#9d17d6")
        style.map("Treeview", background=[("selected", "#007ba0")])

        # إنشاء جدول Treeview
        self.tree = ttk.Treeview(self.main_frame, columns=self.headers_, show="headings", height=25)
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
        self.scroll_y = ttk.Scrollbar(self.main_frame, orient="vertical", command=self.tree.yview)
        self.scroll_x = ttk.Scrollbar(self.main_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=self.scroll_y.set, xscrollcommand=self.scroll_x.set)

   
        self.filter_frame = ctk.CTkFrame(self.main_frame, fg_color='transparent')
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
        from SyriaNews.SetResource import Resource
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
            from SyriaNews.SaveResults import SaveResults_Excel
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
    
        logo_ = self.load_icone_from_path(fr"Icons/{web_id}.png",size=(60, 60))

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
