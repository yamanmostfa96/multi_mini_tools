from datetime import datetime
import re
from urllib.parse import unquote
from datetime import datetime
from urllib.parse import  unquote,urlparse

from SyriaNews.SoupOperations import SoupOps
from SyriaNews.DbOperations import SQL_DB
from SyriaNews.DateChecker import CheckDate



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

       


       
        