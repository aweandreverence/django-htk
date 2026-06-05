# Python Standard Library Imports
import json

# Django Imports
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.db.models import Q
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_POST

# HTK Imports
from htk.api.constants import *
from htk.api.utils import json_response_error
from htk.api.utils import json_response_form_error
from htk.api.utils import json_response_not_found
from htk.api.utils import json_response_okay
from htk.apps.feedback.constants import *
from htk.apps.feedback.forms import FeedbackForm
from htk.apps.feedback.models import FeedbackBoard
from htk.apps.feedback.models import FeedbackCategory
from htk.apps.feedback.models import FeedbackEvidence
from htk.apps.feedback.models import FeedbackRequest
from htk.apps.feedback.models import FeedbackRequestAttachment
from htk.apps.feedback.models import FeedbackRequestComment
from htk.apps.feedback.models import FeedbackRequestEvent
from htk.apps.feedback.models import FeedbackRequestStatusUpdate


@require_POST
def submit(request):
    success = False

    antispam = request.POST.get(HTK_API_KEY_ANTISPAM) == HTK_API_VALUE_ANTISPAM_CHALLENGE_RESPONSE
    feedback_form = FeedbackForm(request.POST)
    if antispam and feedback_form.is_valid():
        site = get_current_site(request)
        success = True
        feedback = feedback_form.save(site, request)
    data = {}
    if success:
        response = json_response_okay()
    else:
        response = json_response_error()
    return response


def _request_user(request):
    user = getattr(request, 'user', None)
    if user is not None and user.is_authenticated:
        return user
    return None


def _client_ip(request):
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR') or None


def _json_body(request):
    if not request.body:
        return {}
    try:
        body = json.loads(request.body.decode('utf-8'))
    except (TypeError, ValueError):
        body = {}
    return body


def _payload(request):
    content_type = request.META.get('CONTENT_TYPE', '')
    body = _json_body(request) if content_type.startswith('application/json') else {}
    data = {}
    data.update(request.POST.dict())
    data.update(body)
    return data


def _json_value(value, default=None):
    if default is None:
        default = {}
    if value in (None, ''):
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


def _bool_value(value, default=False):
    if value in (None, ''):
        return default
    if isinstance(value, bool):
        return value
    return str(value).lower() in ('1', 'true', 'yes', 'on')


