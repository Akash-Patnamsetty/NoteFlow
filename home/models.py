from django.db import models
from django.contrib.auth.models import User
import uuid
from django.utils.html import strip_tags
from django.utils.text import Truncator
import re
# Create your models here.

class Profiles(models.Model):
 user=models.OneToOneField(User,on_delete=models.CASCADE)
 fullname=models.CharField(max_length=100)
 username = models.CharField(max_length=100, blank=True, default="")
 def __str__(self):
  return self.user.username



class Note(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notes")
    title = models.CharField(max_length=255, blank=True, default="Untitled Note")
 
    # Rich-text HTML body. Wherever a code block sits in the note,
    # this contains a placeholder like <div data-codeblock="0"></div>
    # instead of the actual code — the real code lives in CodeBlock rows,
    # matched back up on render via `position`.
    document = models.TextField(blank=True, default="")
    snippet = models.CharField(max_length=200, blank=True, default="", editable=False)
    
 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
 
    is_shared = models.BooleanField(default=False)
    share_token = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, null=True, blank=True
    )
    is_pinned = models.BooleanField(default=False)
 
    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["user", "-updated_at"]),
        ]
 
    def __str__(self):
        return f"{self.title} ({self.user.username})"
    
    def _build_snippet(self):
        """
        Plain-text preview of the note body for dashboard cards.
        Strips HTML tags and collapses code-block placeholders down to
        a short marker so the preview text doesn't get gappy/odd.
        """
        text = re.sub(r'<div[^>]*data-codeblock="\d+"[^>]*></div>', ' [code] ', self.document)
        text = strip_tags(text)
        text = " ".join(text.split())
        return Truncator(text).chars(140)
 
    def save(self, *args, **kwargs):
        # Keep the stored snippet in sync with `document` every time the
        # note is saved — from the editor, the admin, or anywhere else.
        self.snippet = self._build_snippet()
        super().save(*args, **kwargs)
 
 
# ─────────────────────────────────────────────
# Code Block (belongs to a Note)
# ─────────────────────────────────────────────
 
class CodeBlock(models.Model):
    LANGUAGE_CHOICES = [
        ("python", "Python"),
        ("javascript", "JavaScript"),
        ("html", "HTML"),
        ("css", "CSS"),
        ("sql", "SQL"),
        ("bash", "Bash"),
    ]
 
    note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name="codeblocks")
 
    # Sequence order — matches the N in <div data-codeblock="N"> inside Note.document
    position = models.PositiveIntegerField()
 
    language = models.CharField(max_length=30, choices=LANGUAGE_CHOICES, default="python")
    filename = models.CharField(max_length=255, blank=True, default="")
    code = models.TextField(blank=True, default="")
 
    created_at = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        ordering = ["position"]
        unique_together = ("note", "position")
        indexes = [
            models.Index(fields=["note", "position"]),
        ]
 
    def __str__(self):
        return f"{self.filename or 'snippet'} ({self.language}) — {self.note.title}"
 
 
# ─────────────────────────────────────────────
# Note Tag
# ─────────────────────────────────────────────
 
class NoteTag(models.Model):
    note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name="tags")
    name = models.CharField(max_length=50)
 
    class Meta:
        unique_together = ("note", "name")
        indexes = [
            models.Index(fields=["name"]),
        ]
 
    def __str__(self):
        return self.name