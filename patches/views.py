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

        return context

    def get_queryset(self):
        q = PatchEntry.objects.order_by('-date')
        print()
        print(self.kwargs)

        print()
        author = self.request.GET.get('author', False)
        if author:
            q = q.filter(authors__author__display_name=author)

        return q

class DetailView(generic.DetailView):
    model = PatchEntry
    template_name = 'patches/detail.html'

