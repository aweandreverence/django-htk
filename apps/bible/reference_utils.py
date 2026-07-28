# Python Standard Library Imports
import re
from typing import Dict, Optional, Set

# HTK Imports
from htk.apps.bible.constants.aliases import BIBLE_BOOKS_ALIASES
from htk.utils.text.algorithms import levenshtein_distance


ORDINAL_ALIASES = {
    '1': '1',
    'i': '1',
    'first': '1',
    'one': '1',
    '2': '2',
    'ii': '2',
    'second': '2',
    'two': '2',
    '3': '3',
    'iii': '3',
    'third': '3',
    'three': '3',
}

BOOK_REFERENCE_TOKEN_RE = re.compile(r'\d+|[A-Za-z]+')
BIBLE_BOOKS_NORMALIZED_ALIAS_MAPPINGS: Dict[str, Set[str]] = {}
BIBLE_BOOKS_NORMALIZED_PREFIX_MAPPINGS: Dict[str, Set[str]] = {}


def normalize_bible_book_reference(reference: Optional[str]) -> str:
    """Normalize a Bible book name or abbreviation for lookup.

    The normalized form intentionally ignores punctuation, spacing, and case so
    common reference styles such as ``1Co``, ``1 Co.``, and ``First Co`` can be
    resolved through the same alias map.
    """
    tokens = []
    for match in BOOK_REFERENCE_TOKEN_RE.finditer(reference or ''):
        token = match.group(0).casefold()
        tokens.append(ORDINAL_ALIASES.get(token, token))
    return ''.join(tokens)


def _allowed_bible_book_alias_distance(value: str) -> int:
    """Return the maximum edit distance for fuzzy Bible book aliases."""
    return 1


def _add_normalized_mapping(
    mapping: Dict[str, Set[str]],
    key: str,
    book_name: str,
) -> None:
    if not key:
        return
    mapping.setdefault(key, set()).add(book_name)


for _book_name, _aliases in BIBLE_BOOKS_ALIASES.items():
    for _alias in (_book_name, *_aliases):
        _normalized_alias = normalize_bible_book_reference(_alias)
        _add_normalized_mapping(
            BIBLE_BOOKS_NORMALIZED_ALIAS_MAPPINGS,
            _normalized_alias,
            _book_name,
        )
        for _prefix_length in range(3, len(_normalized_alias)):
            _add_normalized_mapping(
                BIBLE_BOOKS_NORMALIZED_PREFIX_MAPPINGS,
                _normalized_alias[:_prefix_length],
                _book_name,
            )


def _unique_book_name(book_names: Set[str]) -> Optional[str]:
    if len(book_names) == 1:
        return next(iter(book_names))
    return None


def _common_prefix_length(left: str, right: str) -> int:
    length = 0
    for left_character, right_character in zip(left, right):
        if left_character != right_character:
            break
        length += 1
    return length


def match_bible_book_alias(
    reference: Optional[str],
    allow_prefix: bool = True,
    allow_fuzzy: bool = False,
) -> Optional[Dict[str, object]]:
    """Return a unique canonical book match for a name or abbreviation.

    Matching is deliberately conservative:
    1. normalized exact aliases win first;
    2. normalized prefixes are accepted only when they complete to one book;
    3. Levenshtein correction is accepted only when the best match maps to one
       book, so misspelled ambiguous abbreviations are left unresolved.
    """
    normalized_reference = normalize_bible_book_reference(reference)
    if not normalized_reference:
        return None

    exact_book = _unique_book_name(
        BIBLE_BOOKS_NORMALIZED_ALIAS_MAPPINGS.get(normalized_reference, set())
    )
    if exact_book:
        return {
            'book': exact_book,
            'distance': 0,
            'kind': 'exact',
            'normalized': normalized_reference,
        }

    if allow_prefix:
        prefix_book = _unique_book_name(
            BIBLE_BOOKS_NORMALIZED_PREFIX_MAPPINGS.get(
                normalized_reference, set()
            )
        )
        if prefix_book:
            return {
                'book': prefix_book,
                'distance': 0,
                'kind': 'prefix',
                'normalized': normalized_reference,
            }

    if not allow_fuzzy or len(normalized_reference) < 2:
        return None

    candidate_mappings = dict(BIBLE_BOOKS_NORMALIZED_ALIAS_MAPPINGS)
    if allow_prefix:
        candidate_mappings.update(BIBLE_BOOKS_NORMALIZED_PREFIX_MAPPINGS)

    best_distance = None
    best_prefix_length = None
    best_books = set()
    for candidate, book_names in candidate_mappings.items():
        distance = levenshtein_distance(normalized_reference, candidate)
        if distance > _allowed_bible_book_alias_distance(candidate):
            continue
        prefix_length = _common_prefix_length(normalized_reference, candidate)
        if (
            best_distance is None
            or distance < best_distance
            or (
                distance == best_distance
                and prefix_length > best_prefix_length
            )
        ):
            best_distance = distance
            best_prefix_length = prefix_length
            best_books = set(book_names)
        elif distance == best_distance and prefix_length == best_prefix_length:
            best_books.update(book_names)

    best_book = _unique_book_name(best_books)
    if best_book:
        return {
            'book': best_book,
            'distance': best_distance,
            'kind': 'fuzzy',
            'normalized': normalized_reference,
        }
    return None


def resolve_bible_book_alias(
    reference: Optional[str],
    allow_prefix: bool = True,
    allow_fuzzy: bool = False,
) -> Optional[str]:
    """Resolve a Bible book name or abbreviation to one canonical book name."""
    match = match_bible_book_alias(
        reference,
        allow_prefix=allow_prefix,
        allow_fuzzy=allow_fuzzy,
    )
    return match['book'] if match else None
