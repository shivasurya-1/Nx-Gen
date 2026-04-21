from django.urls import path
from .views import (
    AdminBlogListCreateView,
    AdminBlogDetailView,
    AdminBlogMetaView,
    AdminBlogCategoryListCreateView,
    PublicBlogListView,
    PublicBlogDetailView,
    latest_blogs
)

urlpatterns = [

    # path('admin/login/', BlogAdminLoginView.as_view()),
    # Admin APIs
    path('admin/blogs/', AdminBlogListCreateView.as_view()),
    path('admin/meta/', AdminBlogMetaView.as_view()),
    path('admin/categories/', AdminBlogCategoryListCreateView.as_view()),
    path('admin/blogs/<int:id>/', AdminBlogDetailView.as_view()),
    path('admin/blogs/<int:id>/edit/', AdminBlogDetailView.as_view()),


    # Public APIs
    path('', PublicBlogListView.as_view()),
    path('latest-blogs/', latest_blogs, name='latest_blogs'),
    path('<slug:slug>/', PublicBlogDetailView.as_view()),
]