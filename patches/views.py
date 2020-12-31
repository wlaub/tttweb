from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.views import generic

from django.core.exceptions import ObjectDoesNotExist

from .models import PatchEntry, PatchAuthor, BinaryQuestion

class IndexView(generic.ListView):
    template_name = 'patches/index.html'
    context_object_name = 'patch_entries'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        author = self.request.GET.get('author', False)
        try:
            user = PatchAuthor.objects.get(author__display_name=author)
            context['author'] = user
        except ObjectDoesNotExist:
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
    context_object_name = 'patch_entries'

    default_pk = 1

    class Dummy():
        question = 'No such question'
        def get_options(self): return None

    def get_question(self):
        try:
            return BinaryQuestion.objects.get(pk=self.kwargs.get('pk', self.default_pk))
        except ObjectDoesNotExist:
            return None

    def get_context_data(self, **kwargs):
        context = super(CompareView, self).get_context_data(**kwargs)

        context['question'] = self.get_question()

        context['question_list'] = BinaryQuestion.objects.all()

        return context

    def get_queryset(self):
        question = self.get_question()

        if question:
            options = question.get_options()
            return options
        else:
            return None
    

