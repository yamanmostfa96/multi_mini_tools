import pandas as pd
import customtkinter as ctk
from tkinter import ttk

class Table(ctk.CTkFrame):
    def __init__(self,
                parent,
                dataframe=None, 
                font_header=('Segoe UI', 13, 'bold'), 
                font_data=('Segoe UI', 10),
                columns_width=None,
                with_filter=True,
                with_sorter=True,
                align_center=[0],
                on_update_callback=True,
                with_index=True,
                
                ):
        super().__init__(parent)
        
        self.on_update_callback = on_update_callback
        self.dataset = pd.DataFrame(dataframe) if dataframe is not None else pd.DataFrame()
        
        self.font_header = font_header
        self.font_data = font_data

        self.with_filter=with_filter
        self.with_sorter=with_sorter
        
        self.align_center=align_center
        self.with_index=with_index

        self.data = self.dataset.copy()
        self.original_data = self.dataset.copy()
        self.header =  ['SN'] + self.original_data.columns.tolist()  if self.with_index else self.original_data.columns.tolist() 
        self.columns_width =  [50] + ([100] * len(self.header)) if not columns_width else [50] + columns_width
        self.sort_orders = {col: True for col in self.header}

        self.show_table()


    def show_table(self):
        # تصميم الجدول
        style = ttk.Style(self)
        style.configure("Treeview", background="white", font=self.font_data,borderwidth=2,relief="raised", foreground="black", rowheight=25)
        style.map("Treeview", background=[("selected", "#007ba0")])
        style.configure("Treeview.Heading", font=self.font_header, foreground="#2d1469", background="#2d1469")

        # إنشاء الجدول وعناصر التمرير
        self.tree = ttk.Treeview(self, columns=self.header, show="headings", height=20)
        self.scroll_y = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.scroll_x = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=self.scroll_y.set, xscrollcommand=self.scroll_x.set)
        
        

        for index, (col, width) in enumerate(zip(self.header, self.columns_width)):
            anchor = "center" if index in self.align_center else "w"  
            self.tree.column(col, width=width, anchor=anchor, stretch=False)
            
            if self.with_sorter:

                if col == "SN" :
                    if self.with_index:
                        self.tree.heading(col, text=f'{col}')
                    else: pass
                else:
                    self.tree.heading(col, text=f'↑ {col}' if self.with_sorter else col, 
                        anchor="w", 
                        command=lambda c=col: self.sort_column(c) if self.with_sorter else None)
            else:
                self.tree.heading(col, text=f'{col}', anchor="w")




        self.filter_entries = {}
       

        if self.with_filter:
            filter_frame = ctk.CTkFrame(self)
            filter_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=2)
            for col, width in zip(self.header, self.columns_width):
                entry = ctk.CTkEntry(filter_frame, placeholder_text=f"ʘ تصفية {col}", width=width//1.3, font=(self.font_data,10))
                entry.pack(side="left", padx=2, pady=2)
                entry.bind("<KeyRelease>", lambda event, c=col: self.apply_filter())
                self.filter_entries[col] = entry
            
            filter_frame.grid_columnconfigure(0, weight=1)
        
        self.tree.grid(row=1, column=0, sticky="nsew")
        self.scroll_y.grid(row=1, column=1, sticky="ns")
        self.scroll_x.grid(row=2, column=0, sticky="ew")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
            
        


    def load_data(self):
        for i in self.tree.get_children():
            self.tree.delete(i) 
        if self.data.empty:
            return
        if self.with_index:
            self.data['SN'] = range(1, len(self.data) + 1)
            self.data = self.data[['SN'] + [col for col in self.data.columns if col != 'SN']]
            self.data=self.data.reset_index(drop=True)
    
        for index, row in self.data.iterrows():
            tag = "evenrow" if index % 2 == 0 else "oddrow"
            self.tree.insert("", "end", values=tuple(row), tags=(tag,))
        self.tree.tag_configure("evenrow", background="#dbe7e4")
        self.tree.tag_configure("oddrow", background="white")

        if self.on_update_callback:
            self.on_update_callback(len(self.tree.get_children()))

        

    def sort_column(self, col_name):
        """فرز العمود تصاعديًا أو تنازليًا"""
        if col_name not in self.data.columns:
            return
        ascending = self.sort_orders[col_name]
        self.data = self.data.sort_values(by=col_name, ascending=ascending, ignore_index=True)
        self.load_data()
        arrow = "↑" if ascending else "↓"
        self.tree.heading(col_name, text=f"{col_name} {arrow}")
        self.sort_orders[col_name] = not ascending



    def apply_filter(self):
        """تطبيق التصفية على البيانات"""
        self.data = self.original_data.copy()
        
        for col, entry in self.filter_entries.items():
            value = entry.get().strip().lower()
            if value:
                self.data = self.data[self.data[col].astype(str).str.lower().str.contains(value, na=False)]
        
        self.load_data()

