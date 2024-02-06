import streamlit as st
from TDutils import add_words_inplace, alternate_column_colors
import sqlite3
import tempfile
import os

# Streamlit UI
st.title('TD Snap pageset tools')
st.header("Version: 1.0.0")

# File uploader for the database file
db_file = st.file_uploader("Choose a TD Pageset", type=['spb'])

# File uploader for the text file containing words
text_file = st.file_uploader("Choose a Text File with Word List", type=['txt'])

# Radio button for alternating colours
color_option = st.radio(
    "Choose the color alternation option:",
    ('none', 'two', 'three'),
    index=0  # Default to 'none'
)

# Button to trigger processing after files are selected
if st.button('Process File'):
    if db_file is not None and \
       (text_file is not None or color_option is not 'none'):

        # Set up file on server
       
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.spb') as tmp_file:
            # Write the uploaded file's content to the temporary file
            tmp_file.write(db_file.getvalue())
            tmp_file_path = tmp_file.name
        
        if (text_file is not None):
            # Assuming the text file contains one word per line
            words = text_file.getvalue().decode('utf-8-sig').splitlines()      

            # Example processing: printing the words
            st.write("Words in the uploaded text file:")
            st.write(words)        
            
            # Call the add_words function with the hardcoded file path and tuple of words
            add_words_inplace(tmp_file_path, words)
        
        if (color_option is not 'none'):
            
            # Query the selected color option
            # Here you can add your logic based on the selected color option
            st.write(f"Adding {color_option} alternating colours to columns")
                           
            column_colors = [-1643526, -132102, -3019575]      
            if color_option == 'two':
                column_colors = [-1643526, -3019575]
            
            alternate_column_colors(tmp_file_path, column_colors)
            
        # After processing, read the modified database into a buffer for download
        with open(tmp_file_path, "rb") as f:
            db_data = f.read()

        # Clean up: Delete the temporary file
        os.unlink(tmp_file_path)
        
        # Retrieve the original filename of the uploaded database file
        original_db_filename, original_extension = os.path.splitext(db_file.name)
        output_filename = f"{original_db_filename}_modified{original_extension}"
            
        # Make the modified database available for download
        st.download_button(label="Download Modified Database", data=db_data, file_name=output_filename, mime="application/x-sqlite3")
    else:
        st.error('Please upload both files before processing.')
