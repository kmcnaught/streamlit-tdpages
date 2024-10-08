import inflect
import re

import nltk
from nltk.stem import WordNetLemmatizer
nltk.download('wordnet')  # Download the wordnet data

# Initialize the WordNet lemmatizer
lemmatizer = WordNetLemmatizer()

def change_singular_plural(word):
    if word is None:
        return None
    
    p = inflect.engine()
    singular_form = p.singular_noun(word)
    if singular_form:
        return singular_form
    else:
        # If it is singular, return its plural form
        return p.plural(word.lower())


def get_root(word):
    if word is None:
        return None
    
    word = word.lower()
    pos_tags = ['n', 'v', 'a', 'r']  # n: noun, v: verb, a: adjective, r: adverb
    for pos_tag in pos_tags:
        lemma = lemmatizer.lemmatize(word, pos=pos_tag)
        # If the lemma is different from the original word, return it
        if lemma != word:
            return lemma
    # If none of the POS tags changed the word, return the original word
    return word

def normalize_string(input_string):
    """Normalize strings to lowercase and remove non-alphabetic characters except space."""
    return re.sub(r'[^a-z0-9 ]', '', input_string.lower())

def remove_plural_duplicates(words):

    p = inflect.engine()
    new_words = set()
    
    for word in words:
        # Attempt to convert plural to singular, in case of duplicates we preserve the singular only
        added = False
        try:
            singular_word = p.singular_noun(word)
            if singular_word and singular_word in words:
                new_words.add(singular_word)
                added = True
        except: 
            print("couldn't singularise "+ word)
        finally:
            if not added:
                new_words.add(word)
        
    # Return a list of unique words, preference given to singular forms
    return list(new_words)

def remove_case_duplicates(words):
    
    # Set to track seen lowercase words
    seen = set()
    
    # List to store the result
    final_words = dict()
    
    for word in words:
        # Convert word to lowercase for comparison
        lower_word = word.lower()
        
        # Add the word to the result if the lowercase version is not already present
        # or if this is a lower case
        if lower_word not in seen:
            seen.add(lower_word)
            final_words[lower_word] = word
        elif lower_word==word:
            final_words[lower_word] = word

    return list(final_words.values())


def alphabetise_tuples(words):
    # words is list of tuples (word, symbol)
    return sorted(words, key=lambda x: x[0].lower())     
    