from typing import Iterable


def levenshtein_distance(left: str, right: str) -> int:
    """Return the Levenshtein edit distance between two strings.

    The distance is the minimum number of insertions, deletions, or
    substitutions needed to change ``left`` into ``right``.

    See: https://en.wikipedia.org/wiki/Levenshtein_distance
    """
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


def get_closest_dict_words(
    word: str,
    dict_words: Iterable[str],
    num_results: int = 20,
) -> list[str]:
    """Uses the Levenshtein distance for Word Autocompletion and Autocorrection

    https://blog.paperspace.com/implementing-levenshtein-distance-word-autocomplete-autocorrect/
    """
    dict_word_distances = []
    distances = []
    greatest_distance_allowed = None

    for dict_word in dict_words:
        word_distance = levenshtein_distance(word, dict_word)

        if greatest_distance_allowed is not None and word_distance > greatest_distance_allowed:
            # skip this word, because it cannot be among the closest words
            pass
        else:
            dict_word_distances.append((word_distance, dict_word, ))

            distances.append(word_distance)
            distances.sort()
            if len(distances) >= num_results:
                distances = distances[:num_results]
                greatest_distance_allowed = distances[-1]

    dict_word_distances.sort(key=lambda x: x[0])

    closest_words = [
        dict_word
        for distance, dict_word
        in dict_word_distances[:num_results]
    ]

    return closest_words
