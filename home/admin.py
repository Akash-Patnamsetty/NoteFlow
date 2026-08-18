from django.contrib import admin
from .models import Profiles, Note, CodeBlock,NoteTag

admin.site.register(Profiles)
admin.site.register(Note)
admin.site.register(CodeBlock)
admin.site.register(NoteTag)

# Register your models here.
