"""
views.py - Media library: upload files, add YouTube videos, cultural check, remove
==================================================================================

Owners: Jihe Qi (rules, task J-12), Dinesh Upreti (screens)
"""
from __future__ import annotations

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.decorators import role_required
from apps.core.exceptions import AccessDeniedError, CyberQuestError
from apps.core.models import SystemSettings

from .forms import MediaUploadForm, VideoForm
from .models import MediaFile, VideoEmbed
from .services import MediaService

STAFF = ("super_admin", "school_admin", "teacher")


@role_required(*STAFF)
def media_list(request):
    kind = request.GET.get("kind", "")
    files = MediaService.visible_to(request.user)
    if kind:
        files = files.filter(kind=kind)
    cfg = SystemSettings.load()
    return render(request, "medialib/list.html", {
        "files": files[:200], "videos": MediaService.videos_for(request.user)[:100], "kind": kind, "kinds": MediaFile.KINDS,
        "upload_form": MediaUploadForm(), "video_form": VideoForm(),
        "limits": {k: cfg.max_bytes(k) // (1024 * 1024) for k, _ in MediaFile.KINDS},
        "waiting": [m for m in files if m.needs_cultural_check and not m.cultural_check]})


@role_required(*STAFF)
def media_upload(request):
    form = MediaUploadForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        data = {k: v for k, v in form.cleaned_data.items() if k != "file"}
        try:
            obj = MediaService.upload(request.user, data, form.cleaned_data["file"], request)
        except CyberQuestError as exc:
            form.add_error("file", exc.message)
        else:
            note = " Students will see it after the Cultural Guide checks it." if obj.needs_cultural_check and not obj.cultural_check else ""
            messages.success(request, f"'{obj.title}' uploaded.{note}")
            return redirect("medialib:media_list")
    return render(request, "medialib/upload.html", {"form": form})


@role_required(*STAFF)
@require_POST
def video_add(request):
    form = VideoForm(request.POST)
    if form.is_valid():
        try:
            MediaService.add_video(request.user, form.cleaned_data["title"], form.cleaned_data["url"],
                                   form.cleaned_data["topic"])
        except CyberQuestError as exc:
            messages.error(request, exc.message)
        else:
            messages.success(request, "YouTube video added.")
    else:
        messages.error(request, "Please give a title and a YouTube link.")
    return redirect("medialib:media_list")


@role_required(*STAFF)
@require_POST
def cultural_approve(request, pk):
    media = get_object_or_404(MediaService.visible_to(request.user), pk=pk)
    MediaService.cultural_approve(request.user, media)
    messages.success(request, f"Cultural check given for '{media.title}'. Students can now see it.")
    return redirect("medialib:media_list")


@role_required(*STAFF)
@require_POST
def media_delete(request, pk):
    media = get_object_or_404(MediaService.visible_to(request.user), pk=pk)
    if not MediaService.can_change(request.user, media):
        raise AccessDeniedError("You can only remove your own files.")
    media.file.delete(save=False)
    media.delete()
    messages.info(request, "File removed.")
    return redirect("medialib:media_list")


@role_required(*STAFF)
@require_POST
def video_delete(request, pk):
    video = get_object_or_404(VideoEmbed, pk=pk)
    if not MediaService.can_change(request.user, video):
        raise AccessDeniedError("You can only remove your own videos.")
    video.delete()
    messages.info(request, "Video removed.")
    return redirect("medialib:media_list")
