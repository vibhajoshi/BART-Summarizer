from flask import Flask, render_template, request, redirect, url_for
from utils.scraper import get_articles_from_rss
import os
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer  # You can also try LexRankSummarizer or TextRankSummarizer
import nltk
nltk.download('punkt')
from nltk.tokenize import PunktSentenceTokenizer
from transformers import pipeline

def summarize_article(text, max_length=130, min_length=30):
    summarizer = pipeline("summarization")
    summary = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
    return summary[0]['summary_text']


app = Flask(__name__)

# RSS feeds configuration
RSS_FEEDS = {
    "general": {
        "india": [
            "http://feeds.bbci.co.uk/news/world/asia/india/rss.xml",
            "https://www.thehindu.com/news/national/feeder/default.rss",
            "https://indianexpress.com/section/india/feed/",
        ],
        "international": [
            "http://feeds.bbci.co.uk/news/world/rss.xml",
            "https://www.thehindu.com/news/international/feeder/default.rss",
        ],
    },
    "politics": {
        "india": [
            "http://feeds.bbci.co.uk/news/politics/rss.xml",
            "https://www.thehindu.com/news/national/feeder/default.rss",
        ],
        "international": [
            "http://feeds.bbci.co.uk/news/politics/rss.xml",
            "https://www.thehindu.com/news/international/feeder/default.rss",
        ],
    },
    "technology": {
        "india": [
            "http://feeds.bbci.co.uk/news/technology/rss.xml",
            "https://www.thehindu.com/sci-tech/technology/feeder/default.rss",
        ],
        "international": [
            "http://feeds.bbci.co.uk/news/technology/rss.xml",
            "https://www.thehindu.com/sci-tech/technology/feeder/default.rss",
        ],
    },
    "sports": {
        "india": [
            "http://feeds.bbci.co.uk/news/sport/rss.xml",
            "https://www.thehindu.com/sport/feeder/default.rss",
        ],
        "international": [
            "http://feeds.bbci.co.uk/news/sport/rss.xml",
            "https://www.thehindu.com/sport/feeder/default.rss",
        ],
    },
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/articles', methods=['POST'])
def articles():
    region = request.form.get('region')
    category = request.form.get('category')
    
    if not region or not category:
        return redirect(url_for('index'))
    
    feed_urls = RSS_FEEDS.get(category, {}).get(region, [])
    articles = []
    
    for url in feed_urls:
        try:
            articles.extend(get_articles_from_rss(url))
            if len(articles) >= 20:  # Increased limit to 20 articles
                articles = articles[:20]
                break
        except Exception as e:
            print(f"Error fetching articles from {url}: {e}")
    
    return render_template('articles.html', articles=articles, region=region, category=category)

@app.route('/summary')
def summary():
    article_url = request.args.get('url')
    title = request.args.get('title')
    image_url = request.args.get('image_url')
    
    if not article_url:
        return redirect(url_for('index'))
    
    summary_text = summarize_article(article_url)
    
    return render_template('summary.html', 
                         title=title, 
                         image_url=image_url, 
                         summary=summary_text)

if __name__ == '__main__':
    app.run(debug=True)