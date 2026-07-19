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


class FeedbackBoard(HtkBaseModel):
    """A product/app-scoped feedback space.

    A board maps to the public-facing place where a downstream app collects
    feature requests and other feedback. For A&R this lets one reusable HTK app
    serve AwesomeBible, Maskil, LetsPray.AI, and future products while still
    keeping their requests scoped and filterable.
    """

    site = models.ForeignKey(Site, related_name='feedback_boards', on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    slug = models.SlugField(max_length=128)
    description = models.TextField(blank=True)
    visibility = models.CharField(
        max_length=24,
        choices=FEEDBACK_VISIBILITY_CHOICES,
        default=FEEDBACK_VISIBILITY_PUBLIC,
    )
    is_open = models.BooleanField(default=True)
    allow_public_comments = models.BooleanField(default=True)
    allow_public_voting = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (('site', 'slug'),)
        ordering = ('site', 'name')
        verbose_name = 'Feedback board'
        verbose_name_plural = 'Feedback boards'

    def __str__(self):
        return '%s: %s' % (self.site, self.name)

    def json_encode(self):
        value = super(FeedbackBoard, self).json_encode()
        value.update(
            {
                'name': self.name,
                'slug': self.slug,
                'description': self.description,
                'visibility': self.visibility,
                'is_open': self.is_open,
                'allow_public_comments': self.allow_public_comments,
                'allow_public_voting': self.allow_public_voting,
            }
        )
        return value


class FeedbackCategory(HtkBaseModel):
    board = models.ForeignKey(FeedbackBoard, related_name='categories', on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    slug = models.SlugField(max_length=128)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    auto_assign_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='auto_assigned_feedback_categories',
        null=True,
        blank=True,
        default=None,
        on_delete=models.SET_DEFAULT,
    )
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (('board', 'slug'),)
        ordering = ('board', 'sort_order', 'name')
        verbose_name = 'Feedback category'
        verbose_name_plural = 'Feedback categories'

    def __str__(self):
        return '%s / %s' % (self.board, self.name)

    def json_encode(self):
        value = super(FeedbackCategory, self).json_encode()
        value.update(
            {
                'board_id': self.board_id,
                'name': self.name,
                'slug': self.slug,
                'description': self.description,
                'is_active': self.is_active,
            }
        )
        return value


class FeedbackRequest(HtkBaseModel):
    """A public/semi-public idea, feature request, bug, or feedback item."""

    site = models.ForeignKey(Site, related_name='feedback_requests', on_delete=models.CASCADE)
    board = models.ForeignKey(FeedbackBoard, related_name='requests', null=True, blank=True, on_delete=models.SET_NULL)
    category = models.ForeignKey(FeedbackCategory, related_name='requests', null=True, blank=True, on_delete=models.SET_NULL)
    request_type = models.CharField(max_length=32, choices=FEEDBACK_REQUEST_TYPE_CHOICES, default=FEEDBACK_REQUEST_TYPE_FEATURE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=32, choices=FEEDBACK_STATUS_CHOICES, default=FEEDBACK_STATUS_NEW)
    internal_status = models.CharField(max_length=64, blank=True)
    visibility = models.CharField(max_length=24, choices=FEEDBACK_VISIBILITY_CHOICES, default=FEEDBACK_VISIBILITY_PRIVATE)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='created_feedback_requests', null=True, blank=True, default=None, on_delete=models.SET_DEFAULT)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='owned_feedback_requests', null=True, blank=True, default=None, on_delete=models.SET_DEFAULT)
    username = models.CharField(max_length=150, blank=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(max_length=254, blank=True)
    source_uri = models.CharField(max_length=1024, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)
    referrer = models.CharField(max_length=1024, blank=True)
    context = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    votes_count = models.PositiveIntegerField(default=0)
    supporters_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)
    is_hidden = models.BooleanField(default=False)
    is_spam = models.BooleanField(default=False)
    needs_review = models.BooleanField(default=True)
    needs_followup = models.BooleanField(default=True)
    processed = models.BooleanField(default=False)
    merged_into = models.ForeignKey('self', related_name='merged_requests', null=True, blank=True, on_delete=models.SET_NULL)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-votes_count', '-created_on')
        indexes = (
            models.Index(fields=('site', 'status')),
            models.Index(fields=('site', 'request_type')),
            models.Index(fields=('site', 'visibility')),
            models.Index(fields=('site', 'created_on')),
            models.Index(fields=('board', 'category')),
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
        full_name = ' '.join(part for part in (self.first_name, self.last_name) if part).strip()
        return self.name or full_name or self.username

    def _identity_defaults(self, username='', first_name='', last_name='', email='', name=''):
        return {
            'username': username,
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'name': name,
        }

    def refresh_counts(self, save=True):
        self.votes_count = self.votes.filter(is_active=True, is_spam=False).count()
        self.supporters_count = self.subscriptions.filter(is_active=True).count()
        self.comments_count = self.comments.filter(is_hidden=False, is_spam=False).count()
        if save:
            self.save(update_fields=('votes_count', 'supporters_count', 'comments_count', 'updated_on'))

    def subscribe(self, user=None, email='', name='', source='request', notify=True, username='', first_name='', last_name=''):
        if user is None and not email:
            return None
        defaults = self._identity_defaults(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            name=name,
        )
        defaults.update({
            'source': source,
            'is_active': True,
            'notify_status_updates': notify,
        })
        if user is not None:
            subscription, _ = FeedbackRequestSubscription.objects.update_or_create(
                request=self,
                user=user,
                defaults=defaults,
            )
        else:
            subscription, _ = FeedbackRequestSubscription.objects.update_or_create(
                request=self,
                email=email,
                user=None,
                defaults=defaults,
            )
        return subscription

    def vote(self, user=None, email='', name='', ip_address='', importance=0, subscribe=True, username='', first_name='', last_name=''):
        defaults = self._identity_defaults(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            name=name,
        )
        defaults.update({
            'ip_address': ip_address,
            'importance': importance or 0,
            'is_active': True,
            'is_spam': False,
        })
        if user is not None:
            vote, _ = FeedbackRequestVote.objects.update_or_create(
                request=self,
                user=user,
                defaults=defaults,
            )
        elif email:
            vote, _ = FeedbackRequestVote.objects.update_or_create(
                request=self,
                email=email,
                user=None,
                defaults=defaults,
            )
        else:
            return None
        if subscribe:
            self.subscribe(
                user=user,
                email=email,
                name=name,
                source='vote',
                username=username,
                first_name=first_name,
                last_name=last_name,
            )
        self.refresh_counts()
        return vote

    def unvote(self, user=None, email=''):
        qs = self.votes.filter(is_active=True)
        if user is not None:
            qs = qs.filter(user=user)
        elif email:
            qs = qs.filter(user=None, email=email)
        else:
            return 0
        count = qs.update(is_active=False)
        self.refresh_counts()
        return count

    def json_encode(self):
        value = super(FeedbackRequest, self).json_encode()
        value.update(
            {
                'site_id': self.site_id,
                'board_id': self.board_id,
                'category_id': self.category_id,
                'request_type': self.request_type,
                'title': self.title,
                'description': self.description,
                'status': self.status,
                'visibility': self.visibility,
                'source_uri': self.source_uri,
                'votes_count': self.votes_count,
                'supporters_count': self.supporters_count,
                'comments_count': self.comments_count,
                'is_hidden': self.is_hidden,
                'is_spam': self.is_spam,
                'needs_review': self.needs_review,
                'created_on': self.created_on,
                'updated_on': self.updated_on,
            }
        )
        if self.board_id:
            value['board'] = self.board.json_encode()
        if self.category_id:
            value['category'] = self.category.json_encode()
        return value


class FeedbackRequestVote(HtkBaseModel):
    request = models.ForeignKey(FeedbackRequest, related_name='votes', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='feedback_request_votes', null=True, blank=True, default=None, on_delete=models.SET_DEFAULT)
    email = models.EmailField(max_length=254, blank=True)
    username = models.CharField(max_length=150, blank=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    name = models.CharField(max_length=100, blank=True)
    importance = models.PositiveSmallIntegerField(default=0)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_spam = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = (
            models.UniqueConstraint(fields=('request', 'user'), condition=Q(user__isnull=False), name='feedback_unique_user_vote'),
            models.UniqueConstraint(fields=('request', 'email'), condition=Q(user__isnull=True) & ~Q(email=''), name='feedback_unique_email_vote'),
        )
        ordering = ('-created_on',)
        verbose_name = 'Feedback request vote'
        verbose_name_plural = 'Feedback request votes'

    def __str__(self):
        return '%s vote for %s' % (self.user or self.email, self.request)


class FeedbackRequestSubscription(HtkBaseModel):
    request = models.ForeignKey(FeedbackRequest, related_name='subscriptions', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='feedback_request_subscriptions', null=True, blank=True, default=None, on_delete=models.SET_DEFAULT)
    email = models.EmailField(max_length=254, blank=True)
    username = models.CharField(max_length=150, blank=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    name = models.CharField(max_length=100, blank=True)
    source = models.CharField(max_length=64, blank=True)
    is_active = models.BooleanField(default=True)
    notify_status_updates = models.BooleanField(default=True)
    notify_comments = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = (
            models.UniqueConstraint(fields=('request', 'user'), condition=Q(user__isnull=False), name='feedback_unique_user_subscription'),
            models.UniqueConstraint(fields=('request', 'email'), condition=Q(user__isnull=True) & ~Q(email=''), name='feedback_unique_email_subscription'),
        )
        ordering = ('-created_on',)
        verbose_name = 'Feedback request subscription'
        verbose_name_plural = 'Feedback request subscriptions'

    def __str__(self):
        return '%s subscribed to %s' % (self.user or self.email, self.request)


class FeedbackRequestComment(HtkBaseModel):
    request = models.ForeignKey(FeedbackRequest, related_name='comments', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='feedback_request_comments', null=True, blank=True, default=None, on_delete=models.SET_DEFAULT)
    username = models.CharField(max_length=150, blank=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(max_length=254, blank=True)
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
        return '%s comment on %s' % (self.user or self.email or self.name, self.request)

    def save(self, *args, **kwargs):
        super(FeedbackRequestComment, self).save(*args, **kwargs)
        self.request.refresh_counts()

    def json_encode(self):
        value = super(FeedbackRequestComment, self).json_encode()
        value.update(
            {
                'request_id': self.request_id,
                'name': self.name,
                'comment': self.comment,
                'is_internal': self.is_internal,
                'created_on': self.created_on,
            }
        )
        return value


class FeedbackRequestAttachment(HtkBaseModel):
    request = models.ForeignKey(FeedbackRequest, related_name='attachments', on_delete=models.CASCADE)
    comment = models.ForeignKey(FeedbackRequestComment, related_name='attachments', null=True, blank=True, on_delete=models.CASCADE)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='feedback_request_attachments', null=True, blank=True, default=None, on_delete=models.SET_DEFAULT)
    file = models.FileField(upload_to='feedback/attachments/%Y/%m/%d/')
    original_filename = models.CharField(max_length=255, blank=True)
    content_type = models.CharField(max_length=128, blank=True)
    size_bytes = models.PositiveIntegerField(default=0)
    is_screenshot = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('created_on',)
        verbose_name = 'Feedback request attachment'
        verbose_name_plural = 'Feedback request attachments'

    def __str__(self):
        return self.original_filename or str(self.file)

    def json_encode(self):
        value = super(FeedbackRequestAttachment, self).json_encode()
        value.update(
            {
                'request_id': self.request_id,
                'comment_id': self.comment_id,
                'original_filename': self.original_filename,
                'content_type': self.content_type,
                'size_bytes': self.size_bytes,
                'is_screenshot': self.is_screenshot,
                'url': self.file.url if self.file else '',
                'created_on': self.created_on,
            }
        )
        return value


class FeedbackEvidence(HtkBaseModel):
    """Private/internal captured feedback evidence linked to an idea/request."""

    request = models.ForeignKey(FeedbackRequest, related_name='evidence', null=True, blank=True, on_delete=models.SET_NULL)
    site = models.ForeignKey(Site, related_name='feedback_evidence', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='feedback_evidence', null=True, blank=True, default=None, on_delete=models.SET_DEFAULT)
    username = models.CharField(max_length=150, blank=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(max_length=254, blank=True)
    body = models.TextField(blank=True)
    source = models.CharField(max_length=64, blank=True)
    source_uri = models.CharField(max_length=1024, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)
    referrer = models.CharField(max_length=1024, blank=True)
    context = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    is_internal = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_on',)
        verbose_name = 'Feedback evidence'
        verbose_name_plural = 'Feedback evidence'

    def __str__(self):
        return '%s evidence for %s' % (self.source or 'feedback', self.request_id or self.site_id)


class FeedbackRequestStatusUpdate(HtkBaseModel):
    request = models.ForeignKey(FeedbackRequest, related_name='status_updates', on_delete=models.CASCADE)
    status = models.CharField(max_length=32, choices=FEEDBACK_STATUS_CHOICES)
    message = models.TextField(blank=True)
    is_public = models.BooleanField(default=True)
    notify_supporters = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='feedback_request_status_updates', null=True, blank=True, default=None, on_delete=models.SET_DEFAULT)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_on',)
        verbose_name = 'Feedback request status update'
        verbose_name_plural = 'Feedback request status updates'

    def __str__(self):
        return '%s -> %s' % (self.request, self.status)

    def save(self, *args, **kwargs):
        super(FeedbackRequestStatusUpdate, self).save(*args, **kwargs)
        if self.request.status != self.status:
            self.request.status = self.status
            self.request.save(update_fields=('status', 'updated_on'))

    def json_encode(self):
        value = super(FeedbackRequestStatusUpdate, self).json_encode()
        value.update(
            {
                'request_id': self.request_id,
                'status': self.status,
                'message': self.message,
                'is_public': self.is_public,
                'notify_supporters': self.notify_supporters,
                'created_on': self.created_on,
            }
        )
        return value


class FeedbackRequestEvent(HtkBaseModel):
    request = models.ForeignKey(FeedbackRequest, related_name='events', null=True, blank=True, on_delete=models.CASCADE)
    event_type = models.CharField(max_length=32, choices=FEEDBACK_EVENT_CHOICES)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='feedback_request_events', null=True, blank=True, default=None, on_delete=models.SET_DEFAULT)
    message = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_on',)
        verbose_name = 'Feedback request event'
        verbose_name_plural = 'Feedback request events'

    def __str__(self):
        return '%s: %s' % (self.event_type, self.request_id)
