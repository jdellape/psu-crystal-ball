import requests
from bs4 import BeautifulSoup

def get_player_info(ul):
    name_html = ul.find("li", class_="name")
    name = name_html.find('a').contents[0].strip()
    web_page_url = name_html.find('a')['href']
    return (name, web_page_url)

def get_predicted_by_info(ul):
    predicted_by_html = ul.find("li", class_="predicted-by")
    predicted_by_name = predicted_by_html.find('a').find('span').text.strip()
    return predicted_by_name

def get_prediction_info(ul):
    prediction_team = ""
    prediction_html = ul.find("li", class_="prediction")
    try:
        prediction_team = prediction_html.find('img')['alt']
    except:
        pass
    prediction_date = prediction_html.find('span', class_="prediction-date").text.strip()
    return (prediction_team, prediction_date)


url = 'https://247sports.com/college/penn-state/Season/2025-Football/CurrentTargetPredictions/'
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}

web_page = requests.get(url, headers=headers)
soup = BeautifulSoup(web_page.content, "html.parser")

target_html_list = soup.find_all(class_="target")

data = []

# Items I want to extract: target name, link to target page, predicted by, prediction team, prediction time
for target_html in target_html_list:
    ul = target_html.find('ul')
    target_name, target_link = get_player_info(ul)
    prediction_team, prediction_date = get_prediction_info(ul)
    predicted_by_name = get_predicted_by_info(ul)
    data.append({'player_name':target_name, 'player_url':target_link,
                 'predicted_by':predicted_by_name, 'prediction_date':prediction_date,
                 'predicted_team':prediction_team,
                 'prediction_id': f"{target_name}_{predicted_by_name}_{prediction_date}_{prediction_team}"})
    # print(f"""New crystal ball for Penn State target {target_name} submitted by {predicted_by_name} at {prediction_date}. Predicted Destination: {prediction_team}.
    #        Find more player info here: {target_link}""")

# Grab the latest prediction and store as .env var
latest_prediction = data[0]['prediction_id']
print(latest_prediction)