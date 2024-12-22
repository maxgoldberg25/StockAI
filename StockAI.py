import requests
from datetime import datetime, timedelta
from textblob import TextBlob
import yfinance as yf
import openai
import websocket
import json
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

from concurrent.futures import ThreadPoolExecutor

# Load environment variables from .env file
load_dotenv()

#* Access keys
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
FINHUB_API_KEY = os.getenv("FINHUB_API_KEY")


# // # * Modify this to include this amount of previous days in AI consideration
# // days = 2

# // # Current date in YYYY-MM-DD format
# // current_date = datetime.today().strftime('%Y-%m-%d')
# // previous_date = (datetime.today() - timedelta(days=days)).strftime('%Y-%m-%d')
 
# Fetch penny stocks with news filtering
def get_penny_stocks():

    
    url = f"https://finnhub.io/api/v1/stock/symbol?exchange=US&token={FINHUB_API_KEY}"
    response = requests.get(url)
    
    if response.status_code == 200:
        stocks = response.json()
        common_stocks = [s for s in stocks if s['type'] == 'Common Stock']
        penny_stocks = []

        for stock in common_stocks:
            price_url = f"https://finnhub.io/api/v1/quote?symbol={stock['symbol']}&token={FINHUB_API_KEY}"
            price_response = requests.get(price_url)
            
            if price_response.status_code == 200:
                price_data = price_response.json()
                current_price = price_data.get("c")
                high_price = price_data.get("h")
                low_price = price_data.get("l")
                volume = price_data.get("v")

                print(price_data)

                # Check if the stock qualifies as a penny stock
                if current_price and current_price < 5:
                    # Fetch news using Beautiful Soup
                    news_articles = fetch_yahoo_finance_news(stock.get('description', stock['symbol']))
                    
                    # Only add stocks with recent news
                    if news_articles:
                        penny_stocks.append({
                            "symbol": stock['symbol'],
                            "name": stock.get('description', 'Unknown'),
                            "price": current_price,
                            "high": high_price,
                            "low": low_price,
                            "volume": volume,
                            "news": news_articles[:5]  # Include up to 5 recent news articles
                        })

                        print(f"Added stock with news: {penny_stocks[-1]}\n\n")

                        # ! Modify the penny stock cap to improve performance (best results are when the value is greates)
                        maximumSearch = 20
                        if len(penny_stocks) > maximumSearch:
                            return penny_stocks
        
        return penny_stocks
    
    print(f"Failed to fetch stocks. Status code: {response.status_code}")
    return []

# WebSocket callback functions
real_time_data = {}

def on_message(ws, message):
    data = json.loads(message)
    if data.get("type") == "trade":
        for trade in data.get("data", []):
            symbol = trade["s"]
            price = trade["p"]
            volume = trade["v"]

            # Update real-time data for the stock
            if symbol not in real_time_data:
                real_time_data[symbol] = {"prices": [], "volumes": []}
            real_time_data[symbol]["prices"].append(price)
            real_time_data[symbol]["volumes"].append(volume)

def on_error(ws, error):
    print("WebSocket error:", error)

def on_close(ws, close_status_code, close_msg):
    print("WebSocket closed")

def on_open(ws, symbols):
    for symbol in symbols:
        ws.send(json.dumps({"type": "subscribe", "symbol": symbol}))

