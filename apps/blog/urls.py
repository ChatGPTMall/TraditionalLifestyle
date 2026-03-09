"""
Blog URL Configuration
"""

from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.PostListView.as_view(), name='posts'),
    path('post/<slug:slug>/', views.PostDetailView.as_view(), name='post_detail'),
    path('category/<slug:slug>/', views.CategoryPostsView.as_view(), name='category'),
    path('tag/<slug:slug>/', views.TagPostsView.as_view(), name='tag'),
]
