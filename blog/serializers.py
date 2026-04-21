from rest_framework import serializers
from django.utils.text import slugify
from .models import Blog, BlogCategory, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"


class BlogCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogCategory
        fields = "__all__"


class BlogSerializer(serializers.ModelSerializer):

    # ✅ Write (IDs)
    category = serializers.PrimaryKeyRelatedField(
        queryset=BlogCategory.objects.all()
    )

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=False
    )

    # ✅ Read (objects)
    category_data = serializers.SerializerMethodField()
    tags_data = serializers.SerializerMethodField()

    # ✅ UI Aliases (so DRF accepts these keys during POST/PUT)
    publish_status = serializers.CharField(write_only=True, required=False)
    short_description = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = Blog
        fields = "__all__"
        read_only_fields = ["slug", "author", "created_at", "updated_at"]

    def get_category_data(self, obj):
        if obj.category:
            return {
                "id": obj.category.id,
                "value": obj.category.name
            }
        return None

    def get_tags_data(self, obj):
        return [
            {"id": tag.id, "value": tag.name}
            for tag in obj.tags.all()
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Provide aliases and display names for frontend compatibility
        data["publish_status"] = data.get("status")
        data["status_display"] = instance.get_status_display()
        data["short_description"] = data.get("excerpt")
        return data

    def to_internal_value(self, data):
        # Create a mutable copy if it's a QueryDict (needed for some frontend payloads)
        if hasattr(data, "_mutable"):
            data = data.copy()

        # Map incoming frontend keys to internal backend field names
        if "publish_status" in data:
            data["status"] = data["publish_status"]
        if "short_description" in data:
            data["excerpt"] = data["short_description"]

        return super().to_internal_value(data)

    def validate(self, data):
        from django.utils import timezone
        status = data.get("status")
        publish_at = data.get("publish_at")

        if status == "scheduled" and not publish_at:
            raise serializers.ValidationError(
                {"publish_at": "Publish date is required for scheduled blogs."}
            )
        
        # If publishing now and no date set, default to now
        if status == "published" and not publish_at:
            data["publish_at"] = timezone.now()
        
        return data

    def create(self, validated_data):
        # Remove UI aliases so they don't get passed to the model
        validated_data.pop("publish_status", None)
        validated_data.pop("short_description", None)

        tags = validated_data.pop("tags", [])
        # Slug is handled by the model's save() method
        blog = Blog.objects.create(**validated_data)
        blog.tags.set(tags)   # ✅ handles multiple tags
        return blog

    def update(self, instance, validated_data):
        # Remove UI aliases so they don't get passed to the model
        validated_data.pop("publish_status", None)
        validated_data.pop("short_description", None)

        tags = validated_data.pop("tags", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if tags is not None:
            instance.tags.set(tags)   # ✅ update multiple tags

        instance.save()
        return instance