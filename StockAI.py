import requests
from datetime import datetime, timedelta
from textblob import TextBlob
import yfinance as yf
import openai

from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Access keys
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

current_date = datetime.today().strftime('%Y-%m-%d')
previous_date = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')

def fetch_news(company_name):
    url = f"https://newsapi.org/v2/everything?q={company_name}&from={current_date}&to={previous_date}&apiKey={NEWSAPI_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()["articles"]
    return []

def analyze_sentiment(text):
    analysis = TextBlob(text)
    return analysis.sentiment.polarity

def get_stock_data(ticker):
    stock = yf.Ticker(ticker)
    return stock.history(period="1mo")


def generate_summary(sentiment_data, stock_predictions):
    client = openai.OpenAI(
    # defaults to os.environ.get("OPENAI_API_KEY")
    api_key=OPENAI_API_KEY,
    )

    prompt = (
        f"Given the sentiment data: {sentiment_data} and stock predictions: {stock_predictions}, "
        "suggest which stocks might perform well today and why."
    )

    completion = client.chat.completions.create(
        model="gpt-4o-mini",  # GPT-4 Turbo model
        messages=[
            {"role": "system", "content": "You are a financial analyst who provides insights on stocks."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=100  # Adjust the value as needed
    )
    return completion.choices[0].message.content

def main():
    # Example companies
    companies = ["Amazon", "Apple", "Microsoft", "Google", "Meta", "Tesla", "NVIDIA", "Berkshire Hathaway", "Johnson & Johnson", "Visa", "Procter & Gamble", "JPMorgan Chase", "ExxonMobil", "UnitedHealth Group", "Walmart", "Samsung", "Pfizer", "Coca-Cola", "Disney", "Intel"]
    sentiment_data = {}
    stock_predictions = {}

    for company in companies:
        news = fetch_news(company)
        sentiments = [analyze_sentiment(article["description"]) for article in news if article["description"]]
        sentiment_score = sum(sentiments) / len(sentiments) if sentiments else 0
        sentiment_data[company] = sentiment_score

        # Simulate stock predictions (can replace with actual ML model later)
        stock_predictions[company] = sentiment_score * 100  # Example: Scale sentiment to a stock score

    # Pass both arguments to generate_summary
    insights = generate_summary(sentiment_data, stock_predictions) 
    print(insights)


if __name__ == "__main__":
    main()