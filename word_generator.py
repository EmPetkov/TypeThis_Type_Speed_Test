import json
import random

# Setup - Choose the file and number of words you want. Original file from https://github.com/dwyl/english-words
DICTIONARY_FILE = 'data/words_2-6.json'
DICTIONARY_SIZE = 250


def generate_dictionary() -> None:
    """ Run this once when you want to generate new dictionary with different word lengths. """
    min_symbols = 2
    max_symbols = 6

    with open('data/words_dictionary.json', 'r') as f:
        data = json.load(f)

    # Filter the words based on their length
    filtered_data = {k: v for k, v in data.items() if min_symbols <= len(k) <= max_symbols}
    print(f"New list: {len(filtered_data)} words.")

    # Write the result to a new file
    with open(f'data/words_{min_symbols}-{max_symbols}.json', 'w') as f:
        json.dump(filtered_data, f)


def get_random_words_from_json(filename: str, size: int = 250) -> list:
    with open(filename, 'r') as f:
        data = json.load(f)

    words_list = random.sample(list(data.keys()), size)

    return words_list


def initialize_words_list() -> list:
    return get_random_words_from_json(filename=DICTIONARY_FILE, size=DICTIONARY_SIZE)
