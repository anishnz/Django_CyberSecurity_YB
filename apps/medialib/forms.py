"""forms.py - Media upload and YouTube forms. Owner: Dinesh Upreti (screens)."""

from django import forms

from apps.learning.models import LearningTopic

from .models import MediaFile


class MediaUploadForm(forms.ModelForm):
    """Upload a picture, sound, video or PDF for a topic."""

    class Meta:
        model = MediaFile
        fields = ["kind", "title", "description", "alt_text", "topic", "needs_cultural_check", "is_published"]

    file = forms.FileField(
        help_text="Images: JPG, PNG, WebP, GIF. Audio: MP3, OGG, WAV, M4A. Video: MP4, WebM. "
        "Documents: PDF. The size limit is set by the Super Admin."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["topic"].queryset = LearningTopic.objects.select_related("level").order_by(
            "level__number", "sort_order"
        )
        self.fields["topic"].required = False


class VideoForm(forms.Form):
    title = forms.CharField(max_length=120)
    url = forms.URLField(
        label="YouTube link", help_text="For example https://www.youtube.com/watch?v=... or https://youtu.be/..."
    )
    topic = forms.ModelChoiceField(
        queryset=LearningTopic.objects.select_related("level").order_by("level__number", "sort_order"),
        required=False,
        help_text="The topic page where the video is shown.",
    )
