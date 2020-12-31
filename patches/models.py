from django.db import models
import os
import hashlib

from django.contrib.auth.models import User

from django.core.files.storage import FileSystemStorage

# Create your models here.

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

def generate_checksum(fp):
    md5 = hashlib.md5()
    for chunk in fp.chunks():
        md5.update(chunk)
    return md5.hexdigest()



class PatchTag(models.Model):
    """
    Tags associated with an entry, 0 or more
    """
#    entry = models.ForeignKey(PatchEntry, on_delete=models.CASCADE, related_name='tags')
    name = models.TextField()
    description = models.TextField()

    def summary(self):
        return self.description.split('\n')[0]

    def __str__(self):
        return self.name

def unique_file_name(instance, filename):
    checksum = instance.checksum
    basename, ext = os.path.splitext(filename)
    return os.path.join('patches/images', f'{basename}_{checksum}{ext}')

class PatchImages(models.Model):
    """
    Images attached to an entry, 1 or more
    """
#    entry = models.ForeignKey(PatchEntry, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=unique_file_name, storage=UniqueFileStorage)
    checksum = models.CharField(max_length=36, unique=True, null=True)

    def save(self, *args, **kwargs):
#        if not self.pk:
        self.checksum = generate_checksum(self.image.file)
        super(PatchImages, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.image)

    def __html__(self):
        return "test"


class PatchEntry(models.Model):
    name = models.TextField()
    recording = models.FileField(upload_to='patches/recordings/')
    date = models.DateTimeField()
    desc = models.TextField(null=True)
    tags = models.ManyToManyField(PatchTag, blank=True)
    images = models.ManyToManyField(PatchImages, blank=True)

    def __str__(self):
        return f'Patch Recording - {self.name}'

class PatchAttachments(models.Model):
    """
    Generic files attached to an entry, 0 or more
    """
    entry = models.ForeignKey(PatchEntry, on_delete=models.CASCADE, related_name = 'attachments')
    file = models.FileField(upload_to='patches/attachements/')
    def filename(self):
        return os.path.basename(self.file.name)

class PatchAuthorName(models.Model):
    display_name = models.TextField()
    author_image = models.ImageField(null=True)
    user = models.ForeignKey(User, on_delete = models.CASCADE, related_name='display_name')

    def __str__(self):
        return f'{self.display_name} AKA {self.user.username}'

class AuthorLink(models.Model):
    author = models.ForeignKey(PatchAuthorName, on_delete=models.CASCADE, related_name = 'links')
    url = models.URLField()

class PatchAuthor(models.Model):
    """
    Authors associated with an entry, 1 or more
    """
    entry = models.ForeignKey(PatchEntry, on_delete=models.CASCADE, related_name='authors')
    author= models.ForeignKey(PatchAuthorName, on_delete = models.CASCADE)

class PatchRepoAttachment(models.Model):
    """
    A file in a repository at a specific commit, 0 or more
    """
    entry = models.ForeignKey(PatchEntry, on_delete=models.CASCADE, related_name='repo_attachments')
    repo = models.URLField()
    commit = models.TextField()
    filename = models.TextField()

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

    def get_options(self):
        #TODO: if/else on question text to hardcode custom filters
        #TODO: query patch entries to select two
        pass

    def __str__(self):
        return str(question)

class BinaryAnswer(models.Model):
    """
    An answer for a comparison of two entries.
    count_a/count_b are the number of times the respective answers were given
    For example given the question Is entry_a better than entry_b? then count_a
    gives the number of yes responses and count_b gives the number of no responses.

    Have to be careful about the possibility of duplicate cases where A/B are
    the same but reversed. Possible that's fine and those should just be
    combined in post.
    """
    entryA = models.ForeignKey(PatchEntry, on_delete=models.PROTECT, related_name='a_comparisons')
    entryB = models.ForeignKey(PatchEntry, on_delete=models.PROTECT, related_name='b_comparisons')
    question = models.ForeignKey(BinaryQuestion, on_delete=models.PROTECT, related_name="results")
    count_a = models.IntegerField(default=0)
    count_b = models.IntegerField(default=0)




