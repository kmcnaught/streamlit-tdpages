import streamlit as st
import pandas as pd
from io import BytesIO
import sqlite3
import tempfile
import os

# defer other imports until asked to do something, so we
# can give "busy" feedback

loaded_dependencies=False

# Streamlit UI
st.title('TD Snap pageset creation')

# File uploader for the database file
db_file = st.file_uploader("Choose a blank TD Pageset to use", type=['spb'])
    
# File uploader for the text file containing words
text_file = st.file_uploader("Choose a Text File with Word List", type=['txt'])

# Create a checkbox that defaults to True
st.write("If this is ticked, the pageset will be named after the words list filename")
update_title = st.checkbox('Update title', value=True)

st.write("By default we use one line per word or phrase in the text file. " +\
"If this is ticked, we expect each line as: "+ \
"\"button label|button message\" " + \
"e.g. \"name|my name is Kirsty\"")

different_labels = st.checkbox('Use separate labels + messages', value=False)

# Create an expander for logs
log_expander = st.expander("Show Logs", expanded=False)

# Check if a file has been uploaded
if text_file is not None and update_title:
    # Extract the file name without extension
    file_name, file_extension = os.path.splitext(text_file.name)
    
    # Display the filename in a text input field, pre-filled with the file name (without extension)
    file_name_input = st.text_input("New pageset name:", value=file_name)    

def get_next_id(cursor, table_name):
    
    # Query the sqlite_sequence table to find the next ID for the specified table
    cursor.execute("SELECT seq FROM sqlite_sequence WHERE name=?", (table_name,))
    result = cursor.fetchone()
    
    next_id = 1
    if result:
        next_id = result[0] + 1
    
    return next_id
    

def add_words_alphabetised(db_empty_path, words_and_symbols, messages=None, include_letter_cells=True):

    pageId, layouts = get_page_layout_details(db_empty_path)    
    letter_colors, letter_symbols = get_letter_colours_symbols()    

    # Find available positions on all layouts upfront
    all_available_positions = {}
    for (pageLayoutId, num_columns, num_rows) in layouts: # placed on every grid layout                                    
        all_available_positions[pageLayoutId] = find_available_positions(db_empty_path, pageLayoutId, num_columns, num_rows) 


    try:
            
        # Connect to db_empty for insertions
        conn_empty = sqlite3.connect(db_empty_path)
        cursor_empty = conn_empty.cursor()

        # Calculate the starting IDs for new entries in db_empty
        next_id = get_next_id(cursor_empty, "Button")
        next_ref_id = get_next_id(cursor_empty, "ElementReference")
    
        # Make sure words are alphabetised, and order is maintained
        # for accompanying messages
        if messages is not None:
            # Combine words_and_symbols with messages using zip
            combined = list(zip(words_and_symbols, messages))
            # Sort based on first element of words_and_symbols
            combined.sort(key=lambda x: x[0][0].lower())
            # Unzip back into separate lists
            words_and_symbols, messages = zip(*combined)
        else:
            # If messages is None, just sort words_and_symbols
            words_and_symbols = sorted(words_and_symbols, key=lambda x: x[0].lower())

        pos_i = 0 # keep track of available positions
        current_letter = None

        for i, (word, symbol) in enumerate(words_and_symbols):                                    
            
            letter = word[0].lower()
            
            #########################################################
            # Optionally add a letter cell for each starting letter #
            #########################################################
                
            if include_letter_cells:
                if letter != current_letter:
                    current_letter = letter 
                    
                    # Add an action-less button for this letter               
                    if (current_letter in letter_symbols):
                        add_button(cursor_empty, next_id, next_ref_id, None, letter_symbols[current_letter])
                        add_command_nothing(cursor_empty, next_id)
                        add_element_reference_with_color(cursor_empty, current_letter, pageId, next_ref_id)
                        for pageLayoutId, available_positions in all_available_positions.items(): # placed on every grid layout
                            if pos_i >= len(available_positions):
                                raise ValueError("Ran out of available positions after adding " + i + " buttons on layout "+ pageLayoutId)
                            add_button_placement(cursor_empty, pageLayoutId, next_ref_id, available_positions[pos_i])
                            #break

                        next_id += 1
                        next_ref_id += 1  
                        pos_i += 1

            #########################################
            # Now add a button for the current word #   
            #########################################
            message = None
            if messages is not None:
                message = messages[i]
            add_button(cursor_empty, next_id, next_ref_id, word, symbol, message)
            add_command_speak_message(cursor_empty, next_id)
            add_element_reference_with_color(cursor_empty, word, pageId, next_ref_id)
            for pageLayoutId, available_positions in all_available_positions.items(): # placed on every grid layout
                if pos_i >= len(available_positions):
                    raise ValueError("Ran out of available positions after adding " + i + " buttons on layout "+ pageLayoutId)
                add_button_placement(cursor_empty, pageLayoutId, next_ref_id, available_positions[pos_i])
                #break

            # Increment IDs for the next iteration
            next_id += 1
            next_ref_id += 1 
            pos_i += 1
        
        # commit changes
        conn_empty.commit()
    except Exception as e:
        # If an error occurs, roll back any changes made during the transaction
        # print(f"An error occurred: {e}")
        # traceback.print_exc()  # Print the full traceback information
        conn_empty.rollback()        
        raise e
    finally:                  
        # Close connections
        conn_empty.close()    

