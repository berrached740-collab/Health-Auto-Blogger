import os
import feedparser
import google.generativeai as genai
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import random

def main():
    print("🌿 Starting the Health & Wellness Auto-Blogger...")

    api_key = os.environ.get("GEMINI_API_KEY")
    blog_id = os.environ.get("BLOG_ID")
    
    if not api_key or not blog_id:
        print("❌ Error: GEMINI_API_KEY or BLOG_ID not found")
        return
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    # ====================================================
    # 1. الاتصال بمدونتك أولاً لمعرفة المقالات المنشورة سابقاً
    # ====================================================
    print("🌐 Connecting to Blogger to check history...")
    SCOPES = ['https://www.googleapis.com/auth/blogger']
    
    if not os.path.exists('token.json'):
        print("❌ Error: token.json not found!")
        return
        
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    service = build('blogger', 'v3', credentials=creds)
    
    recent_titles = []
    try:
        # قراءة عناوين آخر 30 مقال من مدونتك لمنع التكرار
        request = service.posts().list(blogId=blog_id, maxResults=30, fields="items(title)")
        response = request.execute()
        recent_titles = [item.get('title', '') for item in response.get('items', [])]
        print(f"🔍 Found {len(recent_titles)} recent articles in your blog. Checking for new news...")
    except Exception as e:
        print(f"⚠️ Could not fetch history: {e}")

    # ====================================================
    # 2. البحث عن خبر جديد (غير مكرر)
    # ====================================================
    rss_urls = [
        "https://www.healthline.com/rss",
        "http://rssfeeds.webmd.com/rss/rss.aspx?RSSSource=RSS_PUBLIC",
        "https://www.medicalnewstoday.com/feed/normal",
        "https://psychcentral.com/blog/feed",
        "https://www.mindbodygreen.com/rss/feed.xml",
        "https://www.shape.com/rss",
        "https://www.menshealth.com/rss",
        "https://www.womenshealthmag.com/rss/all.xml"
    ]
    
    news_title = ""
    news_image_url = ""
    
    random.shuffle(rss_urls)
    
    for url in rss_urls:
        try:
            feed = feedparser.parse(url)
            if feed.entries:
                # فحص أول 15 خبر من المصدر
                for entry in feed.entries[:15]:
                    # الشرط الذهبي: إذا كان عنوان الخبر ليس في مدونتك
                    if entry.title not in recent_titles:
                        news_title = entry.title
                        
                        # سحب الصورة
                        if 'media_content' in entry and len(entry.media_content) > 0:
                            news_image_url = entry.media_content[0]['url']
                        elif 'links' in entry:
                            for link in entry.links:
                                if 'image' in link.get('type', ''):
                                    news_image_url = link.href
                                    break
                        break # وجدنا خبراً حصرياً وغير مكرر، نوقف البحث هنا
            if news_title:
                break # نوقف البحث في باقي المواقع
        except:
            continue
            
    if not news_title:
        print("✅ No NEW news found right now. All recent news are already on your blog. Will try again later.")
        return
        
    print(f"📰 Found NEW exclusive health article: {news_title}")

    # ====================================================
    # 🔴 رابط Adsterra المباشر الخاص بك 
    # ====================================================
    adsterra_direct_link = "https://www.profitablecpmratenetwork.com/ve3ktt21?key=949627e2df43786ddffa0da016c1bdcb"

    prompt = f"""
    You are an expert health, wellness, and spiritual life coach writing for a highly popular holistic living blog.
    Write a highly engaging, soothing, and comprehensive blog post in ENGLISH based on this topic/headline: "{news_title}".
    
    Requirements:
    - Target audience: All ages and genders seeking physical healing, mental peace, body care, and spiritual wellness.
    - Length: Around 600 words.
    - Output MUST be pure HTML code only (no markdown formatting like ```html).
    - Use <h2> and <h3> for well-structured subheadings, and <p> for readable paragraphs.
    - Tone: Compassionate, professional, uplifting, and highly informative.
    - At the end of the article, create a beautiful, eye-catching CSS-styled button with a soothing color (like teal or soft green) that says "Click Here For Your Personalized Wellness Guide" and set its href attribute to exactly this link: {adsterra_direct_link}
    - Do not write any intro or outro, just the HTML.
    """
    
    print("🤖 AI is generating the article...")
    response = model.generate_content(prompt)
    article_html = response.text
    article_html = article_html.replace('```html', '').replace('```', '').strip()

    # خطة بديلة قوية ومضمونة 100% لجلب الصور (تمنع التكرار أيضا)
    if not news_image_url:
        fallback_keywords = ["wellness", "skincare", "yoga", "meditation", "spa", "healing", "mental", "healthy"]
        random_keyword = random.choice(fallback_keywords)
        random_number = random.randint(1, 1000)
        news_image_url = f"https://loremflickr.com/800/400/{random_keyword}?lock={random_number}"
        print(f"🔄 Using fallback image for keyword: {random_keyword}")

    image_html = f'<div style="text-align: center; margin-bottom: 20px;"><img src="{news_image_url}" alt="{news_title}" style="max-width: 100%; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"></div>'
    article_html = image_html + "\n" + article_html
    
    post_body = {
        'title': news_title,
        'content': article_html,
        'labels': ['Health & Wellness', 'Mental Peace', 'Body Care']
    }
    
    print("📝 Publishing the article to Blogger...")
    request = service.posts().insert(blogId=blog_id, body=post_body, isDraft=False)
    response = request.execute()
    
    print(f"✅ Published successfully! Article URL: {response.get('url')}")

if __name__ == '__main__':
    main()
