import streamlit as st
import pandas as pd
from io import BytesIO
from TDutils import add_words_inplace
import sqlite3
import tempfile
import os

# Streamlit UI
st.title('TD Snap pageset tools')

# File uploader for the database file
db_file = st.file_uploader("Choose a TD Pageset", type=['spb'])

# File uploader for the text file containing words
text_file = st.file_uploader("Choose a Text File with Word List", type=['txt'])

# Button to trigger processing after files are selected
if st.button('Process Files'):
    if db_file is not None and text_file is not None:
        # Assuming the text file contains one word per line
        words = text_file.getvalue().decode('utf-8-sig').splitlines()      

        # Example processing: printing the words
        st.write("Words in the uploaded text file:")
        st.write(words)
        st.write(f"first word was {words[0]}")
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.spb') as tmp_file:
            # Write the uploaded file's content to the temporary file
            tmp_file.write(db_file.getvalue())
            tmp_file_path = tmp_file.name
        
        # Call the add_words function with the hardcoded file path and tuple of words
        add_words_inplace(tmp_file_path, words)
        
        # After processing, read the modified database into a buffer for download
        with open(tmp_file_path, "rb") as f:
            db_data = f.read()
        
        # Clean up: Delete the temporary file
        os.unlink(tmp_file_path)
        
        # Make the modified database available for download
        st.download_button(label="Download Modified Database", data=db_data, file_name="modified.spb", mime="application/x-sqlite3")
    else:
        st.error('Please upload both files before processing.')
