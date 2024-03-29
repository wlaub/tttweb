from django.db import models
import os
import hashlib
import random
import datetime

from django.urls import reverse

from django.contrib.auth.models import User

from django.core.files.storage import FileSystemStorage

from easy_thumbnails.fields import ThumbnailerImageField

from licensing.models import Licensed

from .utils import generate_checksum

# Create your models here.

class CaseTextField(models.CharField):
    """
    case-insensitive text field
    """

    lookup_map = {
        'exact': 'iexact',
        'contains': 'icontains',
        'startswith': 'istartswith',
        'endswith': 'iendswith',
        'regex': 'iregex',
        }

    def get_lookup(self, name):
        result = self.lookup_map.get(name, name)
        return super().get_lookup(result)


class PatchAuthorName(models.Model):
    display_name = models.CharField(max_length = 512, unique=True)
    author_image = models.ImageField(null=True)
    bio = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete = models.CASCADE, related_name='display_name')

    def __str__(self):
        return f'{self.display_name} AKA {self.user.username}'

class AuthorLink(models.Model):
    author = models.ForeignKey(PatchAuthorName, on_delete=models.CASCADE, related_name = 'links')
    url = models.URLField()


class PatchTag(models.Model):
    """
    Tags associated with an entry, 0 or more
    """
#    entry = models.ForeignKey(PatchEntry, on_delete=models.CASCADE, related_name='tags')
    name = CaseTextField(max_length = 512, unique=True)
    description = models.TextField()

    def summary(self):
        return self.description.split('\n')[0]

    def count(self):
        """
        Return the number of PatchEntries having this tag
        """
        return PatchEntry.objects.filter(tags__name=self.name).count()

    def __str__(self):
        return self.name

import audio_metadata as audiometa

class AudioMetadata(models.Model):

    duration = models.DurationField()

    @classmethod
    def create(cls, recording):
        result = cls()
        result.refresh(recording)
        return result

    def refresh(self, recording, loud=False):
        metadata = audiometa.load(recording.path)
        self.duration = datetime.timedelta(seconds=metadata['streaminfo']['duration'])
        if loud:
            print(f'New duration: {self.duration}')


    def __str__(self):
        return f'Duration: {self.duration}'

class UniqueFileStorage(FileSystemStorage):
    def get_available_name(self, name, max_length=None):
        if max_length and len(name) > max_length:
            raise(Exception("name's length is greater than max_length"))
        return name

    def _save(self, name, content):
        if self.exists(name):
            # if the file exists, do not call the superclasses _save method
            return name
        # if the file is new, DO call it
        return super(UniqueFileStorage, self)._save(name, content)


def unique_file_name(instance, filename):
    checksum = instance.checksum
    basename, ext = os.path.splitext(filename)
    return os.path.join(instance.unique_filepath, f'{basename}_{checksum}{ext}')


class PatchImages(models.Model):
    """
    Images attached to an entry, 1 or more
    """
#    entry = models.ForeignKey(PatchEntry, on_delete=models.CASCADE, related_name='images')
#    image = models.ImageField(upload_to=unique_file_name, storage=UniqueFileStorage)
    image = ThumbnailerImageField(upload_to=unique_file_name, storage=UniqueFileStorage)
    checksum = models.CharField(max_length=36, unique=True, null=True)
   
    unique_filepath = 'patches/images'

    def save(self, *args, **kwargs):
        self.checksum = generate_checksum(self.image.file)
        super(PatchImages, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.image)

    def __html__(self):
        return "test"

class PatchAttachments(models.Model):
    """
    Generic files attached to an entry, 0 or more
    """
    file = models.FileField(upload_to=unique_file_name, storage=UniqueFileStorage)
    checksum = models.CharField(max_length=36, unique=True, null=True)

    unique_filepath = 'patches/attachements/'

    def save(self, *args, **kwargs):
        self.checksum = generate_checksum(self.file)
        super(PatchAttachments, self).save(*args, **kwargs)

    def filename(self):
        return os.path.basename(self.file.name)


class PatchEntry(Licensed):
    name = models.TextField()
    recording = models.FileField(upload_to='patches/recordings/')
    meta = models.ForeignKey(AudioMetadata, null=True, on_delete=models.CASCADE, related_name='source')
    date = models.DateTimeField()
    desc = models.TextField(null=True, blank=True)
    tags = models.ManyToManyField(PatchTag, blank=True)
    images = models.ManyToManyField(PatchImages, blank=True)
    authors = models.ManyToManyField(PatchAuthorName)
    attachments = models.ManyToManyField(PatchAttachments, blank=True)

    def __str__(self):
        try:
            return f'Audio File - {self.meta.duration} - {self.name}'
        except Exception as e:
            return f'Error rendering entry name: {e}'

    @classmethod
    def refresh_metadata(cls):
        q = cls.objects.all()
        for entry in q:
            entry.meta.refresh(entry.recording, loud=True)
            entry.meta.save()

    def save(self, *args, **kwargs):
        super(PatchEntry, self).save(*args, **kwargs)
        #This comes after so that the file exists
        if self.meta == None:
            self.meta = AudioMetadata.create(self.recording)
            self.meta.save()
            super(PatchEntry, self).save()

    def get_absolute_url(self):
        return reverse('patches:detail', kwargs={'pk': self.id})



