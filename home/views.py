import re
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import transaction
from django.utils.html import escape
from .models import Profiles, Note, CodeBlock, NoteTag


CODEBLOCK_PLACEHOLDER_RE = re.compile(r'<div[^>]*data-codeblock="(\d+)"[^>]*></div>')


# ─────────────────────────────────────────────
# Authentication
# ─────────────────────────────────────────────

def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        full_name = request.POST.get("full_name")
        confirm_password = request.POST.get("confirm_password")
        username = request.POST.get("username")  # optional

        if password == confirm_password:
            print(email, password)
            user = User.objects.create_user(username=email, password=password)
            Profiles.objects.create(
                user=user,
                fullname=full_name,
                username=username if username else ""
            )
            login(request, user)
            return render(request, "dashboard.html")
        else:
            print(email, password)
            return render(request, "siginup.html", {"error": "confirm password is mismatch"})
    return render(request, "siginup.html")


def logins(request):
    # Already logged in? Skip straight to the dashboard.
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        email = request.POST.get("username")
        password = request.POST.get("password")
        print(email, password)
        us = authenticate(request, username=email, password=password)
        if us:
            login(request, us)
            return redirect("dashboard")
        else:
            return redirect("register")
    return render(request, "login.html")


@login_required
def signout(request):
    logout(request)
    return redirect("login")


# ─────────────────────────────────────────────
# Basic pages
# ─────────────────────────────────────────────

def home(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "home_page.html")


@login_required
def settings(request):
    if request.user.is_authenticated:
        return render(request, "settings.html")
    return redirect("login")


# ─────────────────────────────────────────────
# Helper: render note document with code blocks
# ─────────────────────────────────────────────

def render_note_document(note):
    """
    Turns note.document (HTML with <div data-codeblock="N"></div>
    placeholders) into read-only HTML for the view-only note page,
    swapping each placeholder for a labelled code block built from the
    matching CodeBlock row. Classes match the .wb-code-block styling
    in view_note.html.

    NOTE: the code is wrapped in <pre><code class="language-XXX">...
    </code></pre> — the <code> tag (and language-XXX class) is what
    highlight.js's `hljs.highlightElement()` looks for on the frontend.
    Without it, querySelectorAll('.wb-code-block pre code') finds
    nothing and highlighting silently never runs.
    """
    codeblocks_by_position = {cb.position: cb for cb in note.codeblocks.all()}

    def replace(match):
        cb = codeblocks_by_position.get(int(match.group(1)))
        if not cb:
            return ""
        return (
            '<div class="wb-code-block">'
            f'<div class="wb-code-topbar"><span>{escape(cb.get_language_display())}</span>'
            f'<span>{escape(cb.filename or "snippet")}</span></div>'
            f'<pre><code class="language-{escape(cb.language)}">{escape(cb.code)}</code></pre>'
            "</div>"
        )

    return CODEBLOCK_PLACEHOLDER_RE.sub(replace, note.document)


# ─────────────────────────────────────────────
# Dashboard
# ─────────────────────────────────────────────

@login_required
def dashboard(request):
    """Shows only the logged-in user's notes, most recently updated first.
    Optionally filtered to one tag via ?tag=<name> (set by clicking a
    tag in the sidebar)."""
    notes = (
        Note.objects
        .filter(user=request.user)
        .prefetch_related("tags")
        .order_by("-updated_at")
    )

    active_tag = request.GET.get("tag", "").strip()
    if active_tag:
        notes = notes.filter(tags__name=active_tag)

    return render(request, "dashboard.html", {
        "notes": notes,
        "active_tag": active_tag
    })


# ─────────────────────────────────────────────
# Read-only note view
# ─────────────────────────────────────────────

@login_required
def view_note(request, note_id):
    """
    Read-only detail page for a note. This is where dashboard cards link
    to now — Edit/Delete are explicit actions from here, not the default.
    Also tracks a small "recently opened" list in the session, and shows
    pinned notes separately.
    """
    note = get_object_or_404(Note, id=note_id, user=request.user)

    recent_ids = request.session.get("recent_note_ids", [])
    recent_ids = [nid for nid in recent_ids if nid != note.id]
    recent_ids.insert(0, note.id)
    recent_ids = recent_ids[:8]
    request.session["recent_note_ids"] = recent_ids

    pinned_notes = (
        Note.objects.filter(user=request.user, is_pinned=True)
        .prefetch_related("tags")
        .order_by("-updated_at")
    )
    pinned_ids = set(pinned_notes.values_list("id", flat=True))

    notes_by_id = {
        n.id: n for n in Note.objects.filter(user=request.user, id__in=recent_ids)
        .prefetch_related("tags")
    }
    recent_notes = [
        notes_by_id[nid] for nid in recent_ids
        if nid in notes_by_id and nid not in pinned_ids
    ]

    return render(request, "view_note.html", {
        "note": note,
        "rendered_document": render_note_document(note),
        "tags": note.tags.all(),
        "pinned_notes": pinned_notes,
        "recent_notes": recent_notes,
    })


