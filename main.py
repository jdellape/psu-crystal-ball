import os
import logging
import requests
from bs4 import BeautifulSoup
import pandas as pd
from etext import send_sms_via_email

# Auth vars for sending text
SMS_SENDER_ADDRESS = os.environ["SMS_SENDER_ADDRESS"]
SMS_SENDER_PASSWORD = os.environ["SMS_SENDER_PASSWORD"]
SMS_RECIPIENT_PHONE_NUMBER = os.environ["SMS_RECIPIENT_PHONE_NUMBER"]
SMS_PROVIDER = os.environ["SMS_PROVIDER"]

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

def get_recent_predictions(new_df, last_alert_id):
    # Find the index position where the last alert id is located in the df
    index = 0
    for idx, i in enumerate(list(new_df.prediction_id)):
        if i == last_alert_id:
            index = idx
    notification_records = new_df.to_dict('records')[:index]
    return notification_records

def main():
    # Configure logging
    log_level = logging.INFO
    logger = logging.getLogger()
    fmt_string = "[%(levelname)s]\t%(asctime)s.%(msecs)dZ at line %(lineno)d: %(message)s"
    logging.basicConfig(level=log_level, format=fmt_string, datefmt="%Y-%m-%dT%H:%M:%S")

    url = 'https://247sports.com/college/penn-state/Season/2025-Football/CurrentTargetPredictions/'
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}

    logger.info(f"Getting html contents from {url}...")
    # Scrape the web page and parse out what I want
    web_page = requests.get(url, headers=headers)
    soup = BeautifulSoup(web_page.content, "html.parser")

    target_html_list = soup.find_all(class_="target")

    data = []

    logger.info("Parsing data from html...")
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

    # Grab the latest prediction and log it
    website_latest_prediction = data[0]['prediction_id']
    logger.info(f"Latest prediction id from web page: {website_latest_prediction}")

    new_df = pd.DataFrame(data)

    latest_id_last_run = ""
    # Get latest id from previous scrapes and write newest id from this scrape to log
    with open("latest_id_log.txt", "r+") as f:
        latest_id_last_run = f.readlines()[-1]
        logger.info(f"Latest prediction id at last script run: {latest_id_last_run}")
        f.write(f"\n{website_latest_prediction}")

    # This is what we want to send in a notification to alert subscriber to the new crystal ball pick(S)
    if latest_id_last_run != website_latest_prediction:
        logger.info('Getting records for sms notification...')
        notification_records = get_recent_predictions(new_df, latest_id_last_run)
        for idx, record in enumerate(notification_records, 1):
            logger.info(f"Sending message for records {idx} / {len(notification_records)}")
            message = f"{record['predicted_by']} predicts {record['player_name']} will commit to {record['predicted_team']}"
            send_sms_via_email(SMS_RECIPIENT_PHONE_NUMBER, message, SMS_PROVIDER,
                            (SMS_SENDER_ADDRESS, SMS_SENDER_PASSWORD),
                            subject="Crystal Ball Alert")
            message = f"\n{record['player_url']}"
            send_sms_via_email(SMS_RECIPIENT_PHONE_NUMBER, message, SMS_PROVIDER,
                            (SMS_SENDER_ADDRESS, SMS_SENDER_PASSWORD),
                            subject="247 Profile")

if __name__ == "__main__":
    main()