# Django Imports
from django.contrib import admin

# HTK Imports
from htk.apps.feedback.models import Feedback
from htk.apps.feedback.models import FeedbackRequest
from htk.apps.feedback.models import FeedbackRequestAttachment
from htk.apps.feedback.models import FeedbackRequestComment
from htk.apps.feedback.models import FeedbackRequestVote


class FeedbackAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'site',
        'created_on',
        'user',
        'name',
        'email',
        'comment',
        'uri',
        'needs_followup',
    )

    list_editable = (
        'needs_followup',
    )

    list_filter = (
        'site',
        'created_on',
        'needs_followup',
    )

    search_fields = (
        'name',
        'email',
        'comment',
        'uri',
    )

    readonly_fields = (
        'created_on',
        'site',
        'uri',
        'name',
        'email',
        'comment',
    )

    fieldsets = [
        ('Date Information', {
            'fields': [
                'created_on',
            ],
        }),
        ('Page Viewing', {
            'fields': [
                'site',
                'uri',
            ]
        }),
        ('Submitted Feedback', {
            'fields': [
                'name',
                'email',
                'comment',
            ]
        }),
        ('Admin', {
            'fields' : [
                        'needs_followup',
            ]
        }),
    ]

    date_hierarchy = 'created_on'


class FeedbackRequestAttachmentInline(admin.TabularInline):
    model = FeedbackRequestAttachment
    extra = 0
    readonly_fields = (
        'created_on',
        'size_bytes',
        'content_type',
    )


class FeedbackRequestCommentInline(admin.TabularInline):
    model = FeedbackRequestComment
    extra = 0
    readonly_fields = (
        'created_on',
        'updated_on',
    )


class FeedbackRequestAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'created_by',
        'created_on',
        'site',
        'request_type',
        'status',
        'visibility',
        'owner',
        'votes_count',
        'comments_count',
        'needs_review',
        'is_hidden',
        'is_spam',
    )
    list_editable = (
        'status',
        'visibility',
        'owner',
        'needs_review',
        'is_hidden',
        'is_spam',
    )
    list_filter = (
        'site',
        'request_type',
        'status',
        'visibility',
        'created_by',
        'owner',
        'needs_review',
        'is_hidden',
        'is_spam',
        'created_on',
    )
    search_fields = (
        'title',
        'description',
        'name',
        'email',
        'created_by__email',
        'source_uri',
    )
    raw_id_fields = (
        'created_by',
        'owner',
    )
    readonly_fields = (
        'votes_count',
        'comments_count',
        'created_on',
        'updated_on',
    )
    date_hierarchy = 'created_on'
    inlines = [
        FeedbackRequestCommentInline,
        FeedbackRequestAttachmentInline,
    ]

    actions = (
        'mark_needs_review',
        'hide_requests',
    )

    def mark_needs_review(self, request, queryset):
        queryset.update(needs_review=True)

    def hide_requests(self, request, queryset):
        queryset.update(is_hidden=True)


class FeedbackRequestVoteAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'request',
        'user',
        'email',
        'importance',
        'is_active',
        'is_spam',
        'created_on',
    )
    list_filter = (
        'is_active',
        'is_spam',
        'importance',
        'created_on',
    )
    search_fields = (
        'request__title',
        'email',
        'name',
    )


class FeedbackRequestCommentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'request',
        'user',
        'name',
        'email',
        'is_internal',
        'is_hidden',
        'is_spam',
        'created_on',
    )
    list_filter = (
        'is_internal',
        'is_hidden',
        'is_spam',
        'created_on',
    )
    search_fields = (
        'request__title',
        'comment',
        'email',
        'name',
    )


admin.site.register(Feedback, FeedbackAdmin)
admin.site.register(FeedbackRequest, FeedbackRequestAdmin)
admin.site.register(FeedbackRequestVote, FeedbackRequestVoteAdmin)
admin.site.register(FeedbackRequestComment, FeedbackRequestCommentAdmin)
