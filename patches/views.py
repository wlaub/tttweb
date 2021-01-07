import hashlib
import datetime
import mimetypes

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.views import generic
from django.contrib.syndication.views import Feed

from django.core.exceptions import ObjectDoesNotExist

from django.contrib import messages

from django.urls import reverse
from django.utils.feedgenerator import Enclosure, Rss201rev2Feed

from django.db.models import Q

from tttweb.templatetags import tttcms_tags 
from .models import PatchEntry, PatchAuthorName, BinaryQuestion, PatchTag
from . import models

from .serializers import PatchEntrySerializer,PatchAuthorSerializer
from . import serializers

from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
from rest_framework import viewsets

class IsAuthorOrReadOnly(permissions.IsAuthenticatedOrReadOnly):
    def has_object_permission(self, request, view, obj):
        print(obj.authors.all())
        if request.method in permissions.SAFE_METHODS:
            return True

        result = super(IsAuthorOrReadOnly, self).has_object_permission(request, view, obj)
        if not result: return False

        if len(obj.authors.all()) == 0:
            #The object has no authors
            return True
       
        q = obj.authors.filter(user=request.user)
        if len(q.all()) > 0:
            return True
        
        return False


class PatchEntryAPIVS(viewsets.ModelViewSet):
    queryset = PatchEntry.objects.all()
    serializer_class = PatchEntrySerializer
    permission_classes=[IsAuthorOrReadOnly]

class PatchAuthorAPIVS(viewsets.ReadOnlyModelViewSet):
    queryset = PatchAuthorName.objects.all()
    serializer_class = PatchAuthorSerializer

class PatchImageAPIVS(viewsets.ModelViewSet):
    queryset = models.PatchImages.objects.all()
    serializer_class = serializers.PatchImageSerializer
    permission_classes=[IsAuthorOrReadOnly]

class PatchAttachAPIVS(viewsets.ModelViewSet):
    queryset = models.PatchAttachments.objects.all()
    serializer_class = serializers.PatchAttachSerializer
    permission_classes=[IsAuthorOrReadOnly]

class PatchTagAPIVS(viewsets.ModelViewSet):
    queryset = models.PatchTag.objects.all()
    serializer_class = serializers.PatchTagSerializer
    permission_classes=[IsAuthorOrReadOnly]



def get_index_queryset(request):
    order_map = {
        'date': 'date',
        'length': 'meta__duration'
        }

    order_by = request.GET.get('order_by', 'date')
    order_by = order_map.get(order_by, order_by)
    ascending = request.GET.get('ascending', False)
    if not ascending:
        order_by = f'-{order_by}'

    q = PatchEntry.objects.order_by(order_by)

    author = request.GET.get('author', False)
    if author:
        q = q.filter(authors__display_name=author)
    tags = request.GET.get('tags', False)
    if tags:
        taglist = tags.split(',')
        for tag in taglist:
            q = q.filter(tags__name=tag)

    min_date = request.GET.get('min_date', False)
    max_date = request.GET.get('max_date', False)
    min_length = request.GET.get('length', False)
    max_length = request.GET.get('length', False)


    return q


from django import forms

class FilterForm(forms.Form):
    min_length = forms.DurationField(widget=forms.TimeInput)
    max_length = forms.DurationField()
    min_date = forms.DateField(widget=forms.DateInput)
    max_date = forms.DateField(widget=forms.SelectDateWidget)
    order_by = forms.ChoiceField(choices=[('test','date')])
    ascending = forms.BooleanField()


class IndexView(generic.ListView):
    template_name = 'patches/index.html'
    context_object_name = 'patch_entries'

    paginate_by=10

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

        context['filter_form'] = FilterForm()

#        messages.add_message(self.request, messages.INFO, tttcms_tags.format_querystring(self.request.GET))
        return context

    def get_queryset(self):
        q = get_index_queryset(self.request)
        return q

class MyRSSFeed(Rss201rev2Feed):
    def add_item_elements(self, handler, item):
        handler.startElement(u'content:encoded', {})
        handler.startElement(f'![CDATA[{item["description"]}]]', {})
        handler.endElement(u'content:encoded')
        item['description'] = ''
        super(MyRSSFeed, self).add_item_elements(handler, item)

class IndexFeed(Feed):
    title = 'New Audio Files'
    description = 'New audio files uploaded to the website'
    feed_type = MyRSSFeed

    def get_object(self, request):
        self.request = request
        return request

    def link(self, request):
        url = request.build_absolute_uri(
                reverse('patches:index')+tttcms_tags.format_querystring(request.GET)
                )

        return url

    def item_description(self, item):
        desc =  tttcms_tags.render_markdown(item.desc)
        return desc

    def item_link(self, item):
        url = item.get_absolute_url()
        url = self.request.build_absolute_uri(url)
        return url

    def items(self, obj):
        q = get_index_queryset(obj)
        q  = q[:10]
        return q

    def item_enclosures(self, item):
        mime_type = mimetypes.guess_type(item.recording.path)[0]
        url = self.request.build_absolute_uri(item.recording.url)
        length = str(item.recording.file.size)
        return [Enclosure(url=url, length=length, mime_type=mime_type)]

    def item_author_name(self, item):
        return ', '.join(map(lambda x: x.author.display_name, item.authors.all()))

    def item_pubdate(self, item):
        return item.date

    def item_categories(self,item):
        return list(map(lambda x: x.name, item.tags.all()))


class DetailView(generic.DetailView):
    model = PatchEntry
    template_name = 'patches/detail.html'

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        entry = context['object']

        print('!'*80)
        print(dir(entry.recording))

        #Need all the cases where entry is A
        #Also need all the cases where entry is B and there is no complement
        answers = models.BinaryAnswer.objects.filter(question__slug='similar')
        answers_a = list(answers.filter(entryA=entry))
        answers_b = answers.filter(entryB=entry)
        for b in answers_b:
            for a in answers_a:
                complement = False
                if b.entryA == a.entryB:
                    complement=True
            if not complement:
                answers_a.append(b)

        answers = list(map(lambda x: x.get_merged(entry), answers_a))

        answers = sorted(answers, key=lambda x: x.get_score(), reverse=True)

        answers = answers[:3]

        context['similar'] = answers


        return context

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
        origin_id = request.META.get('REMOTE_ADDR')
        
        md5 = hashlib.md5()
        md5.update(bytes(origin_id, encoding='ascii'))
        origin_hash = md5.hexdigest()

        if request.POST['answer'][0] not in ['a','b']:
            messages.add_message(request, messages.INFO, 
                f'Comparison skipped at {datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M:%S %Z")}')
        else:
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

            try:
                answer.save()
                answer_detail.save()
            except Exception as e:
                messages.add_message(request, messages.ERROR, 
                    'Failed to record comparison response: {e}')
            else:
                messages.add_message(request, messages.SUCCESS, 
                    f'Comparison recorded at {answer_detail.date.strftime("%H:%M:%S %Z")}')

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
