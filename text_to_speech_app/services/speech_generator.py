import requests
import os
from django.conf import settings
from datetime import datetime
import uuid

class SpeechGenerator:
    """音声生成サービス"""
    
    @staticmethod
    def text_to_speech(text, voice="nova", api_key=None):
        """テキストを音声に変換する"""
        if not api_key:
            api_key = settings.OPENAI_API_KEY
            
        api_url = "https://api.openai.com/v1/audio/speech"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "tts-1",
            "voice": voice,
            "input": text
        }
        
        try:
            response = requests.post(api_url, headers=headers, json=data)
            
            if response.status_code == 200:
                # 音声ファイルの保存先ディレクトリを確認
                os.makedirs(settings.AUDIO_FILES_DIR, exist_ok=True)
                
                # ファイル名を生成（一意のIDを使用）
                unique_id = uuid.uuid4().hex[:8]
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_name = f"tts_{timestamp}_{unique_id}_{voice}.mp3"
                
                # 保存先パス（メディアルート相対）
                relative_path = os.path.join('audio_files', file_name)
                full_path = os.path.join(settings.MEDIA_ROOT, relative_path)
                
                with open(full_path, "wb") as f:
                    f.write(response.content)
                
                return {
                    'success': True,
                    'file_path': relative_path,
                    'full_path': full_path
                }
            else:
                return {
                    'success': False,
                    'error': f"API エラー: {response.status_code}, 詳細: {response.text}"
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def process_text_in_chunks(text, voice="nova", max_chunk_size=4000):
        """テキストを適切なサイズに分割して処理する"""
        # テキストを適切なサイズに分割
        chunks = [text[i:i+max_chunk_size] for i in range(0, len(text), max_chunk_size)]
        
        results = []
        for chunk in chunks:
            result = SpeechGenerator.text_to_speech(chunk, voice)
            if result['success']:
                results.append(result)
        
        return results