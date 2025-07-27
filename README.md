# BART-Summarizer 📰✨

A Flask-based web app that fetches the latest news articles from RSS feeds and provides concise summaries using various text summarization techniques.

## 🔍 Features

- 📰 Pulls news articles from popular Indian and International RSS feeds.
- 🧠 Summarizes articles using:
  - Sumy’s LSA summarizer
  - (Optionally extendable to BART, TextRank, etc.)
- 🌍 Supports categories: General, Politics, Technology, Sports
- 🧭 Region-based filtering: India / International
- 🖼️ Displays images (if available) alongside summaries

## 🛠️ Tech Stack

- **Frontend:** HTML, CSS (via Jinja templates)
- **Backend:** Python, Flask
- **Summarization Libraries:** `sumy`, `sklearn`, `nltk`
- **Scraping:** `BeautifulSoup`, `feedparser`

## 📸 Screenshots

<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/ba3791eb-b764-4f39-83ef-f93fa12985ae" />
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/6f5c446e-d45a-4b55-ad07-b41264a15665" />
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/6d0ba70b-360f-49d6-8e43-9cf9b7b89d7d" />
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/76f43002-e03f-41c5-a9b7-ca4d9812a968" />




## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/vibhajoshi/BART-Summarizer.git
cd BART-Summarizer

python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

python app.py
