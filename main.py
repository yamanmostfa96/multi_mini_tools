import os
import customtkinter as ctk
import datetime
from PIL import Image
import datetime


from Modails.ConvertExcelToJson import ConverterToJson
from Modails.ConvertExcelToPdf import ConverterXlsPdf
from Modails.FilesTracker import FilesTracker




class APP(ctk.CTk): # واجهة التطبيق الرئيسية
   
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("mini tools")
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.geometry(f"{screen_width}x{screen_height}+0+0")
        
        self.current_frame = None
        
        # إنشاء إطار جانبي
        self.frame_set_page = ctk.CTkScrollableFrame(self, border_width=1,width=180)
        self.frame_set_page.pack(side='left', fill='y', padx=2, pady=0)
        #self.frame_set_page.pack_propagate(False)
        self.global_font='White'
      
        self.clock_label = ctk.CTkLabel(self.frame_set_page, text="", font=("Bahnschrift", 11))
        self.clock_label.pack(pady=10, padx=5)
        self.update_clock()
        

        self.root_frame = ctk.CTkFrame(self, border_width=0, height=screen_height, width=screen_width-150)
        self.root_frame.pack(side='right', fill='both', expand=True)

        self.buttons = [
            ("Excel to JSON", lambda: self.switch_frame("Excel to JSON"), fr"Icons\ExcelTojson.png", (50, 30))
            ,("Excel Folder to PDF", lambda: self.switch_frame("Excel Folder to PDF"), fr"Icons\ExcelToPdf.png", (50, 30))
            ,("Track my Files", lambda: self.switch_frame("Track my Files"), fr"Icons\folder_tracker_icone.png", (40, 40))
            ,("Split Excel File", lambda: self.switch_frame("Split Excel File"), fr"Icons\Splitter.png", (50, 50))
            ,("Syria News", lambda: self.switch_frame("Syria News"), fr"Icons\syria_.png", (50, 50))
            
        ]

        # انشاء ازار استدعاء الادوات
        for text, command, icon, image_size in self.buttons:
            button = ctk.CTkButton(
                self.frame_set_page, text=text, command=command, 
                font=('Segoe UI Semibold', 12),
                image=self.load_image_from_path(icon, image_size), compound="top", 
                corner_radius=0, fg_color="transparent",bg_color="transparent", hover_color="#A9C1A6",
                width=150, height=75, border_width=0, border_color="#A9C1A6"
            )
            button.pack(fill='x', pady=5, padx=2)
        
       
        # زر تبديل الثيم
        self.is_dark_theme = True
        self.theme_button_var = ctk.StringVar(value="on")
        self.theme_button = ctk.CTkSwitch(
                            self.frame_set_page, text="Dark mode", command=self.toggle_theme,
                            variable=self.theme_button_var, onvalue="on", offvalue="off")
        self.theme_button.pack(pady=10,padx=2, fill='x')
        
        # زر الخروج
        self.exit_app = ctk.CTkButton(
            self.frame_set_page, text='Exit App', width=100, height=30,
            command=self.Exit_con_app, font=("Bahnschrift", 12),
            corner_radius=5, fg_color="#AA1A15")
        self.exit_app.pack(pady=10, fill='x', padx=5)

    

    # فانكشن لتحديث الساعة على الواجهة الرئيسية
    def update_clock(self):
        now = datetime.datetime.now()
        self.clock_label.configure(text=now.strftime("%Y-%m-%d %H:%M:%S"))
        self.after(1000, self.update_clock)

    
    # فانكشن لتحويل الى الوضع الداكن او العكس
    def toggle_theme(self):
        self.is_dark_theme = not self.is_dark_theme
        ctk.set_appearance_mode("dark" if self.is_dark_theme else "light")
        self.text_color_global= "black" if ctk.get_appearance_mode() == "Light" else "white"
        self.update_buttons_theme()
    
    # فانكشن لتحديث لون الازرار حسب الثيم الحالي
    def update_buttons_theme(self):
        def find_buttons(widget):
            for child in widget.winfo_children():
                if isinstance(child, ctk.CTkButton):
                    if child.cget("fg_color") != "transparent":
                        continue
                    child.configure(text_color=self.text_color_global)
                elif isinstance(child, ctk.CTkFrame):
                    find_buttons(child)
        try:find_buttons(self.current_frame)
        except: pass
        try:find_buttons(self.frame_set_page)
        except:pass


    # فانكشن لاغلاق التطبيق
    def Exit_con_app(self):
        self.destroy()

    # فانكشن لتحميل الصور من المسار بشكل صحيح
    def load_image_from_path(self, image_path, size=(20, 20)):
        try:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"File not found: {image_path}")

            image = Image.open(image_path)
            return ctk.CTkImage(light_image=image, dark_image=image, size=size)

        except FileNotFoundError: # اذا لم تجد الصورة استخدم صورة افتراضية
            default_image = Image.new("RGB", size, color="gray")
            return ctk.CTkImage(light_image=default_image, dark_image=default_image, size=size)

# فانكشن لتغيير الفريم الذي يتم عرض واجهة الاداة عليه
    def switch_frame(self, selection):
        if self.current_frame is not None:
            self.current_frame.pack_forget()

        if selection == "Excel to JSON":
            self.current_frame = ConverterToJson(self.root_frame)

        if selection =="Excel Folder to PDF":
            self.current_frame = ConverterXlsPdf(self.root_frame)

        if selection =="Track my Files":
            self.current_frame=FilesTracker(self.root_frame)

        if selection=='Split Excel File':
            from Modails.ExcelDfSplitter import ExcellSplitter
            self.current_frame=ExcellSplitter(self.root_frame)

        if selection =="Syria News":
            from SyriaNews.Face import news
            self.current_frame=news(self.root_frame)
     
        """if selection =="spellout Arabic Number":
            from Modails.Spellout import SpelloutARNmbers
            self.current_frame=SpelloutARNmbers(self.root_frame)
        """

        if self.current_frame is not None: 
            self.current_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.update_buttons_theme()

    
    

if __name__ == "__main__":
    app= APP()
    app.mainloop()