from customtkinter import  CTkFrame
from tksheet import Sheet


class TableSheet(CTkFrame):
    def __init__(self, parent, data, width, hight, header=[],column_widths=None,align_center=None):
        super().__init__(parent)
        self.data = data
        self.width=width
        self.hight=hight
        self.header =header
        self.column_widths=column_widths
        self.align_center=align_center

        self.sheet = Sheet(self,header=self.header, data=self.data, width=self.width, height=self.hight,
                             font=('Bahnschrift', 10,'bold'),
                             header_font=('segoe', 12, 'bold'),
                             header_align="center")
        self.formating_data()
        self.sheet.grid(row=0, column=0, sticky="nsew")
        self.sheet.set_options(
                                header_bg="#4F585C",
                                header_fg="#FAFEFF",
                                auto_resize_columns=250,
                                #table_grid_fg='red',
                                table_bg="#333333",
                                
                                
                                )
        self.sheet.enable_bindings('all')               
        self.sheet.disable_bindings('cut','paste','delete','edit_cell','edit_header','edit_index')
        self.sheet.readonly(self.sheet.span("A:ZZ", header=True),readonly=True,)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.sheet.set_all_row_heights(30)
        self.sheet.set_header_height_pixels(35)
        

    def formating_data(self):
            if self.column_widths:
                for i, width in enumerate(self.column_widths):
                    try:self.sheet.column_width(column=i, width=width)
                    except:pass
            if self.align_center:
                try: self.sheet.align_columns(columns=self.align_center, align="center")
                except: pass
            self.alternate_row_colors()
            self.sheet.set_all_row_heights(26)
            self.sheet.set_header_height_pixels(35)
            
    def set_header(self, header):
        self.sheet.set_header_data(header)
            
    def alternate_row_colors(self):
        for row_index in range(self.sheet.get_total_rows()):
            if row_index % 2 == 0:
                self.sheet.highlight_rows(rows=row_index, bg='#DDE1DE')
            else:
                self.sheet.highlight_rows(rows=row_index, bg='#F9F9F9')
        

    def load_data(self, data):
        self.sheet.set_sheet_data(data)
        self.formating_data()


