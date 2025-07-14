# app/api/endpoints/ehon.py
import concurrent.futures
from fastapi import APIRouter, HTTPException
from app.models.schemas import EhonRequest
from app.services import narrative, dalle, html_generator

router = APIRouter()

@router.post("/")
def generate_ehon(req: EhonRequest):
    """
    絵本生成エンドポイント
      - Azure OpenAI でナレーション（JSON）生成
      - 各パネル毎に DALL-E API 呼び出し
      - 生成された画像をダウンロードして Base64 化
      - コンテンツを整形して外部 HTML 生成 API を呼び出す
    """
    try:
        # ① ナレーション（JSON）生成
        narrative_dict = narrative.generate_ehon_narrative(
            req.panel_num, req.commit_outline, req.genre, req.style
        )
        panels = narrative_dict.get("panels", [])
        if not panels:
            raise Exception("生成されたナレーションにパネル情報がありません。")
        
        # ② DALL-E による画像生成（並列処理）
        dalle_results = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(dalle.send_dalle_request_ehon, panel, req.genre, req.style)
                for panel in panels
            ]
            for future in concurrent.futures.as_completed(futures):
                panel, result = future.result()
                if isinstance(result, Exception):
                    print(f"Panel {panel.get('コマ番号')} で画像生成エラー: {result}")
                else:
                    dalle_results.append((panel, result))
        
        # ③ 各パネルの画像ダウンロード（Base64 化）
        ehon_images = {}
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
                    ehon_images[panel.get("コマ番号")] = download_result
        
        # ④ コンテンツ整形（パネル数に応じた画像2点＋テキスト）
        if req.panel_num == 1:
            panel = panels[0]
            img_b64 = ehon_images.get(panel["コマ番号"], "")
            text = panel.get("ナレーション", "")
            content = {
                "img_src_1": img_b64,
                "img_src_2": img_b64,
                "text": text
            }
        else:
            sorted_panels = sorted(panels, key=lambda p: p["コマ番号"])
            img_b64_1 = ehon_images.get(sorted_panels[0]["コマ番号"], "")
            img_b64_2 = ehon_images.get(sorted_panels[1]["コマ番号"], "")
            texts = [panel.get("ナレーション", "") for panel in sorted_panels]
            content = {
                "img_src_1": img_b64_1,
                "img_src_2": img_b64_2,
                "text": "\n".join(texts)
            }
        
        # ⑤ 外部の HTML 生成サービスを呼び出す
        html_result = html_generator.generate_html(is_comic=False, content=content)
        return html_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
