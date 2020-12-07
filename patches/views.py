from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.views import generic

from .models import PatchEntry

class IndexView(generic.ListView):
    template_name = 'patches/index.html'
    context_object_name = 'patch_entries'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        return context

    def get_queryset(self):
        q = PatchEntry.objects.order_by('-date')
        print(self.kwargs)
        if 'tag' in self.kwargs:
            q = q.filter(tags__icontains=self.kwargs['tag'])
        return q

class DetailView(generic.DetailView):
    model = PatchEntry
    template_name = 'patches/detail.html'

