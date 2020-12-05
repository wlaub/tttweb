from django.db import models

# Create your models here.


class PatchEntry(models.Model):
        name = models.TextField()
        #recording = models.FileField('recordings/')
        date = models.DateTimeField()
        desc = models.TextField()



