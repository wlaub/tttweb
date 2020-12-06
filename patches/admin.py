from django.contrib import admin

from . import models
from .models import PatchEntry
class AuthorInline(admin.StackedInline):
    model = models.PatchAuthor
    extra = 1

class ImageInline(admin.StackedInline):
    model = models.PatchImages
    extra = 1

class AttachmentInline(admin.StackedInline):
    model = models.PatchAttachments
    extra = 0

class TagInline(admin.StackedInline):
    model = models.PatchTag
    extra = 1

class RepoInline(admin.TabularInline):
    model = models.PatchRepoAttachment
    extra = 1

class PatchAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields':['name', 'desc', 'recording', 'date']}),
        ]
    inlines = [AuthorInline, ImageInline, TagInline, RepoInline, AttachmentInline]

admin.site.register(PatchEntry, PatchAdmin)

