from django.contrib import admin
from .models import Summary, AudioFile, PDFFile


class AudioFileInline(admin.TabularInline):
    model = AudioFile
    extra = 0
    fields = ("file_path", "is_summary", "voice_type", "created_at")
    readonly_fields = ("created_at",)


class PDFFileInline(admin.StackedInline):
    model = PDFFile
    extra = 0
    fields = ("file", "file_name", "uploaded_at")
    readonly_fields = ("uploaded_at",)


@admin.register(Summary)
class SummaryAdmin(admin.ModelAdmin):
    list_display = ("title", "source_type", "has_summary", "audio_count", "created_at")
    list_filter = ("source_type", "created_at")
    search_fields = ("title", "original_text", "summary_text")
    readonly_fields = ("created_at", "updated_at")
    inlines = [AudioFileInline, PDFFileInline]

    def has_summary(self, obj):
        return bool(obj.summary_text)

    has_summary.boolean = True
    has_summary.short_description = "要約"

    def audio_count(self, obj):
        return obj.audio_files.count()

    audio_count.short_description = "音声ファイル数"


@admin.register(AudioFile)
class AudioFileAdmin(admin.ModelAdmin):
    list_display = ("summary", "voice_type", "is_summary", "created_at")
    list_filter = ("voice_type", "is_summary", "created_at")
    search_fields = ("summary__title",)
    readonly_fields = ("created_at",)


@admin.register(PDFFile)
class PDFFileAdmin(admin.ModelAdmin):
    list_display = ("file_name", "summary", "uploaded_at")
    list_filter = ("uploaded_at",)
    search_fields = ("file_name", "summary__title")
    readonly_fields = ("uploaded_at",)
