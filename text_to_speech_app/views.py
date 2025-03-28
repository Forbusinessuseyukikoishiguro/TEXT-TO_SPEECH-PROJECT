from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, FileResponse, HttpResponse
from django.conf import settings
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
import os
import json

from .models import Summary, AudioFile, PDFFile
from .forms import TextInputForm, PDFUploadForm
from .services.text_processor import TextProcessor
from .services.speech_generator import SpeechGenerator


def index(request):
    """メイン画面を表示"""
    form = TextInputForm()
    pdf_form = PDFUploadForm()
    return render(
        request,
        "text_to_speech_app/index.html",
        {
            "form": form,
            "pdf_form": pdf_form,
        },
    )


def process_text(request):
    """テキスト処理リクエストを処理"""
    if request.method == "POST":
        form = TextInputForm(request.POST)

        if form.is_valid():
            source_type = form.cleaned_data["source_type"]
            feature_choice = form.cleaned_data["feature_choice"]
            title = form.cleaned_data["title"]
            content = ""
            url = None

            # テキストの取得
            if source_type == "text":
                content = form.cleaned_data["text_input"]
                if not title:
                    title = "直接入力テキスト"
            elif source_type == "url":
                url = form.cleaned_data["url"]
                result = TextProcessor.get_text_from_url(url)
                if result["success"]:
                    content = result["content"]
                    if not title:
                        title = result["title"]
                else:
                    messages.error(
                        request,
                        f"URLからのテキスト取得に失敗しました: {result.get('error')}",
                    )
                    return redirect("text_to_speech_app:index")
            else:
                messages.error(
                    request, "PDFの処理にはPDFアップロードフォームを使用してください"
                )
                return redirect("text_to_speech_app:index")

            # 要約処理（必要な場合）
            summary_text = None
            if feature_choice in ["2", "3", "4"]:  # 要約機能がある場合
                summary_length = form.cleaned_data["summary_length"]
                max_words = (
                    int(summary_length)
                    if summary_length != "custom"
                    else form.cleaned_data["custom_length"]
                )

                result = TextProcessor.summarize_text(content, max_words)
                if result["success"]:
                    summary_text = result["summary"]
                else:
                    messages.error(
                        request, f"テキストの要約に失敗しました: {result.get('error')}"
                    )
                    return redirect("text_to_speech_app:index")

            # データベースに保存
            summary = Summary.objects.create(
                title=title,
                original_text=content,
                summary_text=summary_text,
                source_url=url,
                source_type=source_type,
            )

            # 音声生成（必要な場合）
            if feature_choice in ["1", "3", "4"]:  # 音声生成機能がある場合
                voice_type = form.cleaned_data["voice_type"]

                if feature_choice == "1":  # 読み上げのみ
                    results = SpeechGenerator.process_text_in_chunks(
                        content, voice_type
                    )
                    for result in results:
                        if result["success"]:
                            AudioFile.objects.create(
                                summary=summary,
                                file_path=result["file_path"],
                                is_summary=False,
                                voice_type=voice_type,
                            )

                elif feature_choice == "3" and summary_text:  # 要約を読み上げ
                    results = SpeechGenerator.process_text_in_chunks(
                        summary_text, voice_type
                    )
                    for result in results:
                        if result["success"]:
                            AudioFile.objects.create(
                                summary=summary,
                                file_path=result["file_path"],
                                is_summary=True,
                                voice_type=voice_type,
                            )

                elif feature_choice == "4":  # 元テキストを読み上げ
                    results = SpeechGenerator.process_text_in_chunks(
                        content, voice_type
                    )
                    for result in results:
                        if result["success"]:
                            AudioFile.objects.create(
                                summary=summary,
                                file_path=result["file_path"],
                                is_summary=False,
                                voice_type=voice_type,
                            )

            messages.success(request, "処理が完了しました")
            return redirect("text_to_speech_app:summary_detail", summary_id=summary.id)

        # フォームが無効な場合
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{form[field].label}: {error}")
        return redirect("text_to_speech_app:index")

    # GETリクエストの場合はトップページにリダイレクト
    return redirect("text_to_speech_app:index")


def upload_pdf(request):
    """PDFファイルをアップロードして処理"""
    if request.method == "POST":
        form = PDFUploadForm(request.POST, request.FILES)

        if form.is_valid():
            title = form.cleaned_data["title"]
            pdf_file = request.FILES["pdf_file"]

            # PDFからテキストを抽出
            result = TextProcessor.get_text_from_pdf(pdf_file)

            if not result["success"]:
                messages.error(
                    request, f"PDFの処理に失敗しました: {result.get('error')}"
                )
                return redirect("text_to_speech_app:index")

            content = result["content"]
            if not title:
                title = result["title"]

            # データベースに保存
            summary = Summary.objects.create(
                title=title, original_text=content, source_type="pdf"
            )

            # PDFファイル自体も保存
            PDFFile.objects.create(
                summary=summary, file=pdf_file, file_name=pdf_file.name
            )

            messages.success(request, "PDFファイルの処理が完了しました")
            return redirect("text_to_speech_app:summary_detail", summary_id=summary.id)

        # フォームが無効な場合
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{form[field].label}: {error}")

    return redirect("text_to_speech_app:index")


def summary_detail(request, summary_id):
    """要約の詳細を表示"""
    summary = get_object_or_404(Summary, id=summary_id)
    audio_files = summary.audio_files.all()

    return render(
        request,
        "text_to_speech_app/summary.html",
        {
            "summary": summary,
            "audio_files": audio_files,
        },
    )


def history(request):
    """履歴一覧を表示"""
    summaries = Summary.objects.all().order_by("-created_at")
    return render(
        request,
        "text_to_speech_app/history.html",
        {
            "summaries": summaries,
        },
    )


def delete_summary(request, summary_id):
    """要約を削除"""
    summary = get_object_or_404(Summary, id=summary_id)

    # 関連する音声ファイルの物理ファイルも削除
    for audio in summary.audio_files.all():
        if audio.file_path and os.path.exists(
            os.path.join(settings.MEDIA_ROOT, str(audio.file_path))
        ):
            os.remove(os.path.join(settings.MEDIA_ROOT, str(audio.file_path)))

    # PDFファイルも削除
    try:
        pdf_file = summary.pdf_file
        if (
            pdf_file
            and pdf_file.file
            and os.path.exists(os.path.join(settings.MEDIA_ROOT, str(pdf_file.file)))
        ):
            os.remove(os.path.join(settings.MEDIA_ROOT, str(pdf_file.file)))
    except PDFFile.DoesNotExist:
        pass

    # データベースからレコードを削除
    summary.delete()

    messages.success(request, "要約を削除しました")
    return redirect("text_to_speech_app:history")


def play_audio(request, audio_id):
    """音声ファイルを再生"""
    audio = get_object_or_404(AudioFile, id=audio_id)
    file_path = os.path.join(settings.MEDIA_ROOT, str(audio.file_path))

    if os.path.exists(file_path):
        return FileResponse(open(file_path, "rb"), content_type="audio/mpeg")
    else:
        return HttpResponse("ファイルが見つかりません", status=404)
