import requests
from bs4 import BeautifulSoup
import time
import sys





class SoupOps:
    def __init__(self):
        pass
    global header_
    header_= {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                }

    # وظيفة استخراج محتوى الخبر من رابط خبر  
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

    # وظيفة للحصول على المحتوى والعنوان من رابط خبر
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

    # وظيفة للحصول على هيكل صفحة الويب 
    def get_soup(self,url,title):
        time.sleep(0.2)
        response = requests.get(url, headers=header_)
        return BeautifulSoup(response.content, title)


    # وظيفة تحويل صفحة ويب الى ملف بي دي اف 
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
       