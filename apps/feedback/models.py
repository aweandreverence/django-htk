# Django Imports
from django.conf import settings
from django.contrib.sites.models import Site
from django.db import models
from django.db.models import Q

# HTK Imports
from htk.apps.feedback.constants import *
from htk.models import HtkBaseModel


class Feedback(HtkBaseModel):
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='feedback', null=True, blank=True, default=None, on_delete=models.SET_DEFAULT)
    name = models.CharField(max_length=100, null=True, blank=True)
    comment = models.CharField(max_length=2000, null=True, blank=True)
    email = models.EmailField(max_length=100, null=True, blank=True)
    uri = models.CharField(max_length=200, null=True, blank=True)
    # admin
    processed = models.BooleanField(default=False)
    needs_followup = models.BooleanField(default=True)
    # read-only
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'htk'
        verbose_name = 'Feedback'
        verbose_name_plural = 'Feedback'

    def __str__(self):
        s = '%s, %s, [%s]' % (
            self.created_on.strftime('%Y-%m-%d %H:%M:%S'),
            self.uri,
            self.comment[:50] + '...' if self.comment and len(self.comment) > 50 else self.comment
        )
        return s


class FeedbackRequest(HtkBaseModel):
    """A public/semi-public idea, feature request, bug, or feedback item."""

    site = models.ForeignKey(Site, related_name='feedback_requests', on_delete=models.CASCADE)
    request_type = models.CharField(max_length=32, choices=FEEDBACK_REQUEST_TYPE_CHOICES, default=FEEDBACK_REQUEST_TYPE_FEATURE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=32, choices=FEEDBACK_STATUS_CHOICES, default=FEEDBACK_STATUS_NEW)
    visibility = models.CharField(max_length=24, choices=FEEDBACK_VISIBILITY_CHOICES, default=FEEDBACK_VISIBILITY_PRIVATE)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='created_feedback_requests', null=True, blank=True, default=None, on_delete=models.SET_DEFAULT)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='owned_feedback_requests', null=True, blank=True, default=None, on_delete=models.SET_DEFAULT)
    source_uri = models.CharField(max_length=1024, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)
    referrer = models.CharField(max_length=1024, blank=True)
    context = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    votes_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)
    is_hidden = models.BooleanField(default=False)
    is_spam = models.BooleanField(default=False)
    needs_review = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-votes_count', '-created_on')
        indexes = (
            models.Index(fields=('site', 'status')),
            models.Index(fields=('site', 'request_type')),
            models.Index(fields=('site', 'visibility')),
            models.Index(fields=('site', 'created_on')),
        )
        verbose_name = 'Feedback request'
        verbose_name_plural = 'Feedback requests'

    def __str__(self):
        return self.title

    @property
    def is_public(self):
        return self.visibility == FEEDBACK_VISIBILITY_PUBLIC and not self.is_hidden and not self.is_spam

    @property
    def is_open_for_voting(self):
        return self.status not in (FEEDBACK_STATUS_SHIPPED, FEEDBACK_STATUS_DECLINED, FEEDBACK_STATUS_MERGED)

    @property
    def display_name(self):
        if self.created_by_id:
            full_name = self.created_by.get_full_name()
            return full_name or self.created_by.get_username()
        return ''

    def refresh_counts(self, save=True):
        self.votes_count = self.votes.filter(is_active=True, is_spam=False).count()
        self.comments_count = self.comments.filter(is_hidden=False, is_spam=False).count()
        if save:
            self.save(update_fields=('votes_count', 'comments_count', 'updated_on'))

    def vote(self, user, importance=0):
        if user is None:
            return None
        vote, _ = FeedbackRequestVote.objects.update_or_create(
            feedback=self,
            user=user,
            defaults={
                'importance': importance or 0,
                'is_active': True,
                'is_spam': False,
            },
        )
        self.refresh_counts()
        return vote

    def unvote(self, user):
        if user is None:
            return 0
        count = self.votes.filter(user=user, is_active=True).update(is_active=False)
        self.refresh_counts()
        return count

    def json_encode(self):
        value = super(FeedbackRequest, self).json_encode()
        value.update(
            {
                'site_id': self.site_id,
                'request_type': self.request_type,
                'title': self.title,
                'description': self.description,
                'status': self.status,
                'visibility': self.visibility,
                'source_uri': self.source_uri,
                'votes_count': self.votes_count,
                'comments_count': self.comments_count,
                'is_hidden': self.is_hidden,
                'is_spam': self.is_spam,
                'needs_review': self.needs_review,
                'created_on': self.created_on,
                'updated_on': self.updated_on,
            }
        )
        return value


class FeedbackRequestVote(HtkBaseModel):
    feedback = models.ForeignKey(FeedbackRequest, related_name='votes', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='feedback_request_votes', on_delete=models.CASCADE)
    importance = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_spam = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = (
            models.UniqueConstraint(fields=('feedback', 'user'), name='feedback_unique_user_vote'),
        )
        ordering = ('-created_on',)
        verbose_name = 'Feedback request vote'
        verbose_name_plural = 'Feedback request votes'

    def __str__(self):
        return '%s vote for %s' % (self.user, self.feedback)


class FeedbackRequestComment(HtkBaseModel):
    feedback = models.ForeignKey(FeedbackRequest, related_name='comments', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='feedback_request_comments', null=True, blank=True, default=None, on_delete=models.SET_DEFAULT)
    comment = models.TextField()
    is_internal = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)
    is_spam = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('created_on',)
        verbose_name = 'Feedback request comment'
        verbose_name_plural = 'Feedback request comments'

    def __str__(self):
        return '%s comment on %s' % (self.user or 'Anonymous', self.feedback)

    def save(self, *args, **kwargs):
        super(FeedbackRequestComment, self).save(*args, **kwargs)
        self.feedback.refresh_counts()

    def json_encode(self):
        value = super(FeedbackRequestComment, self).json_encode()
        value.update(
            {
                'feedback_id': self.feedback_id,
                'comment': self.comment,
                'is_internal': self.is_internal,
                'created_on': self.created_on,
            }
        )
        return value
