# app/services/narrative.py
import os
import json
from openai import AzureOpenAI
from app.core.config import settings

os.environ['AZURE_OPENAI_API_KEY'] = settings.AZURE_OPENAI_API_KEY

client = AzureOpenAI(
    api_version=settings.OPENAI_API_VERSION,
    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
)

def generate_ehon_narrative(panel_num, commit_outline, genre, style):
    prompt_template = """以下の形式でユーザーから入力を受け取ってください。受け取った情報に基づいて、{panel_num}ページの絵本のナレーションを作成し、指定されたJSON形式で出力してください。

### 受け取り
panel_num: {panel_num}
commit_outline: {commit_outline}
genre: {genre}
style: {style}

### 出力形式
{{
    "panel_num": {panel_num},
    "commit_outline": "{commit_outline}",
    "genre": "{genre}",
    "style": "{style}",
    "panels": [
        {{
            "コマ番号": {{number}},
            "キャラクター": "{{character}}",
            "ナレーション": "{{dialogue}}",
            "シーン": "{{scene}}"
        }}
    ]
}}

### 最重要事項
- ナレーションの文字数は900-1100文字になるようにしてください。多少長くなるのは構いませんが、ナレーションの文字数が少なくなるのは絶対に避けてください。
- ちゃんとコマ数内でナレーションで物語が完結するようにしてください。panel_numが1の場合は、1ページで完結する物語をナレーションに入れてください。
"""
    prompt = prompt_template.format(
        panel_num=panel_num,
        commit_outline=commit_outline,
        genre=genre,
        style=style
    )
    messages = [{"role": "user", "content": prompt}]
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
         response_format={"type": "json_object"}
    )
    # 返ってくる応答からテキスト部分を取得し JSON に変換
    narrative_json_str = response.choices[0].message.content
    return json.loads(narrative_json_str)

def generate_manga_narrative(prompt_text: str) -> dict:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt_text}],
        response_format={"type": "json_object"}
    )
    response_json = response.choices[0].message.content
    if response_json is None:
        raise ValueError("Response content is None")
    return json.loads(response_json)
