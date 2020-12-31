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