@login_required
def toggle_pin(request, note_id):
    """Pins/unpins a note so it shows up (or not) in the Pinned sidebar section."""
    note = get_object_or_404(Note, id=note_id, user=request.user)
    note.is_pinned = not note.is_pinned
    note.save(update_fields=["is_pinned"])
    return JsonResponse({"is_pinned": note.is_pinned})


# ─────────────────────────────────────────────
# Add / Edit note
# ─────────────────────────────────────────────

@login_required
def addnote(request, note_id=None):
    """
    GET  -> renders the editor page (blank for a new note, pre-loaded
            with note data if note_id is given / editing an existing note).
    POST -> saves the note (create if note_id is None, update otherwise).
            Expects JSON in the body — see save_note_from_request() below.
    """
    if request.method == "POST":
        return save_note_from_request(request, note_id)

    note = None
    if note_id:
        note = get_object_or_404(Note, id=note_id, user=request.user)

    print("adding note ")
    return render(request, "addnote.html", {"note": note})


def save_note_from_request(request, note_id=None):
    """
    Does the actual save. Expected JSON body:

    {
        "title": "My note title",
        "document": "<p>Some text</p><div data-codeblock=\"0\"></div><p>more</p>",
        "codeblocks": [
            {"position": 0, "language": "python", "filename": "snippet.py", "code": "print('hi')"}
        ],
        "tags": ["django", "auth"]
    }

    "document" is the rich-text HTML with a placeholder div for every code
    block (matches Note.document's docstring in models.py). The real code
    lives in "codeblocks", matched back up by position.
    """
    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    title = (payload.get("title") or "").strip() or "Untitled Note"
    document = payload.get("document", "")
    codeblocks = payload.get("codeblocks", [])
    tags = payload.get("tags", [])

    if not isinstance(codeblocks, list) or not isinstance(tags, list):
        return JsonResponse({"error": "codeblocks and tags must be lists"}, status=400)

    try:
        with transaction.atomic():
            if note_id:
                note = get_object_or_404(Note, id=note_id, user=request.user)
                note.title = title
                note.document = document
                note.save()
                # Simplest way to keep child rows in sync with whatever
                # the editor currently holds: wipe and rewrite them.
                note.codeblocks.all().delete()
                note.tags.all().delete()
            else:
                note = Note.objects.create(
                    user=request.user,
                    title=title,
                    document=document,
                )

            code_objs = [
                CodeBlock(
                    note=note,
                    position=block.get("position", i),
                    language=block.get("language", "python"),
                    filename=block.get("filename", ""),
                    code=block.get("code", ""),
                )
                for i, block in enumerate(codeblocks)
            ]
            if code_objs:
                CodeBlock.objects.bulk_create(code_objs)

            tag_objs = [
                NoteTag(note=note, name=name.strip())
                for name in tags
                if name and name.strip()
            ]
            if tag_objs:
                NoteTag.objects.bulk_create(tag_objs, ignore_conflicts=True)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({
        "id": note.id,
        "title": note.title,
        "updated_at": note.updated_at.isoformat(),
        "is_shared": note.is_shared,
        "share_token": str(note.share_token) if note.is_shared else None,
    }, status=200)


# ─────────────────────────────────────────────
# Load existing note for editor (AJAX)
# ─────────────────────────────────────────────

@login_required
def get_note(request, note_id):
    """Returns a note's full data as JSON, for hydrating the editor on load."""
    note = get_object_or_404(Note, id=note_id, user=request.user)
    return JsonResponse({
        "id": note.id,
        "title": note.title,
        "document": note.document,
        "codeblocks": [
            {
                "position": cb.position,
                "language": cb.language,
                "filename": cb.filename,
                "code": cb.code,
            }
            for cb in note.codeblocks.all()
        ],
        "tags": [t.name for t in note.tags.all()],
        "created_at": note.created_at.isoformat(),
        "updated_at": note.updated_at.isoformat(),
        "is_shared": note.is_shared,
        "share_token": str(note.share_token) if note.is_shared else None,
    })


# ─────────────────────────────────────────────
# Share / Delete
# ─────────────────────────────────────────────

@login_required
def toggle_share(request, note_id):
    note = get_object_or_404(Note, id=note_id, user=request.user)
    note.is_shared = not note.is_shared
    note.save(update_fields=["is_shared"])
    return JsonResponse({
        "is_shared": note.is_shared,
        "share_token": str(note.share_token) if note.is_shared else None,
    })


@login_required
def delete_note(request, note_id):
    note = get_object_or_404(Note, id=note_id, user=request.user)
    note.delete()
    return JsonResponse({"deleted": True})


def shared_note_view(request, token):
    """Public, read-only view of a shared note — no login required."""
    note = get_object_or_404(Note, share_token=token, is_shared=True)
    return render(request, "shared_note.html", {
        "note": note,
        "codeblocks": note.codeblocks.all(),
        "tags": note.tags.all(),
    })