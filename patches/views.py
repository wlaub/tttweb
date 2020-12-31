import hashlib

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.views import generic

from django.core.exceptions import ObjectDoesNotExist

from django.db.models import Q

from .models import PatchEntry, PatchAuthorName, BinaryQuestion, PatchTag
from . import models



class IndexView(generic.ListView):
    template_name = 'patches/index.html'
    context_object_name = 'patch_entries'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        author = self.request.GET.get('author', False)
        try:
            user = PatchAuthorName.objects.get(display_name=author)
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

    def post(self, request, *args, **kwargs):
        print(request.POST)
        print(request.META.get('REMOTE_ADDR'))

        origin_id = request.META.get('REMOTE_ADDR')
        
        md5 = hashlib.md5()
        md5.update(bytes(origin_id, encoding='ascii'))
        origin_hash = md5.hexdigest()

        is_answer_a = request.POST['answer'][0]=='a'
        question_id = request.POST['question_id'][0]
        entry_a_id = request.POST['entry_a_id'][0]
        entry_b_id = request.POST['entry_b_id'][0]

        #Get all the answers for this pair
        answers = models.BinaryAnswer.objects.filter(
                Q(entryA_id=entry_a_id, entryB_id=entry_b_id)
                )
        """
        There can be equivalent answers under different conditions
        Consider two entries 0 and 1 submitted to a question

        Consider the question "is A > B?"
        There can be two answers where 0 and 1 are compared
        Answer 0 > 1?
            count_a - number of times 0 > 1
            count_b - number of times 1 > 0
        Answer 1 > 0?
            count_a - number of times 1 > 0
            count_b - number of times 0 > 1
        Complete answer:
            count_0>1 = (0>1).count_a + (1>0).count_b
            count_1>0 = (0>1).count_b + (1>0).count_a

        Consider the question is "A = B?"
        Answer 0 = 1?
            count_a = number of times 0 == 1
            count_b = number of times 0 != 1
        Answer 1 = 0?
            count_a = number of times 0 == 1
            count_b = number of times 0 != 1
        Complete answer:
            count 0==1 = (0=1).count_a+(1=0).count_a
            count 0!=1 = (0=1).count_b+(1=0).count_b

        Note that the complete answer is computed differently for these two case.
        These duplicates are allowed to coexist independtently to simply creation.
        The complete answer must be computed on a case by case basic according the
        nature of the question, but only requires the combination of exactly two
        different answers
        """

        #filter to this question
        answers = answers.filter(question_id=question_id)

        if answers.count() == 0:
            #Make a new answer if it doesn't exist
            answer = models.BinaryAnswer(
                entryA_id=entry_a_id, 
                entryB_id=entry_b_id, 
                question_id = question_id)
        else:
            answer = answers[0]

        #Generate the answer detail
        answer_detail = models.BinaryResponseDetail(
                answer=answer, 
                selected_a = is_answer_a,
                origin = origin_hash
                )

        #Update the answer values
        if is_answer_a:
            answer.count_a+=1
        else:
            answer.count_b+=1

        answer.save()
        answer_detail.save()

        print(answer)
        print(answer_detail)

        allresp = models.BinaryResponseDetail.objects.filter(answer=answer)
        print(allresp)


        return HttpResponseRedirect(request.path)


class TagView(generic.ListView):
    model =PatchTag 
    template_name = 'patches/tags.html'
    context_object_name = 'tags'

    def get_queryset(self):
        q = super(TagView, self).get_queryset()

        q = sorted(q.all(), key = lambda x: x.count(), reverse=True)

        return q

    """
    def get_context_data(self, **kwargs):
        context = super(TagView, self).get_context_data(**kwargs)
        context['count'] = {}
        for tag in context['tags']:
            tagname = tag.name
            context['count'][tagname] = PatchEntry.objects.filter(tags__name=tagname).count()

        return context
    """