def split_words_messages(words):
    # Initialize empty lists for words and messages
    words_list = []
    messages_list = []

    for word in words:
        # Try to split the word by the pipe character "|"
        parts = word.split("|", maxsplit=1)
        
        # Check if the split was successful and has at least two parts
        if len(parts) > 1:
            # The first part is considered the word, the second part is considered the message
            word_part = parts[0]
            message_part = parts[1].strip()  # Remove leading/trailing whitespace
        else:
            # If the split wasn't successful or there's only one part, use the whole word as both word and message
            word_part = word
            message_part = word
        
        # Append the word and message to their respective lists
        words_list.append(word_part)
        messages_list.append(message_part)

    return words_list, messages_list

# Button to trigger processing after files are selected
if st.button('Process Files'):
    if db_file is not None and text_file is not None:

        if not loaded_dependencies:
            with st.spinner("Processing..."):
                from TDutils import *            
                from colour_defs import *
                from word_utils import *
                from db_utils import *
                loaded_dependencies = True

        # Assuming the text file contains one word per line
        words = text_file.getvalue().decode('utf-8-sig').splitlines()      

        # remove leading/trailing space, and remove empties. 
        words = [word.strip() for word in words if word.strip()]
        words.sort(key=str.casefold)

        # remove too-similar duplicates
        words = remove_plural_duplicates(words)        
        words = remove_case_duplicates(words)

        # split messages if present
        messages = None
        if different_labels:
            words, messages = split_words_messages(words)

        words_and_symbols = find_closest_symbol_ids(words, log_expander)
        num_symbols = sum(1 for _, symbol in words_and_symbols if symbol is not None)

    
        st.write(f"{len(words)} words found with { num_symbols } symbols")
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.spb') as tmp_file:
            # Write the uploaded file's content to the temporary file
            tmp_file.write(db_file.getvalue())
            tmp_file_path = tmp_file.name        
        
        add_home_button(tmp_file_path, get_static_path('home_button_ref.spb'))

        # Add all alphabetised and colorised buttons        
        add_words_alphabetised(tmp_file_path, words_and_symbols, messages)

        # Update the page title
        if update_title:
            update_page_title(tmp_file_path, file_name_input)

        # Update timestamps to make sure changes are registered
        update_timestamps(tmp_file_path)

        # After processing, read the modified database into a buffer for download
        with open(tmp_file_path, "rb") as f:
            db_data = f.read()
        
        # Clean up: Delete the temporary file
        os.unlink(tmp_file_path)
        
        # Make the modified database available for download
        dl_filename = "modified.spb"
        if update_title:
            dl_filename = file_name_input + ".spb"

        st.download_button(label="Download Modified Database", data=db_data, file_name=dl_filename, mime="application/x-sqlite3")
    else:
        st.error('Please upload empty file and wordlist before processing.')
