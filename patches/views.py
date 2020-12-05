from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse

from .models import PatchEntry

def index(request):
    patch_entries = PatchEntry.objects.order_by('-date')
    context = {'patch_entries': patch_entries}
    return render(request, 'patches/index.html', context)

def entry(request, patch_id):
    entry = get_object_or_404(PatchEntry, pk=patch_id)
    context = {'entry': entry}
    return render(request, 'patches/entry.html', context)

