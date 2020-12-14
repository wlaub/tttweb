from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.views import generic

from .models import PatchEntry, PatchAuthor

class IndexView(generic.ListView):
    template_name = 'patches/index.html'
    context_object_name = 'patch_entries'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        author = self.request.GET.get('author', False)
        try:
            user = PatchAuthor.objects.get(author__display_name=author)
            context['author'] = user
        except:
            pass
        tags = self.request.GET.get('tags', False)
        if tags:
            context['taglist'] = tags.split(',')
        else:
            context['taglist'] = []
        context['tags'] = tags

        return context

    def get_queryset(self):
        q = PatchEntry.objects.order_by('-date')

        author = self.request.GET.get('author', False)
        if author:
            q = q.filter(authors__author__display_name=author)
        tags = self.request.GET.get('tags', False)
        if tags:
            taglist = tags.split(',')
            for tag in taglist:
                q = q.filter(tags__name=tag)

        return q

class DetailView(generic.DetailView):
    model = PatchEntry
    template_name = 'patches/detail.html'

class CompareView(generic.ListView):
    model = PatchEntry
    template_name = 'patches/compare.html'

    def get_quesyset(self):
        return None
    

