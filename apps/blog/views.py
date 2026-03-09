"""
Blog Views
Posts, Categories, and Tags
"""

from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.db.models import Q

from .models import Post, BlogCategory, Tag


class BrandFilterMixin:
    """Filter querysets by current brand."""

    def get_brand(self):
        return getattr(self.request, 'brand', 'men')


class PostListView(BrandFilterMixin, ListView):
    """List all published blog posts."""
    model = Post
    context_object_name = 'posts'
    paginate_by = 9

    def get_queryset(self):
        brand = self.get_brand()
        return Post.objects.filter(
            Q(brand=brand) | Q(brand='both'),
            status='published'
        ).select_related('category', 'author')

    def get_template_names(self):
        brand = self.get_brand()
        return [f'{brand}/blog/posts.html', 'common/blog/posts.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        brand = self.get_brand()
        context['categories'] = BlogCategory.objects.filter(
            Q(brand=brand) | Q(brand='both')
        )
        context['featured_posts'] = Post.objects.filter(
            Q(brand=brand) | Q(brand='both'),
            status='published',
            is_featured=True
        )[:3]
        context['popular_tags'] = Tag.objects.all()[:10]
        return context


class PostDetailView(BrandFilterMixin, DetailView):
    """Blog post detail page."""
    model = Post
    context_object_name = 'post'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        brand = self.get_brand()
        return Post.objects.filter(
            Q(brand=brand) | Q(brand='both'),
            status='published'
        )

    def get_template_names(self):
        brand = self.get_brand()
        return [f'{brand}/blog/post_detail.html', 'common/blog/post_detail.html']

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # Increment view count
        obj.views += 1
        obj.save(update_fields=['views'])
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        brand = self.get_brand()
        context['related_posts'] = Post.objects.filter(
            Q(brand=brand) | Q(brand='both'),
            status='published',
            category=self.object.category
        ).exclude(pk=self.object.pk)[:3]
        context['comments'] = self.object.comments.filter(is_approved=True, parent=None)
        return context


class CategoryPostsView(BrandFilterMixin, ListView):
    """List posts in a category."""
    model = Post
    context_object_name = 'posts'
    paginate_by = 9

    def get_queryset(self):
        brand = self.get_brand()
        category_slug = self.kwargs.get('slug')
        return Post.objects.filter(
            Q(brand=brand) | Q(brand='both'),
            status='published',
            category__slug=category_slug
        )

    def get_template_names(self):
        brand = self.get_brand()
        return [f'{brand}/blog/category.html', 'common/blog/category.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = get_object_or_404(BlogCategory, slug=self.kwargs.get('slug'))
        return context


class TagPostsView(BrandFilterMixin, ListView):
    """List posts with a specific tag."""
    model = Post
    context_object_name = 'posts'
    paginate_by = 9

    def get_queryset(self):
        brand = self.get_brand()
        tag_slug = self.kwargs.get('slug')
        return Post.objects.filter(
            Q(brand=brand) | Q(brand='both'),
            status='published',
            tags__slug=tag_slug
        )

    def get_template_names(self):
        brand = self.get_brand()
        return [f'{brand}/blog/tag.html', 'common/blog/tag.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tag'] = get_object_or_404(Tag, slug=self.kwargs.get('slug'))
        return context
