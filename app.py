from flask import Flask, request, Response
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

app = Flask(__name__)

# الصفحة الرئيسية لإدخال الرابط
HOME_HTML = """
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <title>بروكسي بايثون</title>
    <style>
        body { font-family: Tahoma, sans-serif; background: #121212; color: #fff; text-align: center; padding-top: 80px; }
        input { width: 60%; padding: 12px; font-size: 16px; border-radius: 6px; border: none; }
        button { padding: 12px 24px; font-size: 16px; background: #0078d4; color: white; border: none; border-radius: 6px; cursor: pointer; }
    </style>
</head>
<body>
    <h2>متصفح البروكسي الخاص</h2>
    <form action="/go" method="get">
        <input type="text" name="url" placeholder="اكتب الرابط هنا مثل: https://example.com" required>
        <button type="submit">فتح الموقع</button>
    </form>
</body>
</html>
"""

@app.route('/')
def home():
    return HOME_HTML

@app.route('/go')
def go():
    target_url = request.args.get('url', '').strip()
    if not target_url.startswith(('http://', 'https://')):
        target_url = 'https://' + target_url
    return proxy(target_url)

@app.route('/proxy/<path:target_url>', methods=['GET', 'POST'])
def proxy(target_url):
    if not target_url.startswith(('http://', 'https://')):
        target_url = 'https://' + target_url

    try:
        headers = {'User-Agent': request.headers.get('User-Agent', 'Mozilla/5.0')}
        resp = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            params=request.args,
            data=request.get_data(),
            allow_redirects=True,
            timeout=15
        )

        content_type = resp.headers.get('Content-Type', '')

        # تعديل الروابط داخل صفحات HTML لتمر عبر البروكسي
        if 'text/html' in content_type:
            soup = BeautifulSoup(resp.text, 'html.parser')
            for tag, attr in [('a', 'href'), ('link', 'href'), ('script', 'src'), ('img', 'src'), ('form', 'action')]:
                for el in soup.find_all(tag):
                    if el.has_attr(attr):
                        full_url = urljoin(target_url, el[attr])
                        if full_url.startswith(('http://', 'https://')):
                            el[attr] = f"/proxy/{full_url}"
            return Response(str(soup), status=resp.status_code, content_type=content_type)

        return Response(resp.content, status=resp.status_code, content_type=content_type)

    except Exception as e:
        return f"حدث خطأ أثناء تحميل الموقع: {e}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)