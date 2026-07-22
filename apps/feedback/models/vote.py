# Django Imports
from django.conf import settings
from django.db import models

# HTK Imports
from htk.apps.feedback.models.feedback import FeedbackRequest
from htk.models import HtkBaseModel


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
