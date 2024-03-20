import requests
from bs4 import BeautifulSoup

url = 'https://247sports.com/college/penn-state/Season/2025-Football/CurrentTargetPredictions/'
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}

web_page = requests.get(url, headers=headers)
soup = BeautifulSoup(web_page.content, "html.parser")

target_html_list = soup.find_all(class_="target")

for target_html in target_html_list:
    ul = target_html.find('ul')
    name_html = ul.find("li", class_="name")
    print(name_html.find('a')['href'])
    print(name_html.find('a').contents[0].strip())
    print()