# app/services/news_api.py
from GoogleNews import GoogleNews

def fetch_news(query: str, page_size: int = 5):
    googlenews = GoogleNews(lang='en')
    googlenews.search(query)
    results = googlenews.result()
    
    articles = []
    for item in results[:page_size]:
        articles.append({
            "title": item.get("title"),
            "description": item.get("desc"),
            "url": item.get("link"),
            "source": item.get("media")
        })
    
    if not articles:
        return {"error": "No news found for this query."}
    
    return {"articles": articles}
