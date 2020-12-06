from django.db import models

from django.contrib.auth.models import User

# Create your models here.


class PatchEntry(models.Model):
    name = models.TextField()
    recording = models.FileField('recordings/')
    date = models.DateTimeField()
    desc = models.TextField()

    def __str__(self):
        return f'Patch Recording - {self.name}'

class PatchAttachments(models.Model):
    """
    Generic files attached to an entry, 0 or more
    """
    entry = models.ForeignKey(PatchEntry, on_delete=models.CASCADE, related_name = 'attachments')
    file = models.FileField('attachements/')

class PatchImages(models.Model):
    """
    Images attached to an entry, 1 or more
    """
    entry = models.ForeignKey(PatchEntry, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField('images/')

class PatchTag(models.Model):
    """
    Tags associated with an entry, 0 or more
    """
    entry = models.ForeignKey(PatchEntry, on_delete=models.CASCADE, related_name='tags')
    name = models.TextField()

class PatchAuthorName(models.Model):
    display_name = models.TextField()
    user = models.ForeignKey(User, on_delete = models.CASCADE, related_name='display_name')

    def __str__(self):
        return f'{self.display_name} AKA {self.user.username}'


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