def _int_value(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _feedback_queryset(request):
    site = get_current_site(request)
    qs = FeedbackRequest.objects.filter(site=site)
    user = _request_user(request)
    is_staff = user is not None and user.is_staff
    if not is_staff:
        qs = qs.filter(
            visibility=FEEDBACK_VISIBILITY_PUBLIC,
            is_hidden=False,
            is_spam=False,
        )
    return qs


def _get_board(site, board_slug=None, create=True):
    if not board_slug:
        board_slug = FEEDBACK_DEFAULT_BOARD_SLUG
    try:
        board = FeedbackBoard.objects.get(site=site, slug=board_slug)
    except FeedbackBoard.DoesNotExist:
        if create:
            board = FeedbackBoard.objects.create(
                site=site,
                slug=board_slug,
                name=board_slug.replace('-', ' ').replace('_', ' ').title(),
            )
        else:
            board = None
    return board


def _get_category(board, category_slug=None):
    category = None
    if board is not None and category_slug:
        try:
            category = board.categories.get(slug=category_slug, is_active=True)
        except FeedbackCategory.DoesNotExist:
            category = None
    return category


def _serialize_request(feedback_request, include_detail=False):
    data = feedback_request.json_encode()
    if include_detail:
        data.update(
            {
                'comments': [
                    comment.json_encode()
                    for comment in feedback_request.comments.filter(
                        is_hidden=False,
                        is_spam=False,
                        is_internal=False,
                    )
                ],
                'attachments': [
                    attachment.json_encode()
                    for attachment in feedback_request.attachments.all()
                ],
                'status_updates': [
                    status_update.json_encode()
                    for status_update in feedback_request.status_updates.filter(
                        is_public=True
                    )
                ],
            }
        )
    return data


def _log_event(feedback_request, event_type, actor=None, message='', metadata=None):
    if metadata is None:
        metadata = {}
    return FeedbackRequestEvent.objects.create(
        request=feedback_request,
        event_type=event_type,
        actor=actor,
        message=message,
        metadata=metadata,
    )


def _handle_attachments(request, feedback_request, comment=None):
    user = _request_user(request)
    attachments = []
    for field_name, uploaded_file in request.FILES.items():
        is_screenshot = field_name in ('screenshot', 'screenshot_file') or _bool_value(
            request.POST.get('%s_is_screenshot' % field_name),
            False,
        )
        attachment = FeedbackRequestAttachment.objects.create(
            request=feedback_request,
            comment=comment,
            uploaded_by=user,
            file=uploaded_file,
            original_filename=uploaded_file.name,
            content_type=getattr(uploaded_file, 'content_type', '') or '',
            size_bytes=getattr(uploaded_file, 'size', 0) or 0,
            is_screenshot=is_screenshot,
        )
        attachments.append(attachment)
        _log_event(
            feedback_request,
            FEEDBACK_EVENT_ATTACHMENT_ADDED,
            actor=user,
            metadata={'attachment_id': attachment.id},
        )
    return attachments


@require_GET
def request_list(request):
    qs = _feedback_queryset(request)
    data = request.GET
    board_slug = data.get('board')
    category_slug = data.get('category')
    request_type = data.get('type') or data.get('request_type')
    status = data.get('status')
    query = data.get('q') or data.get('query')
    order = data.get('order') or data.get('ordering') or 'popular'

    if board_slug:
        qs = qs.filter(board__slug=board_slug)
    if category_slug:
        qs = qs.filter(category__slug=category_slug)
    if request_type:
        qs = qs.filter(request_type=request_type)
    if status:
        qs = qs.filter(status=status)
    if query:
        qs = qs.filter(Q(title__icontains=query) | Q(description__icontains=query))

    if order == 'recent':
        qs = qs.order_by('-created_on')
    elif order == 'updated':
        qs = qs.order_by('-updated_on')
    else:
        qs = qs.order_by('-votes_count', '-created_on')

    limit = min(max(_int_value(data.get('limit'), 50), 1), 100)
    offset = max(_int_value(data.get('offset'), 0), 0)
    results = list(qs[offset:offset + limit])
    response = json_response_okay(
        {
            'requests': [_serialize_request(item) for item in results],
            'limit': limit,
            'offset': offset,
            'has_more': qs.count() > offset + limit,
        }
    )
    return response


@require_GET
def request_detail(request, request_id):
    try:
        feedback_request = _feedback_queryset(request).get(id=request_id)
    except FeedbackRequest.DoesNotExist:
        return json_response_not_found()
    return json_response_okay({'request': _serialize_request(feedback_request, include_detail=True)})


@require_GET
def request_matches(request):
    query = request.GET.get('q') or request.GET.get('query') or request.GET.get('title')
    if not query:
        return json_response_okay({'requests': []})
    qs = _feedback_queryset(request).filter(
        Q(title__icontains=query) | Q(description__icontains=query)
    ).order_by('-votes_count', '-created_on')[:10]
    return json_response_okay({'requests': [_serialize_request(item) for item in qs]})


@require_POST
def request_submit(request):
    site = get_current_site(request)
    data = _payload(request)
    title = (data.get('title') or '').strip()
    description = (data.get('description') or data.get('message') or data.get('comment') or '').strip()
    if not title:
        return json_response_error({'error': 'Missing title'})

    user = _request_user(request)
    board = _get_board(site, data.get('board') or data.get('board_slug'))
    category = _get_category(board, data.get('category') or data.get('category_slug'))
    owner = category.auto_assign_owner if category is not None else None
    source_uri = data.get('source_uri') or data.get('uri') or request.META.get('HTTP_REFERER', '')
    user_agent = data.get('user_agent') or request.META.get('HTTP_USER_AGENT', '')
    referrer = data.get('referrer') or request.META.get('HTTP_REFERER', '')
    visibility = data.get('visibility') or FEEDBACK_VISIBILITY_PUBLIC

    feedback_request = FeedbackRequest.objects.create(
        site=site,
        board=board,
        category=category,
        request_type=data.get('type') or data.get('request_type') or FEEDBACK_REQUEST_TYPE_FEATURE,
        title=title,
        description=description,
        visibility=visibility,
        created_by=user,
        owner=owner,
        name=data.get('name', ''),
        email=data.get('email', ''),
        source_uri=source_uri,
        user_agent=user_agent,
        referrer=referrer,
        context=_json_value(data.get('context')),
        metadata=_json_value(data.get('metadata')),
        needs_review=_bool_value(data.get('needs_review'), False),
    )
    FeedbackEvidence.objects.create(
        request=feedback_request,
        site=site,
        user=user,
        name=data.get('name', ''),
        email=data.get('email', ''),
        body=description,
        source=data.get('source', 'submit'),
        source_uri=source_uri,
        user_agent=user_agent,
        referrer=referrer,
        context=feedback_request.context,
        metadata=feedback_request.metadata,
    )
    feedback_request.vote(
        user=user,
        email=data.get('email', ''),
        name=data.get('name', ''),
        ip_address=_client_ip(request),
        importance=_int_value(data.get('importance'), 0),
        subscribe=_bool_value(data.get('subscribe'), True),
    )
    _handle_attachments(request, feedback_request)
    _log_event(feedback_request, FEEDBACK_EVENT_CREATED, actor=user)
    return json_response_okay({'request': _serialize_request(feedback_request, include_detail=True)})


@require_POST
def request_vote(request, request_id):
    try:
        feedback_request = _feedback_queryset(request).get(id=request_id)
    except FeedbackRequest.DoesNotExist:
        return json_response_not_found()
    if not feedback_request.is_open_for_voting:
        return json_response_error({'error': 'Request is closed for voting'})
    data = _payload(request)
    user = _request_user(request)
    email = data.get('email', '')
    if user is None and not email:
        return json_response_error({'error': 'Authenticated user or email required'})
    vote = feedback_request.vote(
        user=user,
        email=email,
        name=data.get('name', ''),
        ip_address=_client_ip(request),
        importance=_int_value(data.get('importance'), 0),
        subscribe=_bool_value(data.get('subscribe'), True),
    )
    _log_event(feedback_request, FEEDBACK_EVENT_VOTED, actor=user)
    return json_response_okay(
        {
            'request': _serialize_request(feedback_request),
            'vote_id': vote.id if vote is not None else None,
        }
    )


@require_POST
def request_unvote(request, request_id):
    try:
        feedback_request = _feedback_queryset(request).get(id=request_id)
    except FeedbackRequest.DoesNotExist:
        return json_response_not_found()
    data = _payload(request)
    user = _request_user(request)
    email = data.get('email', '')
    count = feedback_request.unvote(user=user, email=email)
    _log_event(feedback_request, FEEDBACK_EVENT_UNVOTED, actor=user)
    return json_response_okay({'request': _serialize_request(feedback_request), 'removed': count})


@require_POST
def request_comment(request, request_id):
    try:
        feedback_request = _feedback_queryset(request).get(id=request_id)
    except FeedbackRequest.DoesNotExist:
        return json_response_not_found()
    data = _payload(request)
    comment_text = (data.get('comment') or data.get('message') or '').strip()
    if not comment_text:
        return json_response_error({'error': 'Missing comment'})
    user = _request_user(request)
    is_internal = _bool_value(data.get('is_internal'), False)
    if is_internal and not (user is not None and user.is_staff):
        return json_response_error({'error': 'Forbidden'}, status=403)
    comment = FeedbackRequestComment.objects.create(
        request=feedback_request,
        user=user,
        name=data.get('name', ''),
        email=data.get('email', ''),
        comment=comment_text,
        is_internal=is_internal,
    )
    _handle_attachments(request, feedback_request, comment=comment)
    _log_event(feedback_request, FEEDBACK_EVENT_COMMENTED, actor=user)
    return json_response_okay({'comment': comment.json_encode(), 'request': _serialize_request(feedback_request)})


@require_POST
def request_status_update(request, request_id):
    user = _request_user(request)
    if user is None or not user.is_staff:
        return json_response_error({'error': 'Forbidden'}, status=403)
    try:
        feedback_request = FeedbackRequest.objects.get(id=request_id)
    except FeedbackRequest.DoesNotExist:
        return json_response_not_found()
    data = _payload(request)
    status = data.get('status')
    if status not in dict(FEEDBACK_STATUS_CHOICES):
        return json_response_error({'error': 'Invalid status'})
    status_update = FeedbackRequestStatusUpdate.objects.create(
        request=feedback_request,
        status=status,
        message=data.get('message', ''),
        is_public=_bool_value(data.get('is_public'), True),
        notify_supporters=_bool_value(data.get('notify_supporters'), True),
        created_by=user,
    )
    _log_event(
        feedback_request,
        FEEDBACK_EVENT_STATUS_UPDATED,
        actor=user,
        metadata={'status_update_id': status_update.id, 'status': status},
    )
    return json_response_okay({'status_update': status_update.json_encode(), 'request': _serialize_request(feedback_request)})


@login_required
@require_GET
def request_my(request):
    qs = FeedbackRequest.objects.filter(site=get_current_site(request)).filter(
        Q(created_by=request.user) | Q(votes__user=request.user) | Q(subscriptions__user=request.user)
    ).distinct().order_by('-updated_on')
    return json_response_okay({'requests': [_serialize_request(item) for item in qs]})
