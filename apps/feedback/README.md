# Feedback App

Reusable feedback collection and UserVoice-style feature-request infrastructure.

The app keeps the legacy `Feedback` contact-form model working, while adding a
new product-feedback layer for feature requests, bug reports, votes,
comments, and attachments.

## Core Concepts

### Legacy `Feedback`

`Feedback` remains a simple contact-form submission model:

```python
from htk.apps.feedback.models import Feedback

feedback = Feedback.objects.create(
    site=site,
    user=user,
    name='Jane',
    email='jane@example.com',
    comment='This page was confusing.',
    uri='/bible/Romans/8',
)
```

The legacy API endpoint remains available:

```
POST /feedback/submit
```

### `FeedbackRequest`

A request is the central reviewable item: feature request, bug report,
content issue, support question, or general feedback. New requests default to
`private` and `needs_review=True`; publish them only after staff review.

```python
from htk.apps.feedback.constants import FEEDBACK_REQUEST_TYPE_FEATURE
from htk.apps.feedback.models import FeedbackRequest

request = FeedbackRequest.objects.create(
    site=site,
    created_by=user,
    request_type=FEEDBACK_REQUEST_TYPE_FEATURE,
    title='Add reading plans',
    description='I would like a reading plan for the Psalms.',
    source_uri='/dashboard',
    context={
        'app': 'awesome-bible',
        'surface': 'dashboard',
    },
)
```

## Bug Reports: Screenshot + User/Page State

For bug reports, downstream apps should submit both attachments and structured
context. Screenshots are helpful, but page state is often what makes the report
reproducible.

Suggested context for AwesomeBible:

```json
{
  "app": "awesome-bible",
  "surface": "reader",
  "path": "/bible/Romans/8",
  "reference": "Romans 8",
  "search_query": "love",
  "collection_id": 17,
  "viewport": {"width": 1440, "height": 900},
  "app_version": "2026.06.05"
}
```

Attach screenshots/files with multipart form data. Use the `screenshot` field
name or set `<field>_is_screenshot=true`.

## API Endpoints

The app uses plain Django views and HTK JSON helpers, not DRF. Existing URL
style omits trailing slashes.

### List requests

```
GET /feedback/requests?q=search&type=feature_request&status=planned&order=popular
```

Response includes public, non-hidden, non-spam requests for normal users. Staff
users may see private/hidden items.

### Find likely duplicates

```
GET /feedback/requests/matches?q=reading%20plans
```

Use this while a user is typing a title/body so they can support an existing
idea instead of creating a duplicate.

### Submit a request

```
POST /feedback/requests/submit
Content-Type: application/json

{
  "type": "feature_request",
  "title": "Add reading plans",
  "description": "I would like a reading plan for the Psalms.",
  "context": {
    "surface": "dashboard"
  }
}
```

Form-encoded and multipart submissions are also supported. Public-facing submissions default to `visibility=private` and `needs_review=true`; non-staff users cannot self-publish by passing `visibility=public`. Staff may intentionally set `visibility=public` and `needs_review=false` after review.

### Detail

```
GET /feedback/requests/<id>
```

Returns the request plus public comments and attachments.

### Vote / unvote

```
POST /feedback/requests/<id>/vote
POST /feedback/requests/<id>/unvote
```

Authenticated users can vote once per request. Anonymous/email voting is
supported by passing an email address. Duplicate votes update the existing vote
instead of incrementing the count.

### Comment

```
POST /feedback/requests/<id>/comment
```

Public comments are available by default. Staff users may pass
`is_internal=true` for staff-only comments.

### Staff status update

```
POST /feedback/requests/<id>/status
```

Staff-only. Changes the request status directly.

### My requests

```
GET /feedback/requests/my
```

Authenticated users can see requests they created or voted for.

## Model Shape

- `FeedbackRequest` — idea/feature/bug/content/support/general request.
- `FeedbackRequestVote` — one active support/vote per user or email.
- `FeedbackRequestComment` — public or internal discussion.
- `FeedbackRequestAttachment` — screenshot/file/log attachment.

## Integration Notes

- Keep new submissions private by default and publish only reviewed, public-safe requests.
- Keep status lightweight; add richer workflow only when a real queue needs it.
- Scope every request by `site`.
- Do not expose private emails or account traits in public payloads.
- Add async email/webhook delivery in consuming apps or future HTK work.
- Use `context` JSON for app-specific page state and `metadata` JSON for
  staff/integration-only data.
