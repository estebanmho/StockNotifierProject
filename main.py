import os
import requests
import datetime as dt
from newsapi import NewsApiClient
from twilio.rest import Client


API_KEY_STOCK = os.environ.get("API_KEY_STOCK")
API_KEY_NEWS = os.environ.get("API_KEY_NEWS_STOCK")
SYMBOL = os.environ.get("SYMBOL_STOCK")
NOW = dt.datetime.now()


def get_stock_data():
    param_stock = {
        "function": "TIME_SERIES_DAILY",
        "symbol": SYMBOL,
        "apikey": API_KEY_STOCK,
        "datatype": "json",
        "outputsize": "compact"
    }

    result_stock = requests.get(url="https://www.alphavantage.co/query", params=param_stock)
    result_stock.raise_for_status()
    return result_stock.json()['Time Series (Daily)']


def calculate_percentage(stock_data) -> float:
    yesterday = NOW - dt.timedelta(days=1)
    before_yesterday = None
    if yesterday.weekday() == 0:
        before_yesterday = NOW - dt.timedelta(days=4)
    elif yesterday.weekday() == 5:
        yesterday = yesterday - dt.timedelta(days=1)
        before_yesterday = yesterday - dt.timedelta(days=1)
    elif yesterday.weekday() == 6:
        yesterday = yesterday - dt.timedelta(days=-2)
        before_yesterday = yesterday - dt.timedelta(days=1)
    else:
        before_yesterday = yesterday - dt.timedelta(days=1)

    value_yesterday = stock_data[str(yesterday.date())]["4. close"]
    value_before_yesterday = stock_data[str(before_yesterday.date())]["4. close"]
    diff = float(value_yesterday)-float(value_before_yesterday)
    coc = diff/float(value_yesterday)
    return coc*100


def obtain_news():
    newsapi = NewsApiClient(api_key=API_KEY_NEWS)

    # /v2/top-headlines
    top_headlines = newsapi.get_top_headlines(q='Tesla', #Change the keyword
                                              category='business',
                                              language='en',
                                              country='us')
    return top_headlines


def notify_user(news, percentage):
    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    auth_token = os.environ['TWILIO_AUTH_TOKEN']
    client = Client(account_sid, auth_token)
    if percentage < 0:
        icon = '????'
    else:
        icon = '????'
    for new in news["articles"]:
        if len(new['description']) < 200:
            x = len(new['description'])
        else:
            x = 200
        body = f"{SYMBOL} {icon} {round(percentage,2)}%\nHeading: {new['title']}\nBrief: {new['description'][:x]}..."
        message = client.messages.create(
            body=body,
            from_=os.environ['FROM_PHONE'],
            to=os.environ['TO_PHONE']
        )

data_stock = get_stock_data()
percentage = calculate_percentage(data_stock)
if percentage > 10 or percentage < -10:
    news = obtain_news()
    notify_user(news, percentage)
