"""
JARVIS Tools - Web Scraping
BeautifulSoup4 live Google News RSS & Wikipedia summaries
"""
import requests
import urllib.parse
import re
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def fetch_wikipedia_summary(query: str) -> str:
    try:
        search_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={urllib.parse.quote(query)}&limit=1&namespace=0&format=json"
        res = requests.get(search_url, headers=HEADERS, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if len(data) > 2 and data[2]:
                summary = data[2][0]
                if summary:
                    return summary.strip()
    except Exception:
        pass
    return None

def fetch_live_web_search(query: str) -> str:
    try:
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        res = requests.get(url, headers=HEADERS, timeout=5)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            snippets = soup.find_all("a", class_="result__snippet")
            results = []
            for s in snippets[:2]:
                text = s.get_text().strip()
                if text:
                    results.append(text)
            if results:
                summary = " ".join(results)
                summary = re.sub(r'\s+', ' ', summary)
                return summary[:280]
    except Exception:
        pass
    return None

def fetch_breaking_news() -> str:
    try:
        url = "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"
        res = requests.get(url, headers=HEADERS, timeout=5)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "xml")
            items = soup.find_all("item")
            headlines = []
            for item in items[:5]:
                title = item.find("title")
                if title:
                    headlines.append(title.get_text().strip())
            if headlines:
                return "Top headlines: " + "; ".join(headlines) + "."
    except Exception:
        pass
    return "Could not retrieve live news right now, sir."

def get_weather(location: str = "") -> str:
    try:
        url = f"https://wttr.in/{urllib.parse.quote(location)}?format=%C+%t"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            weather = res.text.strip()
            return f"Current weather{f' in {location}' if location else ''}: {weather}, sir."
    except Exception:
        pass
    return "Could not retrieve weather, sir."

def get_news() -> str:
    return fetch_breaking_news()

def get_web_information(query: str) -> str:
    q = query.lower().strip()
    
    if "news" in q or "headlines" in q:
        return fetch_breaking_news()
    
    wiki_ans = fetch_wikipedia_summary(query)
    if wiki_ans:
        return wiki_ans
    
    web_ans = fetch_live_web_search(query)
    if web_ans:
        return web_ans
    
    return None

if __name__ == "__main__":
    print(get_weather("New York"))
    print(get_news())
    print(get_web_information("who is elon musk"))