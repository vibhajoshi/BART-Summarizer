import feedparser
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_image_url(entry):
    """Helper function to extract image URL from an entry"""
    image_url = None
    base_url = urlparse(entry.link).netloc if 'link' in entry else None

    # 1. Check for 'media_content' (used in many feeds)
    if 'media_content' in entry:
        for media in entry.media_content:
            if media.get('type', '').startswith('image/'):
                image_url = media.get('url', '')
                break
    
    # 2. Check 'media_thumbnail'
    if not image_url and 'media_thumbnail' in entry:
        for media in entry.media_thumbnail:
            if media.get('url'):
                image_url = media['url']
                break

    # 3. Check 'enclosures'
    if not image_url and 'enclosures' in entry:
        for enc in entry.enclosures:
            if enc.get('type', '').startswith('image/'):
                image_url = enc.get('href', '')
                break

    # 4. Parse from 'content' HTML
    if not image_url and 'content' in entry:
        for content in entry.content:
            soup = BeautifulSoup(content.value, 'html.parser')
            img_tag = soup.find('img')
            if img_tag and img_tag.get('src'):
                image_url = img_tag['src']
                break

    # 5. Parse from 'summary' HTML
    if not image_url and 'summary' in entry:
        soup = BeautifulSoup(entry.summary, 'html.parser')
        img_tag = soup.find('img')
        if img_tag and img_tag.get('src'):
            image_url = img_tag['src']

    # 6. Check for 'links' with image type
    if not image_url and 'links' in entry:
        for link in entry.links:
            if link.get('type', '').startswith('image/'):
                image_url = link.get('href', '')
                break

    # 7. Fallback to Open Graph image if available
    if not image_url and 'link' in entry:
        try:
            response = requests.get(entry.link, timeout=5)
            if response.ok:
                soup = BeautifulSoup(response.text, 'html.parser')
                og_image = soup.find('meta', property='og:image')
                if og_image and og_image.get('content'):
                    image_url = og_image['content']
        except:
            pass

    # Fix relative URLs and clean up image URL
    if image_url:
        # Remove query parameters if they make the URL invalid
        image_url = image_url.split('?')[0].split('#')[0]
        
        # Handle protocol-relative URLs
        if image_url.startswith('//'):
            image_url = 'https:' + image_url
        # Handle relative URLs
        elif not image_url.startswith(('http://', 'https://')):
            if base_url:
                image_url = urljoin(f'https://{base_url}', image_url)
            elif 'link' in entry:
                image_url = urljoin(entry.link, image_url)

    return image_url

def process_entry(entry):
    """Process a single feed entry"""
    try:
        image_url = get_image_url(entry)
        
        return {
            'title': entry.get('title', 'No title'),
            'url': entry.get('link', ''),
            'image_url': image_url if image_url else None
        }
    except Exception as e:
        print(f"Error processing entry: {e}")
        return None

def get_articles_from_rss(rss_url):
    """Fetch and process articles from RSS feed"""
    feed = feedparser.parse(rss_url)
    articles = []
    
    # Increased limit to 20 entries per feed
    entries = feed.entries[:20] if len(feed.entries) > 20 else feed.entries
    
    # Use threading to speed up image URL fetching
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_entry, entry) for entry in entries]
        
        for future in as_completed(futures):
            result = future.result()
            if result:
                articles.append(result)
    
    return articles