# text_to_speech_app/services/text_processor.py
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse
import PyPDF2
import os
from django.conf import settings


class TextProcessor:
    """テキスト処理サービス"""

    @staticmethod
    def get_text_from_url(url):
        """URLからテキストを取得する"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers)
            response.encoding = response.apparent_encoding

            soup = BeautifulSoup(response.text, "html.parser")

            # タイトル情報の取得
            title = soup.title.string if soup.title else url

            # テキストコンテンツの取得
            paragraphs = soup.find_all("p")
            text_content = "\n".join([p.get_text().strip() for p in paragraphs])

            if len(text_content) < 100:
                text_content = soup.body.get_text(separator="\n", strip=True)

            return {
                "success": True,
                "title": title,
                "content": text_content,
                "url": url,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_text_from_pdf(pdf_file):
        """PDFファイルからテキストを抽出する"""
        try:
            # PDFからテキストを抽出
            text_content = ""

            # PyPDF2でPDFを読み込む
            pdf_reader = PyPDF2.PdfReader(pdf_file)

            total_pages = len(pdf_reader.pages)

            # 各ページからテキストを抽出
            for page_num in range(total_pages):
                page = pdf_reader.pages[page_num]
                text_content += page.extract_text() + "\n\n"

            # PDFファイルの名前を取得
            file_name = os.path.basename(pdf_file.name)

            return {
                "success": True,
                "title": file_name,
                "content": text_content,
                "page_count": total_pages,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def summarize_text(text, max_words=300, api_key=None):
        """OpenAI Chat APIを使ってテキストを要約する"""
        if not api_key:
            api_key = settings.OPENAI_API_KEY

        api_url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        # 文字数の目安を計算（日本語では単語数×4程度が文字数の目安）
        char_estimate = max_words * 4

        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": f"あなたは与えられた文章を約{max_words}語（約{char_estimate}文字）に要約するアシスタントです。",
                },
                {
                    "role": "user",
                    "content": f"以下の文章を約{max_words}語（約{char_estimate}文字）に要約してください:\n\n{text}",
                },
            ],
        }

        try:
            response = requests.post(api_url, headers=headers, json=data)

            if response.status_code == 200:
                result = response.json()
                summary = result["choices"][0]["message"]["content"]

                # 実際の単語数と文字数を計算
                word_count = len(summary.split())
                char_count = len(summary)

                return {
                    "success": True,
                    "summary": summary,
                    "word_count": word_count,
                    "char_count": char_count,
                }
            else:
                return {
                    "success": False,
                    "error": f"API エラー: {response.status_code}, 詳細: {response.text}",
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
