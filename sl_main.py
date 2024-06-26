import streamlit as st
import pandas as pd
from io import BytesIO
import sqlite3
import tempfile
import os
from TDutils import *
#from jupyter_utils import *
from colour_defs import *
from word_utils import *
from db_utils import *

# Streamlit UI
st.title('TD Snap pageset creation')

# File uploader for the database file
db_file = st.file_uploader("Choose a blank TD Pageset to use", type=['spb'])
    
# File uploader for the text file containing words
text_file = st.file_uploader("Choose a Text File with Word List", type=['txt'])

# Create a checkbox that defaults to True
update_title = st.checkbox('Update title', value=True)

# Check if a file has been uploaded
if text_file is not None and update_title:
    # Extract the file name without extension
    file_name, file_extension = os.path.splitext(text_file.name)
    
    # Display the filename in a text input field, pre-filled with the file name (without extension)
    file_name_input = st.text_input("New pageset name:", value=file_name)    

def add_words_alphabetised(db_empty_path, words_and_symbols, include_letter_cells=True):
    
    try:
        pageId, (num_columns, num_rows) = get_page_layout_details(db_empty_path)
        available_positions = find_available_positions(db_empty_path, pageId, num_columns, num_rows) 
                
        # Retrieve the highest IDs for adding
        # FIXME: maybe this is better done from sqlite_sequence?
        max_id_empty, max_ref_id_empty = get_highest_button_id(db_empty_path)        
        
        # Calculate the starting IDs for new entries in db_empty
        next_id = max_id_empty + 1
        next_ref_id = max_ref_id_empty + 1
        
        # Connect to db_empty for insertions
        conn_empty = sqlite3.connect(db_empty_path)
        cursor_empty = conn_empty.cursor()
    
        letter_colors, letter_symbols = get_letter_colours_symbols()

        # Make sure words are alphabetised
        words_and_symbols = sorted(words_and_symbols, key=lambda x: x[0].lower())     

        pos_i = 0 # keep track of available positions
        current_letter = None

        for i, (word, symbol) in enumerate(words_and_symbols):            
            if i >= len(available_positions):
                print("Error: Ran out of available positions after adding", i, "buttons.")
                break                      
            
            letter = word[0].lower()
            
            #########################################################
            # Optionally add a letter cell for each starting letter #
            #########################################################
                
            if include_letter_cells:
                if letter != current_letter:
                    current_letter = letter 
                    
                    # Add an action-less button for this letter                    
                    add_button(cursor_empty, next_id, next_ref_id, None, letter_symbols[current_letter])
                    add_command_nothing(cursor_empty, next_id)
                    add_element_reference_with_color(cursor_empty, current_letter, pageId, next_ref_id)
                    add_button_placement(cursor_empty, pageId, next_ref_id, available_positions[pos_i])

                    next_id += 1
                    next_ref_id += 1  
                    pos_i += 1

            #########################################
            # Now add a button for the current word #   
            #########################################

            add_button(cursor_empty, next_id, next_ref_id, word, symbol)
            add_command_speak_message(cursor_empty, next_id)
            add_element_reference_with_color(cursor_empty, word, pageId, next_ref_id)
            add_button_placement(cursor_empty, pageId, next_ref_id, available_positions[pos_i])

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

# Button to trigger processing after files are selected
if st.button('Process Files'):
    if db_file is not None and text_file is not None:
        # Assuming the text file contains one word per line
        words = text_file.getvalue().decode('utf-8-sig').splitlines()      
        words = remove_plural_duplicates(words)
        words.sort(key=str.casefold)
        words_and_symbols = find_symbol_ids(words)
        num_symbols = sum(1 for _, symbol in words_and_symbols if symbol is not None)

        # Example processing: printing the words
        st.write(f"{len(words)} words found with { num_symbols } symbols")
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.spb') as tmp_file:
            # Write the uploaded file's content to the temporary file
            tmp_file.write(db_file.getvalue())
            tmp_file_path = tmp_file.name        

        add_home_button(tmp_file_path, get_static_path('home_button_ref.spb'))

        # Add all alphabetised and colorised buttons        
        add_words_alphabetised(tmp_file_path, words_and_symbols)

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
