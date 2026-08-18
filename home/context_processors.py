from django.db.models import Count

from .models import Note, NoteTag


def notes_sidebar(request):
    """
    Runs on every request. Injects the data nav.html's sidebar needs
    (total note count, and each tag with how many notes use it) so
    every page that extends nav.html shows real data without every
    view having to fetch and pass it manually.
    """
    if not request.user.is_authenticated:
        return {}

    all_notes_count = Note.objects.filter(user=request.user).count()

    sidebar_tags = (
        NoteTag.objects.filter(note__user=request.user)
        .values("name")
        .annotate(count=Count("note", distinct=True))
        .order_by("-count", "name")
    )

    return {
        "sidebar_all_notes_count": all_notes_count,
        "sidebar_tags": sidebar_tags,
    }