def get_real_time_trade_data(penny_stocks):
    symbols = [stock["symbol"] for stock in penny_stocks]

    def on_open_wrapper(ws):
        on_open(ws, symbols)

    ws = websocket.WebSocketApp(
        f"wss://ws.finnhub.io?token={FINHUB_API_KEY}",
        on_open=on_open_wrapper,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.run_forever()

# Filter high-potential stocks
def filter_high_potential_stocks(stocks):
    # Integrate real-time trade data into stocks
    print("\n\ntype of stocks:", type(stocks))
    for stock in stocks:
        symbol = stock["symbol"]
        print(symbol)
        
        if symbol in real_time_data:
            prices = real_time_data[symbol]["prices"]
            volumes = real_time_data[symbol]["volumes"]
            
            # Update stock data with real-time trade information
            if prices:
                stock["avg_price"] = sum(prices) / len(prices)
            if volumes:
                stock["total_volume"] = sum(volumes)

    # Example ranking: sort by volume and price range (including real-time data if available)
    ranked_stocks = sorted(
        stocks, 
        key=lambda x: (
            x.get("total_volume", x["volume"]),  # Use real-time volume if available
            x["high"] - x["low"]
        ), 
        reverse=True
    )
    return ranked_stocks[:50]  # Top 50

def fetch_yahoo_finance_news(stock_symbol):
    """
    Scrape news articles dynamically loaded by JavaScript on Yahoo Finance.
    """
    # Setup Selenium WebDriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    url = f"https://finance.yahoo.com/quote/{stock_symbol}/news"
    driver.get(url)

    # Allow time for the JavaScript to load
    time.sleep(2)  # Adjust this delay if needed

    # Fetch the rendered page source
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()  # Close the browser session

    # Parse the news section
    news_items = soup.select('section[data-testid="storyitem"]')  # Adjusted based on Yahoo layout
    print(f"Found {len(news_items)} news items for {stock_symbol}.")

    news = []
    for idx, item in enumerate(news_items, start=1):
        # Extract the article link
        link_elem = item.select_one('a.subtle-link[href]')
        link = link_elem['href'] if link_elem else None
        if link and link.startswith('/'):
            link = f"https://finance.yahoo.com{link}"  # Handle relative links

        # Extract the article title
        title_elem = item.select_one('h3')
        title = title_elem.get_text(strip=True) if title_elem else None

        # Extract a snippet or publishing details
        snippet_elem = item.select_one('div.publishing')
        snippet = snippet_elem.get_text(strip=True) if snippet_elem else "No snippet available"

        if title and link:
            news.append({
                "title": title,
                "snippet": snippet,
            })

    print(f"Total articles scraped for {stock_symbol}: {len(news)}")
    return news



def analyze_sentiment(text):
    analysis = TextBlob(text)
    return analysis.sentiment.polarity

def get_stock_data(ticker):
    stock = yf.Ticker(ticker)
    return stock.history(period="1mo")


def generate_summary(sentiment_data):
    client = openai.OpenAI(
    # defaults to os.environ.get("OPENAI_API_KEY")
    api_key=OPENAI_API_KEY,
    )

    prompt = (
        f"Given the sentiment data: {sentiment_data}, "
        "suggest which stocks might perform well today and give me bullet points for the specific reasons why."
        "Make sure your response fits within 250 characters."
    )

    completion = client.chat.completions.create(
        model="gpt-4o-mini",  # GPT-4 Turbo model
        messages=[
            {"role": "system", "content": "You are a financial analyst who provides insights on stocks."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=250  # Adjust the value as needed
    )
    return completion.choices[0].message.content



def main():
    
    # // Blue chip companies
    #// companies = ["Amazon", "Apple", "Microsoft", "Google", "Meta", "Tesla", "NVIDIA", "Berkshire Hathaway", "Johnson & Johnson", "Visa", "Procter & Gamble", "JPMorgan Chase", "ExxonMobil", "UnitedHealth Group", "Walmart", "Samsung", "Pfizer", "Coca-Cola", "Disney", "Intel"]
 
    # Step 1: Fetch penny stocks
    penny_stocks = get_penny_stocks()
    print("Fetched Penny Stocks:", penny_stocks)

    # Step 2: Filter high-potential stocks
    high_potential_stocks = filter_high_potential_stocks(penny_stocks)
    print("High Potential Stocks:", high_potential_stocks)

    penny_stocks_arr = filter_high_potential_stocks(penny_stocks)
    sentiment_data = {}
    stock_predictions = {}

    sentiments = []
    for article in penny_stocks_arr:
        # Make sure there is a 'news' list and it's not empty
        if "news" in article and article["news"]:
            symbol = article.get("symbol", "UNKNOWN")  # Fetch the stock ticker
            for news_item in article["news"]:
                title = news_item.get("title", "")
                if title:
                    polarity = analyze_sentiment(title)
                    sentiments.append({
                        "symbol": symbol,
                        "score": polarity
                    })

    print(sentiments)

    # Pass both arguments to generate_summary
    insights = generate_summary(sentiments) 
    print(insights)
    


if __name__ == "__main__":
    main()