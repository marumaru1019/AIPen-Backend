# app/api/endpoints/manga.py
import concurrent.futures
from fastapi import APIRouter, HTTPException
from app.models.schemas import MangaRequest
from app.services import narrative, dalle, html_generator

# 漫画生成用のプロンプトテンプレート（few-shot例などを含む）
MANGA_PROMPT_TEMPLATE = """以下の形式でユーザーから入力を受け取ってください。受け取った情報に基づいて、{panel_num}コマ漫画のセリフを作成し、指定されたJSON形式で出力してください。

### 受け取り
panel_num: {panel_num}
commit_outline: {commit_outline}
genre: {genre}
style: {style}

### 出力形式
```json
{{
    "panel_num": {panel_num},
    "commit_outline": "{commit_outline}",
    "genre": "{genre}",
    "style": "{style}",
    "panels": [
        {{
            "コマ番号": {{number}},
            "キャラクター": "{{character}}",
            "セリフ": "{{dialogue}}",
            "シーン": "{{scene}}"
        }},
        ...
    ]
}}
```

以下にfew-shotの例を示します：

### 最重要事項
- 出力はそのままDALLE-3のプロンプトに使用するので、**コンテンツフィルターにはじかれるような**文章や単語は含めないでください。

### 受け取りの例
panel_num: 3
commit_outline: 勇者がドラゴンを退治する冒険
genre: ファンタジー
style: 日本

### Few-shot例

```json
{{
    "panel_num": 3,
    "commit_outline": "勇者がドラゴンを退治する冒険",
    "genre": "ファンタジー",
    "style": "日本",
    "panels": [
        {{
            "コマ番号": 1,
            "キャラクター": "勇者",
            "セリフ": "ドラゴン退治の旅に出るぞ！",
            "シーン": "村の広場、朝焼けの空。勇者は剣を持ち、鎧を着ている。背景に村の家々が見える。"
        }},
        {{
            "コマ番号": 2,
            "キャラクター": "村人",
            "セリフ": "気をつけてね、勇者様！",
            "シーン": "村の広場、朝焼けの空。村人はシンプルな農夫の服を着ている。背景に村の家々と勇者が見える。"
        }},
        {{
            "コマ番号": 3,
            "キャラクター": "勇者",
            "セリフ": "大丈夫さ、必ずドラゴンを倒してくる！",
            "シーン": "村の広場、朝焼けの空。勇者は自信に満ちた表情で剣を握りしめている。背景に村の家々が見える。"
        }}
    ]
}}
```

### 別の受け取りの例
panel_num: 3
commit_outline: 若い魔法使いが師匠の試練を受ける話
genre: ファンタジー
style: 日本

### Few-shot例

```json
{{
    "panel_num": 3,
    "commit_outline": "若い魔法使いが師匠の試練を受ける話",
    "genre": "ファンタジー",
    "style": "日本",
    "panels": [
        {{
            "コマ番号": 1,
            "キャラクター": "魔法使い",
            "セリフ": "師匠、試練を受ける準備ができました。",
            "シーン": "古びた魔法の塔の内部、蝋燭の灯り。若い魔法使いはローブを着て、手に杖を持っている。背景に古い書棚や魔法の道具が見える。"
        }},
        {{
            "コマ番号": 2,
            "キャラクター": "師匠",
            "セリフ": "よし、では始めるぞ。",
            "シーン": "古びた魔法の塔の内部、蝋燭の灯り。師匠は長い白髪と髭を持ち、古びたローブを着ている。背景に魔法の書棚が見える。"
        }},
        {{
            "コマ番号": 3,
            "キャラクター": "魔法使い",
            "セリフ": "絶対に合格してみせます！",
            "シーン": "古びた魔法の塔の内部、蝋燭の灯り。若い魔法使いは自信に満ちた表情で杖を握りしめている。背景に魔法の書棚が見える。"
        }}
    ]
}}
```
"""

router = APIRouter()

@router.post("/")
def generate_manga(req: MangaRequest):
    """
    漫画生成エンドポイント
      - Azure OpenAI で漫画用セリフ（JSON）生成
      - 各パネル毎に DALL-E API で画像生成
      - 画像をダウンロードして Base64 化し、コンテンツリストを作成
      - 外部 HTML 生成サービスに渡して結果を返す
    """
    try:
        # ① 漫画用ナレーション（JSON）の生成
        prompt_text = MANGA_PROMPT_TEMPLATE.format(
            panel_num=req.panel_num,
            commit_outline=req.commit_outline,
            genre=req.genre,
            style=req.style
        )
        narrative_dict = narrative.generate_manga_narrative(prompt_text)
        panels = narrative_dict.get("panels", [])
        if not panels:
            raise Exception("生成された漫画情報にパネルがありません。")
        
        # ② DALL-E による画像生成（並列処理）
        dalle_results = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(dalle.send_dalle_request_manga, panel, narrative_dict)
                for panel in panels
            ]
            for future in concurrent.futures.as_completed(futures):
                panel, result = future.result()
                if isinstance(result, Exception):
                    print(f"Panel {panel.get('コマ番号')} で画像生成エラー: {result}")
                else:
                    dalle_results.append((panel, result))
        
        # ③ 画像ダウンロード（Base64 化）
        content_list = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            download_futures = [
                executor.submit(dalle.download_image, panel, result)
                for panel, result in dalle_results
            ]
            for future in concurrent.futures.as_completed(download_futures):
                panel, download_result = future.result()
                if isinstance(download_result, Exception):
                    print(f"Panel {panel.get('コマ番号')} の画像ダウンロードエラー: {download_result}")
                else:
                    text = panel.get("セリフ", "")
                    content_list.append({
                        "img_src": download_result,
                        "text": text
                    })
        
        # ④ 外部 HTML 生成サービスを呼び出す
        html_result = html_generator.generate_html(is_comic=True, content=content_list)
        return html_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))