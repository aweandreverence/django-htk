# Python Standard Library Imports
import re


# Common Bible book abbreviations or aliases

BIBLE_BOOKS_ALIASES = {
    'Genesis' : [
        'Gen',
        'Gn',
    ],
    'Exodus' : [
        'Ex',
        'Exo',
    ],
    'Leviticus' : [
        'Lev',
        'Lv',
    ],
    'Numbers' : [
        'Num',
    ],
    'Deuteronomy' : [
        'Deut',
        'Dt',
    ],
    'Joshua' : [
        'Jos',
        'Josh',
    ],
    'Judges' : [
        'Jdg',
        'Judg',
        'Judge',
    ],
    'Ruth' : [
        'Rut',
    ],
    '1 Samuel' : [
        '1Sam',
        '1 Sam',
    ],
    '2 Samuel' : [
        '2Sam',
        '2 Sam',
    ],
    '1 Kings' : [
        '1Kin',
        '1 Kin',
    ],
    '2 Kings' : [
        '2Kin',
        '2 Kin',
    ],
    '1 Chronicles' : [
        '1Chr',
        '1 Chr',
    ],
    '2 Chronicles' : [
        '2Chr',
        '2 Chr',
    ],
    'Ezra' : [
        'Ezr',
    ],
    'Nehemiah' : [
        'Neh',
    ],
    'Esther' : [
        'Esth',
    ],
    'Job' : [
        'Job',
    ],
    'Psalms' : [
        'Ps',
        'Psalm',
    ],
    'Proverbs' : [
        'Pro',
        'Prov',
    ],
    'Ecclesiastes' : [
        'Eccl',
    ],
    'Song of Solomon' : [
        'Song',
        'Song of Songs',
        'Songs',
    ],
    'Isaiah' : [
        'Is',
        'Isa',
    ],
    'Jeremiah' : [
        'Jer',
    ],
    'Lamentations' : [
        'Lam',
    ],
    'Ezekiel' : [
        'Eze',
        'Ezek',
    ],
    'Daniel' : [
        'Dan',
    ],
    'Hosea' : [
        'Hos',
    ],
    'Joel' : [
        'Jl',
        'Joel',
    ],
    'Amos' : [
        'Am',
        'Amo',
        'Amos',
    ],
    'Obadiah' : [
        'Ob',
        'Oba',
        'Obad',
    ],
    'Jonah' : [
        'Jon',
    ],
    'Micah' : [
        'Mic',
    ],
    'Nahum' : [
        'Nah',
    ],
    'Habakkuk' : [
        'Hab',
    ],
    'Zephaniah' : [
        'Zep',
        'Zeph',
    ],
    'Haggai' : [
        'Hag',
    ],
    'Zechariah' : [
        'Zec',
        'Zech',
    ],
    'Malachi' : [
        'Mal',
    ],
    'Matthew' : [
        'Mt',
        'Mat',
        'Matt',
    ],
    'Mark' : [
        'Mk',
    ],
    'Luke' : [
        'Lk',
        'Luk',
    ],
    'John' : [
        'Jn',
    ],
    'Acts' : [
        'Ac',
        'Act',
    ],
    'Romans' : [
        'Ro',
        'Rom',
        'Roms',
    ],
    '1 Corinthians' : [
        '1Co',
        '1Cor',
        '1 Cor',
        '1 Corin',
        '1 Corinth',
    ],
    '2 Corinthians' : [
        '2Co',
        '2Cor',
        '2 Cor',
        '2 Corin',
        '2 Corinth',
    ],
    'Galatians' : [
        'Gal',
    ],
    'Ephesians' : [
        'Eph',
    ],
    'Philippians' : [
        'Phil',
    ],
    'Colossians' : [
        'Col',
        'Cols',
    ],
    '1 Thessalonians' : [
        '1Th',
        '1Thess',
        '1 Th',
        '1 Thess',
    ],
    '2 Thessalonians' : [
        '2Th',
        '2Thess',
        '2 Th',
        '2 Thess',
    ],
    '1 Timothy' : [
        '1Tim',
        '1 Tim',
    ],
    '2 Timothy' : [
        '2Tim',
        '2 Tim',
    ],
    'Titus' : [
        'Tit',
    ],
    'Philemon' : [
        'Philem',
        'Phlm',
        'Phm',
    ],
    'Hebrews' : [
        'Heb',
    ],
    'James' : [
        'Jas',
        'Jam',
    ],
    '1 Peter' : [
        '1Pe',
        '1Pet',
        '1 Pet',
    ],
    '2 Peter' : [
        '2Pe',
        '2Pet',
        '2 Pet',
    ],
    '1 John' : [
        '1Jn',
        '1John',
        '1 Jn',
    ],
    '2 John' : [
        '2Jn',
        '2John',
        '2 Jn',
    ],
    '3 John' : [
        '3Jn',
        '3John',
        '3 Jn',
    ],
    'Jude' : [
        'Jud',
    ],
    'Revelation' : [
        'Rev',
    ],
}

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


def normalize_bible_book_reference(reference):
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


def levenshtein_distance(left, right):
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)

    previous_row = list(range(len(right) + 1))
    for left_index, left_character in enumerate(left, start=1):
        current_row = [left_index]
        for right_index, right_character in enumerate(right, start=1):
            insert_cost = current_row[right_index - 1] + 1
            delete_cost = previous_row[right_index] + 1
            replace_cost = previous_row[right_index - 1] + (
                0 if left_character == right_character else 1
            )
            current_row.append(min(insert_cost, delete_cost, replace_cost))
        previous_row = current_row
    return previous_row[-1]


def allowed_bible_book_alias_distance(value):
    return 1


# Programmatically build mappings from common Bible book abbreviations or aliases to canonical name, including uppercase and lowercase variants
BIBLE_BOOKS_ALIAS_MAPPINGS = {}
BIBLE_BOOKS_NORMALIZED_ALIAS_MAPPINGS = {}
BIBLE_BOOKS_NORMALIZED_PREFIX_MAPPINGS = {}


def _add_normalized_mapping(mapping, key, book_name):
    if not key:
        return
    mapping.setdefault(key, set()).add(book_name)


for book_name, aliases in BIBLE_BOOKS_ALIASES.items():
    for alias in (book_name, *aliases):
        variants = (
            book_name.lower(),
            book_name.upper(),
            alias,
            alias.lower(),
            alias.upper(),
        )
        for variant in variants:
            BIBLE_BOOKS_ALIAS_MAPPINGS[variant] = book_name

        normalized_alias = normalize_bible_book_reference(alias)
        _add_normalized_mapping(
            BIBLE_BOOKS_NORMALIZED_ALIAS_MAPPINGS,
            normalized_alias,
            book_name,
        )
        for prefix_length in range(3, len(normalized_alias)):
            _add_normalized_mapping(
                BIBLE_BOOKS_NORMALIZED_PREFIX_MAPPINGS,
                normalized_alias[:prefix_length],
                book_name,
            )


def _unique_book_name(book_names):
    if len(book_names) == 1:
        return next(iter(book_names))
    return None


def _common_prefix_length(left, right):
    length = 0
    for left_character, right_character in zip(left, right):
        if left_character != right_character:
            break
        length += 1
    return length


def match_bible_book_alias(reference, allow_prefix=True, allow_fuzzy=False):
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
        if distance > allowed_bible_book_alias_distance(candidate):
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


def resolve_bible_book_alias(reference, allow_prefix=True, allow_fuzzy=False):
    match = match_bible_book_alias(
        reference,
        allow_prefix=allow_prefix,
        allow_fuzzy=allow_fuzzy,
    )
    return match['book'] if match else None
