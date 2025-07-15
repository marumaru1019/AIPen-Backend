# app/services/dalle.py
import requests
import base64
from app.core.config import settings

DALL_E_URL = settings.DALL_E_URL
DALL_E_API_KEY = settings.DALL_E_API_KEY

def send_dalle_request_ehon(panel, genre, style):
    """
    絵本用の画像生成プロンプト例：
    ・文字は含まない
    ・柔らかい色調・温かみのあるタッチで描く
    ・シーンとキャラクターの情報を反映
    """
    prompt = f"""次の情報に基づいて、イラストを作成してください。

- 画像に文字は含めないでください。
- シーンとキャラクターをもとに、柔らかい色調と温かみのあるタッチで描いてください。
- 以下の情報を参考にしてください:
  - ジャンル: {genre}
  - スタイル: {style}
  - シーン: {panel['シーン']}
  - キャラクター: {panel['キャラクター']}
"""
    payload = {
        "prompt": prompt,
        "n": 1,
        "size": "1792x1024"
    }
    headers = {
        "Content-Type": "application/json",
        "api-key": DALL_E_API_KEY
    }
    try:
        response = requests.post(DALL_E_URL, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
        return (panel, result)
    except Exception as e:
        return (panel, e)

def send_dalle_request_manga(panel: dict, narrative: dict):
    prompt = (
        "次の情報に基づいて漫画のデザインを作成してください。\n\n"
        "# 最重要事項\n"
        "- 画像に吹き出し等は入れないでください。\n"
        "- 文字は含まない画像を生成してください。\n"
        "- 各コマは1画像ずつ出力し、複数のコマを1画像に含めないでください。\n"
        "- 漫画の吹き出しや文字は後で追加するので、絵に集中してください。\n"
        "- コマ番号によって画像内のキャラクター配置を変えてください。\n"
        "  - コマ番号=1: キャラクターを右下に配置\n"
        "  - コマ番号=2: キャラクターを左下に配置\n"
        "  - コマ番号=3: キャラクターを中心に配置\n"
        "  - コマ番号=4: キャラクターを左下に配置\n\n"
        "# 情報\n"
        "- ジャンル: {genre}\n"
        "- スタイル: {style}\n"
        "- シーン: {scene}\n"
        "- キャラクター: {character}\n"
        "- セリフ: {dialogue}\n"
        "- コマ番号: {number}"
    ).format(
        genre=narrative.get("genre"),
        style=narrative.get("style"),
        scene=panel.get("シーン"),
        character=panel.get("キャラクター"),
        dialogue=panel.get("セリフ"),
        number=panel.get("コマ番号")
    )
    payload = {
        "prompt": prompt,
        "n": 1,
        "size": "1024x1792"
    }
    headers = {
        "Content-Type": "application/json",
        "api-key": DALL_E_API_KEY
    }
    try:
        response = requests.post(DALL_E_URL, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
        return (panel, result)
    except Exception as e:
        return (panel, e)

def download_image(panel: dict, result: dict):
    try:
        image_url = result['data'][0]['url']
        img_response = requests.get(image_url)
        img_response.raise_for_status()
        img_data = img_response.content
        img_base64 = base64.b64encode(img_data).decode('utf-8')
        return (panel, img_base64)
    except Exception as e:
        return (panel, e)
