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
        (None, {'fields':['name', 'desc', 'recording', 'date', 'images', 'tags']}),
        ]
#    list_display = ['tags']
    autocomplete_fields = ('tags','images')
    inlines = [AuthorInline, 
#            ImageInline, 
#            TagInline, 
            RepoInline, AttachmentInline]

class LinkInline(admin.StackedInline):
    model = models.AuthorLink
    extra = 1

class TagAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    fieldsets = [
        (None, {'fields': ['name', 'description']})
        ]

class PatchImageAdmin(admin.ModelAdmin):
    search_fields = ('image',)
    fieldsets = [
        (None, {'fields': ['image']})
        ]

class PatchAuthorNameAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['display_name', 'author_image', 'user']})
        ]
    inlines = [LinkInline]



class BinaryQuestionAdmin(admin.ModelAdmin):
    fields= ('question', 'answer_a', 'answer_b', 'slug', 'selection_method')

class BinaryResponseDetailAdmin(admin.ModelAdmin):
    exclude = []

class BRDInline(admin.TabularInline):
    model=models.BinaryResponseDetail
    extra=0

class BinaryAnswerAdmin(admin.ModelAdmin):
    fields = ('entryA', 'entryB', 'question', 'count_a', 'count_b')
    inlines = [BRDInline]


admin.site.register(models.PatchAuthorName, PatchAuthorNameAdmin)
admin.site.register(models.PatchTag, TagAdmin)
admin.site.register(models.PatchImages, PatchImageAdmin)

admin.site.register(PatchEntry, PatchAdmin)

admin.site.register(models.BinaryQuestion, BinaryQuestionAdmin)
admin.site.register(models.BinaryResponseDetail, BinaryResponseDetailAdmin)
admin.site.register(models.BinaryAnswer, BinaryAnswerAdmin)

