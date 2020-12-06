from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.views import generic

from .models import PatchEntry

class IndexView(generic.ListView):
    template_name = 'patches/index.html'
    context_object_name = 'patch_entries'

    def get_queryset(self):
        return PatchEntry.objects.order_by('-date')

class DetailView(generic.DetailView):
    model = PatchEntry
    template_name = 'patches/detail.html'

