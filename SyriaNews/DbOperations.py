from tkinter import messagebox
import sqlite3 as sq
from sqlite3 import Error
import pandas as pd
from datetime import datetime


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
    
