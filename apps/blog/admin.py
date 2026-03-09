"""
Blog Admin Configuration
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import BlogCategory, Tag, Post, Comment


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'post_count', 'order']
    list_filter = ['brand']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['order']
    ordering = ['order', 'name']

    def post_count(self, obj):
        return obj.posts.count()
    post_count.short_description = 'Posts'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'post_count']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}

    def post_count(self, obj):
        return obj.posts.count()
    post_count.short_description = 'Posts'


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ['user', 'name', 'email', 'content', 'created_at']
    fields = ['user', 'name', 'content', 'is_approved', 'created_at']

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'author', 'category', 'brand', 'status_badge',
        'is_featured', 'views', 'published_at'
    ]
    list_filter = ['status', 'brand', 'category', 'is_featured', 'published_at']
    search_fields = ['title', 'content', 'excerpt']
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ['author']
    filter_horizontal = ['tags']
    list_editable = ['is_featured']
    date_hierarchy = 'published_at'
    readonly_fields = ['views', 'created_at', 'updated_at']
    inlines = [CommentInline]

    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'author', 'category', 'tags', 'brand')
        }),
        ('Content', {
            'fields': ('excerpt', 'content', 'featured_image')
        }),
        ('Publishing', {
            'fields': ('status', 'is_featured', 'published_at')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Stats', {
            'fields': ('views',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        colors = {
            'draft': '#f59e0b',
            'published': '#22c55e',
            'archived': '#6b7280',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    actions = ['publish_posts', 'draft_posts', 'archive_posts']

    @admin.action(description='Publish selected posts')
    def publish_posts(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='published', published_at=timezone.now())
        self.message_user(request, f'{queryset.count()} posts published.')

    @admin.action(description='Mark as Draft')
    def draft_posts(self, request, queryset):
        queryset.update(status='draft')
        self.message_user(request, f'{queryset.count()} posts marked as draft.')

    @admin.action(description='Archive selected posts')
    def archive_posts(self, request, queryset):
        queryset.update(status='archived')
        self.message_user(request, f'{queryset.count()} posts archived.')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['post', 'commenter', 'content_preview', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'created_at']
    search_fields = ['content', 'name', 'email', 'user__email']
    raw_id_fields = ['post', 'user', 'parent']
    list_editable = ['is_approved']
    readonly_fields = ['created_at']

    def commenter(self, obj):
        if obj.user:
            return obj.user.full_name
        return obj.name or obj.email
    commenter.short_description = 'By'

    def content_preview(self, obj):
        if len(obj.content) > 50:
            return f'{obj.content[:50]}...'
        return obj.content
    content_preview.short_description = 'Comment'

    actions = ['approve_comments', 'reject_comments']

    @admin.action(description='Approve selected comments')
    def approve_comments(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, f'{queryset.count()} comments approved.')

    @admin.action(description='Reject selected comments')
    def reject_comments(self, request, queryset):
        queryset.update(is_approved=False)
        self.message_user(request, f'{queryset.count()} comments rejected.')
