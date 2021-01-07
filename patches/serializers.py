from rest_framework import serializers
from .models import PatchEntry, PatchAuthorName
from . import models
import json

class JsonListSer(serializers. ListSerializer):
    """
    For consuming json-encoded lists
    """
    def get_value(self, data):
        result =  data.get(self.field_name, '[]')
        result = json.loads(result)
        return result



class PatchAuthorSerializer(serializers.ModelSerializer):

    class Meta:
        model = PatchAuthorName
        fields = ['display_name']

class RepoAttachSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PatchRepoAttachment
        list_serializer_class = JsonListSer
        exclude=['entry']

class PatchEntrySerializer(serializers.ModelSerializer):
    authors = serializers.SlugRelatedField(
        many=True, 
        slug_field='display_name',
        read_only=False,
        queryset=PatchAuthorName.objects.all()
        )

    tags = serializers.SlugRelatedField(
        many=True, 
        slug_field='name',
        read_only=False,
        queryset=models.PatchTag.objects.all()
        )

    repo_attachments = RepoAttachSerializer(many=True, read_only=False)

    class Meta:
        model = PatchEntry
        exclude = []

    def create(self, validated_data):
        repos = validated_data.pop('repo_attachments')
        entry = super(PatchEntrySerializer, self).create(validated_data)
        for repodata in repos:
            models.PatchRepoAttachment.objects.create(entry=entry, **repodata)
        return entry


