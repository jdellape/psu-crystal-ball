import os
import logging
import requests
from bs4 import BeautifulSoup
import gspread
import pandas as pd
from etext import send_sms_via_email

# Auth for connecting to google sheets
GSPREAD_CREDS = {
    "type": "service_account",
    "project_id": os.environ["GSPREAD_PROJECT_ID"],
    "private_key_id": os.environ["GSPREAD_PRIVATE_KEY_ID"],
    "private_key": os.environ["GSPREAD_PRIVATE_KEY"],
    "client_email": os.environ["GSPREAD_CLIENT_EMAIL"],
    "client_id": os.environ["GSPREAD_CLIENT_ID"],
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": os.environ["GSPREAD_CLIENT_X509_CERT_URL"],
    "universe_domain": "googleapis.com"
}

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

def get_recent_predictions(new_df, old_df):
    df = pd.concat([new_df, old_df]).drop_duplicates(keep=False)
    records = df.to_dict('records')
    return records

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

    # Connect to google sheet as data source
    logger.info("Connecting to google sheet data source...")
    gc = gspread.service_account_from_dict(GSPREAD_CREDS)

    worksheet = gc.open('psu-crystal-ball').sheet1

    old_df = pd.DataFrame(worksheet.get_all_records())

    worksheet_latest_prediction = list(old_df['prediction_id'])[0]
    logger.info(f"Latest prediction id stored in google sheet: {worksheet_latest_prediction}")

    # This is what we want to send in a notification to alert subscriber to the new crystal ball pick(S)
    if worksheet_latest_prediction != website_latest_prediction:
        # Get the rows in new_df not in old_df
        notification_records = get_recent_predictions(new_df, old_df)
        for record in notification_records:
            message = f"{record['predicted_by']} predicts {record['player_name']} will commit to {record['predicted_team']}"
            send_sms_via_email(SMS_RECIPIENT_PHONE_NUMBER, message, SMS_PROVIDER,
                            (SMS_SENDER_ADDRESS, SMS_SENDER_PASSWORD),
                            subject="Crystal Ball Alert")
            message = f"\n{record['player_url']}"
            send_sms_via_email(SMS_RECIPIENT_PHONE_NUMBER, message, SMS_PROVIDER,
                            (SMS_SENDER_ADDRESS, SMS_SENDER_PASSWORD),
                            subject="247 Profile")

    # Clear the worksheet and overwrite with current scrape
    worksheet.clear()
    worksheet.update([new_df.columns.values.tolist()] + new_df.values.tolist())

if __name__ == "__main__":
    main()