class PatchRepoAttachment(models.Model):
    """
    A file in a repository at a specific commit, 0 or more
    """
    entry = models.ForeignKey(PatchEntry, on_delete=models.CASCADE, related_name='repo_attachments')
    repo = models.TextField()
    commit = models.TextField()
    filename = models.TextField()

    def get_file_tag(self):
        fmt = f'<a href = "{{}}">{self.filename}</a>'
        if 'github.com' in self.repo:
            _, name = self.repo.split('github.com')
            name = name.replace('.git','')
            name = name.strip(':/')
            link = f'https://github.com/{name}/blob/{self.commit}/{self.filename}'
            return fmt.format(link)

        return self.filename

##
## Comparison Models
##

class BinaryQuestion(models.Model):
    """
    A question with two possible answers.
    E.g. 
    question                          answer_a   answer_b
    Is entry_a similar to entry_b?    yes      / no
    Is entry_a better than entry_b?   yes      / no

    There needs to be a way of imposing constraints on the way entries
    can be selected per-question.
    """
    question = models.TextField()
    answer_a = models.TextField()
    answer_b = models.TextField()

    slug = models.SlugField(null = True)

    selection_method = models.IntegerField(default=0)

    #Map slugs to methods for merging complementary pairs of answers
    merge_methods = {
        'symmetric': ['similar',],
        'reversed' : ['better',],
        }

    def get_options(self):
        #TODO: if/else on question text to hardcode custom filters
        #TODO: query patch entries to select two
        if self.selection_method == 0: #any two at random
            entries = PatchEntry.objects.all()
            if entries.count() < 2: return None

            return random.sample(list(entries), k=2)
        else:
            return None

    def __str__(self):
        return str(self.question)

class BinaryAnswer(models.Model):
    """
    An answer for a comparison of two entries.
    For any given pair of options there can be two answers to a question
    depending on the ordering of the options. These two answers are said to
    be complementary, and may be merged in different ways depending on the kind
    of question.

    """
    entryA = models.ForeignKey(PatchEntry, on_delete=models.PROTECT, related_name='a_comparisons')
    entryB = models.ForeignKey(PatchEntry, on_delete=models.PROTECT, related_name='b_comparisons')
    question = models.ForeignKey(BinaryQuestion, on_delete=models.PROTECT, related_name="results")
    count_a = models.IntegerField(default=0)
    count_b = models.IntegerField(default=0)

    def align(self, entry):
        """
        Align self to the given entry so that it corresponds to entryA
        This uses the merge_method to determine whether or not to reverse
        the counts as well
        """
        result = {
            'entryA': self.entryA,
            'entryB': self.entryB,
            'question': self.question,
            'count_a': self.count_a,
            'count_b': self.count_b,
            }

        if self.entryA == entry:
            result = BinaryAnswer(**result) 
            return result

        slug = self.question.slug
        if self.entryB == entry:
            result['entryB'] = self.entryA
            result['entryA'] = self.entryB
            if slug in BinaryQuestion.merge_methods['reversed']:
                result['count_b'] = self.count_a
                result['count_a'] = self.count_b
            result = BinaryAnswer(**result)
            return result

        raise KeyError(f'Entry {entry} not in answer {self}')

    def get_merged(self, align_entry = None):
        """
        If align_entry is given, align that to entryA
        Return a dictionary of this answer merged with is complement if it exists
        {
        entryA, entryB, question, count_a, count_b
        }
        """
        slug = self.question.slug
        other = BinaryAnswer.objects.filter(entryA=self.entryB, entryB=self.entryA, question=self.question)
        if align_entry:
            result=self.align(align_entry)
        else:
            result = {
                'entryA': self.entryA,
                'entryB': self.entryB,
                'question': self.question,
                'count_a': self.count_a,
                'count_b': self.count_b,
                }
            result = BinaryAnswer(**result)

        if other.count() == 0:
            return result
        else:
            other=other[0].align(result.entryA)
            result.count_a += other.count_a
            result.count_b += other.count_b
            return result

    def get_score(self):
        """
        May change to be more statistical later but basically give a number
        tellling how much the answer is answer_a
        """
        return self.count_a/(self.count_a+self.count_b)

    def __str__(self):
        return f"""Binary Answer:
  {self.entryA}
  {self.question} {self.question.answer_a} = {self.count_a} / {self.question.answer_b} = {self.count_b}
  {self.entryB}"""

class BinaryResponseDetail(models.Model):
    """
    Details about a specific response i.e. date/time, a or b, origin
    Should be able to reconstruct a BinaryAnswer over time
    """
    answer = models.ForeignKey(BinaryAnswer, on_delete=models.PROTECT, related_name='responses')
    selected_a = models.BooleanField()
    date = models.DateTimeField(auto_now_add=True)
    origin = models.TextField() #This should be some kind of hash uniquely identifying an origin

    def __str__(self):
        return f"""{self.answer}
    {self.answer.question.answer_a if self.selected_a else self.answer.question.answer_b} At: {self.date}
    From: {self.origin}"""

