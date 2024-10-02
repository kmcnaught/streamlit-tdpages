from nltk.corpus import wordnet as wn
import nltk
import gensim.models
from nltk.data import find
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet
import streamlit as st


import gensim.downloader as api
from gensim.models import KeyedVectors



# Load a pre-trained Word2Vec model
wv_model = api.load("glove-wiki-gigaword-100")

# Compute word similar from word2vec vectors
def wv_similarity(word1, word2):
    word1 = word1.lower()
    word2 = word2.lower()
    if word1 in wv_model and word2 in wv_model:
        return wv_model.similarity(word1, word2)
    else:
        # if word1 not in wv_model:
        #     st.write(f"{word1} not in Word2Vec")
        if word2 not in wv_model:
            st.write(f"{word2} not in Word2Vec")
        return -1.0;#??    

# Use wordnet to find semantically similar words, then score with word2vec
# This seems to consistently give more appropriate words that using word2vec directly
# The only thing that word2vec can be useful for is mapping a phrase to a single word
# which is sometimes pretty good, but can also be a not-good mapping, so we're not
# currently doing that. 
def find_semantically_related_words_with_similarity(word):
    """ Find semantically related forms of a word across all POS categories with path similarity scores """
    related_words = {}

    # Iterate over all possible POS categories
    for pos in [wn.NOUN, wn.VERB, wn.ADJ, wn.ADV]:
        synsets = wn.synsets(word, pos=pos)

        for synset in synsets:
            # Collect synonyms
            for lemma in synset.lemmas():
                related_words[lemma.name()] = wv_similarity(lemma.name(), word)

            # Collect hypernyms and hyponyms
            for hypernym in synset.hypernyms():
                for lemma in hypernym.lemmas():
                    related_words[lemma.name()] = wv_similarity(lemma.name(), word)

            for hyponym in synset.hyponyms():
                for lemma in hyponym.lemmas():
                    related_words[lemma.name()] = wv_similarity(lemma.name(), word)

            # Collect derivationally related forms
            for lemma in synset.lemmas():
                related_forms = lemma.derivationally_related_forms()
                for related_lemma in related_forms:
                    related_word = related_lemma.name()                    
                    related_words[related_word] = wv_similarity(related_word, word)

    # Sort related words by similarity score
    sorted_related_words = sorted(related_words.items(), key=lambda item: item[1], reverse=True)    

    return sorted_related_words


# Get the base form of a word, if you don't know its PoS
def get_base_form(word):
    lemmatizer = WordNetLemmatizer()
    
    base_forms = [
        # Try lemmatizing with different PoS tags
        lemmatizer.lemmatize(word, pos=wordnet.NOUN),
        lemmatizer.lemmatize(word, pos=wordnet.VERB),
        lemmatizer.lemmatize(word, pos=wordnet.ADJ),
        lemmatizer.lemmatize(word, pos=wordnet.ADV),        
    ]

    # Special case for adverbs which don't always get lemmatized correctly with the above
    try:
        # https://stackoverflow.com/a/57686805 
        adv_base = wordnet.synset(word+'.r.1').lemmas()[0].pertainyms()[0].name()
        base_forms.append(adv_base)
    except:
        pass
    
    # Take the shortest form as the most base form
    return min(base_forms, key=len)


