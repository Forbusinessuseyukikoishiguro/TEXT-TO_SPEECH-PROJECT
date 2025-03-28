from django.urls import path
from . import views

app_name = "text_to_speech_app"

urlpatterns = [
    path("", views.index, name="index"),
    path("process/", views.process_text, name="process_text"),
    path("summary/<int:summary_id>/", views.summary_detail, name="summary_detail"),
    path("history/", views.history, name="history"),
    path("delete/<int:summary_id>/", views.delete_summary, name="delete_summary"),
    path("play/<int:audio_id>/", views.play_audio, name="play_audio"),
    path("upload-pdf/", views.upload_pdf, name="upload_pdf"),
]
