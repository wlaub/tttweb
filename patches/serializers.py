from rest_framework import serializers
from .models import PatchEntry, PatchAuthorName
from . import models
from . import utils
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

class PatchImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PatchImages
        fields = '__all__'

class PatchAttachSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PatchAttachments
        fields = '__all__'

class PatchTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PatchTag
        fields = '__all__'



class PatchEntrySerializer(serializers.ModelSerializer):
    """
    Pass pk's for existing objects. To create new objects, pass to
    corresponding extra_field.
    """
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

    extra_images=serializers.ListField(child=serializers.FileField())

    class Meta:
        model = PatchEntry
        exclude = []

    def validate_extra_images(self, data):
        print('***')
        print(utils.generate_checksum(data[0])) 
        checksums = {utils.generate_checksum(fp):fp for fp in data}
        q = models.PatchImages.objects.filter(checksum__in=checksums.keys())
        if q.count() != 0:
            bad_files = [checksums[x.checksum].name for x in q.all()]
            raise serializers.ValidationError(f'files {bad_files} conflict with existing file checksums')
        return data

    def create(self, validated_data):
        repos = validated_data.pop('repo_attachments')
        entry = super(PatchEntrySerializer, self).create(validated_data)
        for repodata in repos:
            models.PatchRepoAttachment.objects.create(entry=entry, **repodata)
        return entry


