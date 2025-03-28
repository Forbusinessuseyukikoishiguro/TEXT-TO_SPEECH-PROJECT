from django.db import models
from django.utils import timezone


class Summary(models.Model):
    """要約モデル"""

    title = models.CharField("タイトル", max_length=255, blank=True)
    original_text = models.TextField("元のテキスト")
    summary_text = models.TextField("要約テキスト", blank=True, null=True)
    source_url = models.URLField("ソースURL", blank=True, null=True)
    source_type = models.CharField(
        "ソースタイプ",
        max_length=50,
        choices=[
            ("url", "URL"),
            ("pdf", "PDFファイル"),
            ("text", "直接入力"),
        ],
    )
    created_at = models.DateTimeField("作成日時", default=timezone.now)
    updated_at = models.DateTimeField("更新日時", auto_now=True)

    def __str__(self):
        return self.title or f"要約 {self.id}"

    class Meta:
        verbose_name = "要約"
        verbose_name_plural = "要約一覧"
        ordering = ["-created_at"]

    @property
    def summary_length(self):
        """要約の長さを返す"""
        if self.summary_text:
            return len(self.summary_text)
        return 0


class AudioFile(models.Model):
    """音声ファイルモデル"""

    summary = models.ForeignKey(
        Summary, on_delete=models.CASCADE, related_name="audio_files"
    )
    file_path = models.FileField("ファイルパス", upload_to="audio_files/%Y/%m/%d/")
    is_summary = models.BooleanField("要約音声", default=False)
    voice_type = models.CharField(
        "音声タイプ",
        max_length=50,
        choices=[
            ("nova", "Nova (女性)"),
            ("alloy", "Alloy (男性風)"),
            ("echo", "Echo (男性風)"),
            ("fable", "Fable (男性風)"),
            ("onyx", "Onyx (男性風)"),
            ("shimmer", "Shimmer (女性風)"),
        ],
        default="nova",
    )
    created_at = models.DateTimeField("作成日時", default=timezone.now)

    def __str__(self):
        return f"{self.summary} - {'要約' if self.is_summary else '元文'} 音声"

    class Meta:
        verbose_name = "音声ファイル"
        verbose_name_plural = "音声ファイル一覧"
        ordering = ["-created_at"]


class PDFFile(models.Model):
    """PDFファイルモデル"""

    summary = models.OneToOneField(
        Summary, on_delete=models.CASCADE, related_name="pdf_file"
    )
    file = models.FileField("PDFファイル", upload_to="pdf_files/%Y/%m/%d/")
    file_name = models.CharField("ファイル名", max_length=255)
    uploaded_at = models.DateTimeField("アップロード日時", default=timezone.now)

    def __str__(self):
        return self.file_name

    class Meta:
        verbose_name = "PDFファイル"
        verbose_name_plural = "PDFファイル一覧"
