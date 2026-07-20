# Django Imports
from django.contrib import admin

# HTK Imports
from htk.apps.feedback.models import Feedback
from htk.apps.feedback.models import FeedbackBoard
from htk.apps.feedback.models import FeedbackCategory
from htk.apps.feedback.models import FeedbackEvidence
from htk.apps.feedback.models import FeedbackRequest
from htk.apps.feedback.models import FeedbackRequestAttachment
from htk.apps.feedback.models import FeedbackRequestComment
from htk.apps.feedback.models import FeedbackRequestEvent
from htk.apps.feedback.models import FeedbackRequestStatusUpdate
from htk.apps.feedback.models import FeedbackRequestSubscription
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
        'processed',
        'needs_followup',
    )

    list_editable = (
        'processed',
        'needs_followup',
    )

    list_filter = (
        'site',
        'created_on',
        'processed',
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
                'processed',
                'needs_followup',
            ]
        }),
    ]

    date_hierarchy = 'created_on'


class FeedbackCategoryInline(admin.TabularInline):
    model = FeedbackCategory
    extra = 0
    fields = (
        'name',
        'slug',
        'is_active',
        'sort_order',
        'auto_assign_owner',
    )


class FeedbackBoardAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'site',
        'name',
        'slug',
        'visibility',
        'is_open',
        'allow_public_voting',
        'allow_public_comments',
        'updated_on',
    )
    list_filter = (
        'site',
        'visibility',
        'is_open',
        'allow_public_voting',
        'allow_public_comments',
    )
    search_fields = (
        'name',
        'slug',
        'description',
    )
    prepopulated_fields = {
        'slug': ('name',),
    }
    inlines = [FeedbackCategoryInline]


class FeedbackCategoryAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'board',
        'name',
        'slug',
        'is_active',
        'sort_order',
        'auto_assign_owner',
    )
    list_filter = (
        'board__site',
        'board',
        'is_active',
    )
    search_fields = (
        'name',
        'slug',
        'description',
    )
    prepopulated_fields = {
        'slug': ('name',),
    }


class FeedbackRequestAttachmentInline(admin.TabularInline):
    model = FeedbackRequestAttachment
    extra = 0
    readonly_fields = (
        'created_on',
        'size_bytes',
        'content_type',
    )


class FeedbackRequestStatusUpdateInline(admin.TabularInline):
    model = FeedbackRequestStatusUpdate
    extra = 0
    readonly_fields = (
        'created_on',
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
        'board',
        'request_type',
        'status',
        'internal_status',
        'visibility',
        'owner',
        'votes_count',
        'supporters_count',
        'comments_count',
        'needs_review',
        'is_hidden',
        'is_spam',
        'processed',
    )
    list_editable = (
        'status',
        'internal_status',
        'visibility',
        'owner',
        'needs_review',
        'is_hidden',
        'is_spam',
        'processed',
    )
    list_filter = (
        'site',
        'board',
        'category',
        'request_type',
        'status',
        'visibility',
        'created_by',
        'owner',
        'needs_review',
        'is_hidden',
        'is_spam',
        'processed',
        'created_on',
    )
    search_fields = (
        'title',
        'description',
        'name',
        'email',
        'created_by__username',
        'created_by__email',
        'source_uri',
    )
    raw_id_fields = (
        'created_by',
        'owner',
    )
    readonly_fields = (
        'votes_count',
        'supporters_count',
        'comments_count',
        'created_on',
        'updated_on',
    )
    date_hierarchy = 'created_on'
    inlines = [
        FeedbackRequestStatusUpdateInline,
        FeedbackRequestCommentInline,
        FeedbackRequestAttachmentInline,
    ]

    actions = (
        'mark_needs_review',
        'mark_processed',
        'hide_requests',
    )

    def mark_needs_review(self, request, queryset):
        queryset.update(needs_review=True)

    def mark_processed(self, request, queryset):
        queryset.update(processed=True, needs_followup=False)

    def hide_requests(self, request, queryset):
        queryset.update(is_hidden=True)


class FeedbackRequestVoteAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'request',
        'user',
        'username',
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
        'username',
        'name',
        'user__username',
    )


class FeedbackRequestSubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'request',
        'user',
        'username',
        'email',
        'source',
        'is_active',
        'notify_status_updates',
        'notify_comments',
        'created_on',
    )
    list_filter = (
        'is_active',
        'notify_status_updates',
        'notify_comments',
        'source',
        'created_on',
    )
    search_fields = (
        'request__title',
        'email',
        'username',
        'name',
        'user__username',
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


class FeedbackEvidenceAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'site',
        'request',
        'source',
        'user',
        'email',
        'source_uri',
        'is_internal',
        'created_on',
    )
    list_filter = (
        'site',
        'source',
        'is_internal',
        'created_on',
    )
    search_fields = (
        'request__title',
        'body',
        'email',
        'username',
        'name',
        'source_uri',
    )


class FeedbackRequestStatusUpdateAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'request',
        'status',
        'is_public',
        'notify_supporters',
        'created_by',
        'created_on',
    )
    list_filter = (
        'status',
        'is_public',
        'notify_supporters',
        'created_on',
    )
    search_fields = (
        'request__title',
        'message',
    )


class FeedbackRequestAttachmentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'request',
        'comment',
        'original_filename',
        'content_type',
        'size_bytes',
        'is_screenshot',
        'created_on',
    )
    list_filter = (
        'content_type',
        'is_screenshot',
        'created_on',
    )
    search_fields = (
        'request__title',
        'original_filename',
    )


class FeedbackRequestEventAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'request',
        'event_type',
        'actor',
        'created_on',
    )
    list_filter = (
        'event_type',
        'created_on',
    )
    search_fields = (
        'request__title',
        'message',
    )
    readonly_fields = (
        'created_on',
    )


admin.site.register(Feedback, FeedbackAdmin)
admin.site.register(FeedbackBoard, FeedbackBoardAdmin)
admin.site.register(FeedbackCategory, FeedbackCategoryAdmin)
admin.site.register(FeedbackRequest, FeedbackRequestAdmin)
admin.site.register(FeedbackRequestVote, FeedbackRequestVoteAdmin)
admin.site.register(FeedbackRequestSubscription, FeedbackRequestSubscriptionAdmin)
admin.site.register(FeedbackRequestComment, FeedbackRequestCommentAdmin)
admin.site.register(FeedbackRequestAttachment, FeedbackRequestAttachmentAdmin)
admin.site.register(FeedbackEvidence, FeedbackEvidenceAdmin)
admin.site.register(FeedbackRequestStatusUpdate, FeedbackRequestStatusUpdateAdmin)
admin.site.register(FeedbackRequestEvent, FeedbackRequestEventAdmin)
