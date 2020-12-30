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
#    model = models.PatchEntry.tags
    extra = 1

class RepoInline(admin.TabularInline):
    model = models.PatchRepoAttachment
    extra = 1

class PatchAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields':['name', 'desc', 'recording', 'date', 'tags']}),
        ]
#    list_display = ['tags']
    autocomplete_fields = ('tags',)
    inlines = [AuthorInline, ImageInline, 
#            TagInline, 
            RepoInline, AttachmentInline]

class LinkInline(admin.StackedInline):
    model = models.AuthorLink
    extra = 1

class TagAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    fieldsets = [
        (None, {'fields': ['name']})
        ]

class PatchAuthorNameAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['display_name', 'author_image', 'user']})
        ]
    inlines = [LinkInline]

admin.site.register(models.PatchAuthorName, PatchAuthorNameAdmin)
admin.site.register(models.PatchTag, TagAdmin)

admin.site.register(PatchEntry, PatchAdmin)
