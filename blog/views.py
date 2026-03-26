from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from rest_framework import status
from django.db.models import Q
from django.shortcuts import get_object_or_404

from .models import Blog
from .serializers import BlogSerializer
from .permissions import IsAdminOnly


class BlogPagination(PageNumberPagination):
    page_size = 5


# ---------------- ADMIN BLOG CRUD ---------------- #

class AdminBlogListCreateView(APIView):
    permission_classes = [IsAdminOnly, IsAuthenticated]

    def get(self, request):
        search = request.GET.get("search")
        status_filter = request.GET.get("status")

        blogs = Blog.objects.filter(is_deleted=False).order_by("-created_at")

        if search:
            blogs = blogs.filter(
                Q(title__icontains=search) |
                Q(content__icontains=search)
            )

        if status_filter:
            blogs = blogs.filter(status=status_filter)

        paginator = BlogPagination()
        result_page = paginator.paginate_queryset(blogs, request)
        serializer = BlogSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = BlogSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminBlogDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOnly]

    def get(self, request, id):
        blog = get_object_or_404(Blog, id=id, is_deleted=False)
        serializer = BlogSerializer(blog)
        return Response(serializer.data)

    def put(self, request, id):
        blog = get_object_or_404(Blog, id=id, is_deleted=False)
        serializer = BlogSerializer(blog, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        blog = get_object_or_404(Blog, id=id)
        blog.is_deleted = True
        blog.save()
        return Response({"message": "Blog soft deleted"}, status=status.HTTP_200_OK)


# ---------------- PUBLIC APIs ---------------- #

class PublicBlogListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        blogs = Blog.objects.filter(
            status="published",
            is_deleted=False
        ).order_by("-created_at")

        serializer = BlogSerializer(blogs, many=True)
        return Response(serializer.data)


class PublicBlogDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        blog = get_object_or_404(
            Blog,
            slug=slug,
            status="published",
            is_deleted=False
        )

        serializer = BlogSerializer(blog)
        return Response(serializer.data)