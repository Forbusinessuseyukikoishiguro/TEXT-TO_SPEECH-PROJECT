from django import forms
from .models import Summary


class TextInputForm(forms.Form):
    """テキスト入力フォーム"""

    title = forms.CharField(
        label="タイトル",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    text_input = forms.CharField(
        label="テキスト",
        widget=forms.Textarea(attrs={"rows": 10, "class": "form-control"}),
        required=False,
    )
    url = forms.URLField(
        label="URL",
        required=False,
        widget=forms.URLInput(attrs={"class": "form-control"}),
    )
    source_type = forms.ChoiceField(
        label="入力ソース",
        choices=[
            ("text", "テキストを直接入力"),
            ("url", "URLからテキストを取得"),
            ("pdf", "PDFファイルをアップロード"),
        ],
        widget=forms.RadioSelect,
        initial="text",
    )
    feature_choice = forms.ChoiceField(
        label="実行する機能",
        choices=[
            ("1", "テキストの読み上げのみ"),
            ("2", "テキストの要約のみ"),
            ("3", "テキストの要約と読み上げ（要約を読み上げ）"),
            ("4", "テキストの要約と読み上げ（元のテキストを読み上げ）"),
        ],
        widget=forms.RadioSelect,
        initial="3",
    )
    voice_type = forms.ChoiceField(
        label="音声の種類",
        choices=[
            ("nova", "Nova (女性 - 日本語対応)"),
            ("alloy", "Alloy (男性風 - 多言語)"),
            ("echo", "Echo (男性風 - 多言語)"),
            ("fable", "Fable (男性風 - 多言語)"),
            ("onyx", "Onyx (男性風 - 多言語)"),
            ("shimmer", "Shimmer (女性風 - 多言語)"),
        ],
        widget=forms.RadioSelect,
        initial="nova",
    )
    summary_length = forms.ChoiceField(
        label="要約の長さ",
        choices=[
            ("100", "超短縮（約100語/約400文字）"),
            ("200", "短縮（約200語/約800文字）"),
            ("300", "標準（約300語/約1200文字）"),
            ("500", "詳細（約500語/約2000文字）"),
            ("800", "非常に詳細（約800語/約3200文字）"),
            ("custom", "カスタム"),
        ],
        widget=forms.RadioSelect,
        initial="300",
    )
    custom_length = forms.IntegerField(
        label="カスタム長さ（単語数）",
        required=False,
        min_value=50,
        max_value=2000,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        source_type = cleaned_data.get("source_type")
        text_input = cleaned_data.get("text_input")
        url = cleaned_data.get("url")

        if source_type == "text" and not text_input:
            self.add_error("text_input", "テキスト入力が空です")
        elif source_type == "url" and not url:
            self.add_error("url", "URLが空です")

        summary_length = cleaned_data.get("summary_length")
        custom_length = cleaned_data.get("custom_length")

        if summary_length == "custom" and not custom_length:
            self.add_error("custom_length", "カスタム長さを入力してください")

        return cleaned_data


class PDFUploadForm(forms.Form):
    """PDFアップロードフォーム"""

    title = forms.CharField(
        label="タイトル",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    pdf_file = forms.FileField(
        label="PDFファイル",
        widget=forms.FileInput(
            attrs={"class": "form-control", "accept": "application/pdf"}
        ),
    )
