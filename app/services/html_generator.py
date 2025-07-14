# app/services/html_generator.py
import requests
from app.core.config import settings
import base64

def generate_html(is_comic: bool, content):
    payload = {
        "user_id": "test_user",
        "is_comic": is_comic,
        "content": content
    }
    response = requests.post(settings.GENERATE_HTML_URL, json=payload)
    response.raise_for_status()
    html_result = response.json()
    # base64_html = html_result['output_html_base64']
    # html_data = base64.b64decode(base64_html)
    # with open('output4.html', 'wb') as html_file:
    #     html_file.write(html_data)
    return html_result
