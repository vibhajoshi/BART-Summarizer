from nltk.tokenize import sent_tokenize, word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
from gensim.summarization import summarize as textrank_summarize
from transformers import pipeline
import nltk
import requests
from bs4 import BeautifulSoup
import re
from heapq import nlargest

# Download NLTK data
nltk.download('punkt')
nltk.download('stopwords')

# Initialize summarizer with strict length control
bert_summarizer = None
MAX_INPUT_LENGTH = 10000  # characters
TARGET_SUMMARY_LENGTH = 100  # words

def clean_text(text):
    """More aggressive cleaning for better summarization"""
    text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
    text = re.sub(r'\[.*?\]|\(.*?\)', '', text)  # Remove brackets and parens
    text = re.sub(r'<[^>]+>', '', text)  # Remove HTML tags
    text = re.sub(r'\bhttps?://\S+|www\.\S+', '', text)  # Remove URLs
    text = re.sub(r'[^\w\s.,;:!?\'-]', '', text)  # Keep only essential punctuation
    return text.strip()

def truncate_text(text, max_length=MAX_INPUT_LENGTH):
    """Ensure we don't process extremely long documents"""
    return text[:max_length] if len(text) > max_length else text

def fetch_article_content(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'iframe', 'noscript']):
            element.decompose()
        
        # Priority selectors for main content
        selectors = [
            'article', 
            '[itemprop="articleBody"]',
            '.article-content',
            '.post-content',
            '#article-body',
            '.story-content',
            '.article-text',
            'main'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                text = ' '.join([elem.get_text() for elem in elements])
                return clean_text(truncate_text(text))
        
        # Fallback strategies
        fallbacks = [
            ('p', lambda: ' '.join([p.get_text() for p in soup.find_all('p')])),
            ('body', lambda: soup.body.get_text())
        ]
        
        for _, fallback in fallbacks:
            text = fallback()
            if len(word_tokenize(text)) > 50:  # Minimum meaningful content
                return clean_text(truncate_text(text))
        
        return None
    except Exception as e:
        print(f"Error fetching article content: {e}")
        return None

def tfidf_summarize(text, word_limit=TARGET_SUMMARY_LENGTH):
    """More efficient TF-IDF summarization with strict length control"""
    sentences = sent_tokenize(text)
    if len(sentences) <= 3:
        return ' '.join(sentences)
    
    # Pre-filter very short/long sentences
    sentences = [s for s in sentences if 10 < len(word_tokenize(s)) < 50]
    
    vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
    try:
        sentence_vectors = vectorizer.fit_transform(sentences)
        sentence_scores = np.array(sentence_vectors.sum(axis=1)).flatten()
        
        # Select top sentences without exceeding word limit
        selected_indices = []
        word_count = 0
        for idx in nlargest(len(sentences), range(len(sentences)), 
                          key=lambda x: sentence_scores[x]):
            s_words = word_tokenize(sentences[idx])
            if word_count + len(s_words) <= word_limit:
                selected_indices.append(idx)
                word_count += len(s_words)
            if word_count >= word_limit:
                break
                
        selected_indices.sort()
        return ' '.join([sentences[i] for i in selected_indices])
    except:
        return None

def get_bert_summarizer():
    global bert_summarizer
    if bert_summarizer is None:
        # Using a more efficient model for your 8GB RAM
        bert_summarizer = pipeline(
            "summarization", 
            model="facebook/bart-large-cnn",  # Lighter than BART-large
            device=-1  # Use CPU (better for 8GB RAM)
        )
    return bert_summarizer

def bert_summarize(text, word_limit=TARGET_SUMMARY_LENGTH):
    """Strict length-controlled BERT summarization"""
    try:
        summarizer = get_bert_summarizer()
        
        # Calculate token counts for precise length control
        words = word_tokenize(text)
        if len(words) > 1024:  # Model's max token limit
            text = ' '.join(words[:1024])
        
        # Dynamic length calculation
        min_len = max(30, int(word_limit * 0.7))
        max_len = min(150, int(word_limit * 1.3))
        
        summary = summarizer(
            text,
            max_length=max_len,
            min_length=min_len,
            do_sample=False,
            truncation=True
        )
        
        # Post-process to ensure word limit
        summary_text = summary[0]['summary_text']
        summary_words = word_tokenize(summary_text)
        if len(summary_words) > word_limit:
            return ' '.join(summary_words[:word_limit])
        return summary_text
    except Exception as e:
        print(f"Error in BERT summarization: {e}")
        return None

def summarize_article(url):
    """Main summarization pipeline with strict length enforcement"""
    article_text = fetch_article_content(url)
    if not article_text or len(word_tokenize(article_text)) < 50:
        return "Insufficient content for summarization."
    
    # Attempt summarization with fallbacks
    summary = None
    methods = [
        ("BERT", lambda: bert_summarize(article_text)),
        ("TextRank", lambda: textrank_summarize(article_text, word_count=TARGET_SUMMARY_LENGTH)),
        ("TF-IDF", lambda: tfidf_summarize(article_text))
    ]
    
    for name, method in methods:
        try:
            summary = method()
            if summary and 30 <= len(word_tokenize(summary)) <= 150:
                break
        except Exception as e:
            print(f"{name} summarization failed: {e}")
    
    # Final length validation
    if summary:
        words = word_tokenize(summary)
        if len(words) > 150:
            summary = ' '.join(words[:150])
        elif len(words) < 30:
            summary = None
    
    return summary if summary else "Could not generate a sufficiently concise summary."