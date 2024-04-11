import sqlite3
import uuid
import os
import shutil
import re
import datetime
import sqlite3
import re
from word_utils import *
from colour_defs import *
import streamlit as st

def merge_two_dicts(x, y):
    z = x.copy()   # start with keys and values of x
    z.update(y)    # modifies z with keys and values of y
    return z

def remove_content(db_path):
    # Remove everything except a "Home" button in the top left. 
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Fetch Label and ElementReferenceId from Button
        cursor.execute("SELECT Id, Label, ElementReferenceId FROM Button")
        buttons = cursor.fetchall()
        
        for Id, label, element_ref_id in buttons:
            if Id <= 2 and label == "Home":
                continue;
                
            # Remove element reference entry
            cursor.execute(f"DELETE FROM ElementReference WHERE Id = {element_ref_id};")
            cursor.execute(f"DELETE FROM ElementPlacement WHERE Id = {element_ref_id};")
            
            # Remove command sequence entry (this is based on button ID not reference ID)
            cursor.execute(f"DELETE FROM CommandSequence WHERE ButtonId = {Id};")                        

            # Remove button itself
            cursor.execute(f"DELETE FROM Button WHERE Id = {Id};")                        
            
#         # Commit the changes to make them persistent
            conn.commit()

    finally:
        # Close the cursor and the connection to the database
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        print("The SQLite connection is closed.")
    
    

def create_temp_file(filename):
    # Extract the directory, base name, and extension of the file
    dir_path, base_name = os.path.split(filename)
    name, extension = os.path.splitext(base_name)
    
    # Define the temp folder path
    temp_folder = os.path.join(dir_path, 'temp')
    
    # Create the temp folder if it doesn't exist
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)
    
    # Generate a new filename with a timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    new_filename = f"{name}_{timestamp}{extension}"
    
    # Copy the file to the temp folder with the new filename
    new_file_path = os.path.join(temp_folder, new_filename)
    shutil.copy2(filename, new_file_path)
    
    # Return the new filename
    return new_file_path


def make_empty_db(filename):
    # Make a copy of a DB, stripping out the content
    # This lets us copy from one to another with the end result appearing as
    # an "in-place" edit (i.e. using all the same page set properties)
    new_fname = create_temp_file(filename)
    remove_content(new_fname)
    return new_fname

def update_background_color(new_color, database):
    """
    Update the BackgroundColor column in the ElementReference table.

    Args:
    - new_color: The new color value to be set.
    - database: The SQLite database file. Defaults to 'your_database.db'.
    """
    try:
        conn = sqlite3.connect(database)
        cursor = conn.cursor()
        
        update_query = """UPDATE ElementReference SET BackgroundColor = ?"""
        cursor.execute(update_query, (new_color,))
        
        # Commit the changes to the database
        conn.commit()
        print("BackgroundColor updated successfully.")
    except sqlite3.Error as error:
        print("Failed to update BackgroundColor in the SQLite table", error)
    finally:
        # Ensure the database connection is closed even if an error occurs
        if conn:            
            conn.commit()
            conn.close()
            print("The SQLite connection is closed.")


def alternate_column_colors(db_path, column_colors):
    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Fetch GridPosition and ElementReferenceId from ElementPlacement
    cursor.execute("SELECT GridPosition, ElementReferenceId FROM ElementPlacement")
    placements = cursor.fetchall()
    
    # Dictionary to hold the new color for each ElementReferenceId
    color_updates = {}
    
    for position, element_ref_id in placements:
        # Split GridPosition to get column number (assuming "column,row")
        column = int(position.split(',')[0])
        
        # Determine color based on column (cycle through column_colors)
        color = column_colors[column % len(column_colors)]
        
        # Prepare update dictionary
        color_updates[element_ref_id] = color
    
    # Update ElementReference with new colors
    for element_ref_id, color in color_updates.items():
        cursor.execute("UPDATE ElementReference SET BackgroundColor = ? WHERE Id = ?",
                       (color, element_ref_id))
    
    # Commit the changes and close the connection
    conn.commit()
    conn.close()

def add_button_placement(cursor, pageId, elementRefId, position):
    c, r = position
    cmd = f"""INSERT INTO ElementPlacement 
                (GridPosition, GridSpan, Visible, ElementReferenceId, PageLayoutId) 
                VALUES ('{c},{r}', '1,1', '1', '{elementRefId}', '{pageId}')
                """
    cursor.execute(cmd)

def add_button(fname, pageId, label, elementId, elementRefId, position):

    connection = sqlite3.connect(fname)
    crsr = connection.cursor()    

    try: 
        # Add button         
        cmd = f"""INSERT INTO Button 
          (Id, Label, ImageOwnership, BorderColor, BorderThickness, LabelOwnership, CommandFlags, ContentType, UniqueId, ElementReferenceId, ActiveContentType, LibrarySymbolId, PageSetImageId, SymbolColorDataId, MessageRecordingId) 
          VALUES 
          ({elementId}, '{label}', '0', '-132102', '0.0', '3', '8', '6', '{str(uuid.uuid1())}', {elementRefId}, '0', '0', '0', '0', '0')"""

        #print(cmd)   
        crsr.execute(cmd)

        # Add associated command sequence
        content = '\'{"$type":"1","$values":[{"$type":"3","MessageAction":0}]}\'' # this means "speak message" action
        cmd = f"""
        INSERT INTO CommandSequence (SerializedCommands, ButtonId)
        VALUES ({content}, "{elementId}")
        """
        crsr.execute(cmd)
        
        # Add position      
        c, r = position
        
        cmd = f"""INSERT INTO ElementPlacement 
            (GridPosition, GridSpan, Visible, ElementReferenceId, PageLayoutId) 
            VALUES ('{c},{r}', '1,1', '1', '{elementRefId}', '{pageId}')
            """
        crsr.execute(cmd)

        # Add entry to ElementReference
        cmd = f"""
            INSERT INTO ElementReference 
            (Id, ElementType, ForegroundColor, BackgroundColor, AudioCueRecordingId, PageId) 
            VALUES ('{elementRefId}', '0', '-14934754', '-132102', '0', '{pageId}')
            """
        crsr.execute(cmd)

    except Exception as e:
        print("The error raised is: ", e)
        
    finally:
        # Ensure the database connection is closed even if an error occurs
        if connection:            
            connection.commit()
            connection.close()
            print("The SQLite connection is closed.")

def get_highest_button_id(fname):
    connection = sqlite3.connect(fname)
    crsr = connection.cursor()
    
    res = crsr.execute("SELECT MAX(Id) as max_items FROM Button")
    MaxId = int(res.fetchone()[0] or 0)
    
    res = crsr.execute("SELECT MAX(ElementReferenceId) as max_items FROM Button")
    MaxRefId = int(res.fetchone()[0] or 0)

    connection.close()
    
    # Id, ElementReferenceId
    return MaxId, MaxRefId

def increment_filename(filename):
    path, name_ext = os.path.split(filename)
    name, ext = os.path.splitext(name_ext)
    
    i = 1
    new_filename = os.path.join(path, f"{name}{i}{ext}")
    
    while os.path.exists(new_filename):
        i += 1
        new_filename = os.path.join(path, f"{name}{i}{ext}")
    
    return new_filename


def add_words_inplace(fname, word_list):

    maxId, maxRefId= get_highest_button_id(fname)
    
    maxId += 1
    maxRefId += 1

    pageId, (ncols, nrows) = get_page_layout_details(fname)
    available_positions = find_available_positions(fname, pageId, ncols, nrows)

    for i, word in enumerate(word_list):
        if i < len(available_positions):
            add_button(fname, pageId, word, maxId, maxRefId, available_positions[i])
            maxId += 1
            maxRefId += 1
        else:
            print("Error: Ran out of available positions after adding", i, "buttons.")
            break

    return fname

def add_words(fname, word_list):

    new_fname = increment_filename(fname)
    shutil.copyfile(fname, new_fname)
    
    maxId, maxRefId= get_highest_button_id(fname)

    maxId += 1
    maxRefId += 1

    pageId, (ncols, nrows) = get_page_layout_details(new_fname)
    available_positions = find_available_positions(new_fname, pageId, ncols, nrows)

    for i, word in enumerate(word_list):
        if i < len(available_positions):
            add_button(new_fname, pageId, word, maxId, maxRefId, available_positions[i])
            maxId += 1
            maxRefId += 1
        else:
            print("Error: Ran out of available positions after adding", i, "buttons.")
            break

    return new_fname


def get_page_layout_details(db_filename):    
    
    conn = sqlite3.connect(db_filename)
    cursor = conn.cursor()
    
    # Select rows from Page table excluding ignored titles
    rows_to_ignore = ['Dashboard', 'Message Bar'] # standard "Page"s
    query = "SELECT Id, Title FROM Page WHERE Title NOT IN ({})".format(','.join('?' for _ in rows_to_ignore))
    cursor.execute(query, rows_to_ignore)
    rows = cursor.fetchall()

    if len(rows) == 0:
        print("Error: Couldn't find Page row")
        return None, None
    if len(rows) != 1:
        error_message = 'Error: Found multiple novel Titles: ' + ', '.join(row[1] for row in rows)
        print(error_message)
        return None, None
    else:
        pageId = rows[0][0]

    # Retrieve PageLayoutSetting for the unique Id
    cursor.execute("SELECT PageLayoutSetting FROM PageLayout WHERE Id = ?", (pageId,))
    setting = cursor.fetchone()[0]

    # Extract num_columns and num_rows from PageLayoutSetting
    num_columns, num_rows = map(int, setting.split(',')[:2])

    conn.close()
    
    return pageId, (num_columns, num_rows)

def find_available_positions(db_filename, pageId, ncols, nrows):
    
    # Generate all possible positions
    npages = 3 
    all_positions = [
            (c, r) for r in range(nrows * npages) for c in range(ncols)
            if not (
            # Exclude bottom right of any page
            (c == ncols - 1 and r % nrows == nrows - 1) or
            # Exclude top right of any page except the first one
            (c == ncols - 1 and r % nrows == 0 and r != 0)
        )    
    ]
    
    # Connect to DB and fetch occupied positions
    conn = sqlite3.connect(db_filename)
    cursor = conn.cursor()
    cursor.execute("SELECT GridPosition FROM ElementPlacement WHERE PageLayoutId = ?", (pageId,))
    occupied_positions_raw = cursor.fetchall()
        
    # Parse 'r, c' format and convert to list of tuples
    occupied_positions = []
    for pos_raw in occupied_positions_raw:
        r, c = map(int, pos_raw[0].split(','))
        occupied_positions.append((r, c))
    
    # Filter out occupied positions
    available_positions = [pos for pos in all_positions if pos not in occupied_positions]
    
    # Close DB connection
    conn.close()
    
    return available_positions    

def int_to_rgb(value):
    if not type(value) is int:
        value = int(value)
        
    # Convert to a 32-bit binary representation, stripping the '0b' prefix and padding with zeros
    binary_str = format(value & 0xFFFFFFFF, '032b')
    # Extract the RGB portions (ignoring the alpha channel)
    r = int(binary_str[8:16], 2)
    g = int(binary_str[16:24], 2)
    b = int(binary_str[24:32], 2)
    return (r, g, b)
    
def rgb_to_int(r, g, b, a=255):
    # Ensure the values are within the 0-255 range
    r = max(0, min(r, 255))
    g = max(0, min(g, 255))
    b = max(0, min(b, 255))
    a = max(0, min(a, 255))
    
    # Combine the RGBA values into a single 32-bit integer
    # Shift the bits left and use bitwise OR to combine them
    value = (a << 24) | (r << 16) | (g << 8) | b
    
    # Convert to a signed 32-bit integer
    # If the highest bit (bit 31) is set, the number is negative in two's complement
    # This checks if bit 31 is set and adjusts the value accordingly
    if value & (1 << 31):
        value = value - (1 << 32)
    
    return value

# Extract words pasted from notes -
# words are surrounded by single asterisk. 
# definitions (when present) follow after a colon
# strip out any links (surrounded by double asterisk)

def extract_words(filename):
    terms_without_definitions, terms_with_definitions = extract_definitions(filename)
    words_with_definitions = list(terms_with_definitions.keys())
    combined_words_list = terms_without_definitions + words_with_definitions
    return combined_words_list
    
def extract_definitions(filename):
    # Compile the regex patterns
    link_pattern = re.compile(r'\*\*.*?\*\*')
    term_only_pattern = re.compile(r'^\s*-?\s*\*(.+?)\*\s*$', re.MULTILINE)
    term_with_definition_pattern = re.compile(r'^\s*-?\s*\*(.+?)\*\s*:\s*(.+)$', re.MULTILINE)

    # Read the file content
    with open(filename, 'r', encoding='utf-8') as file:
        content = file.read()

    # Step 1: Remove all links
    content_no_links = re.sub(link_pattern, '', content)

    # Step 2: Find all lines with just a word/phrase and no definition
    terms_without_definitions = term_only_pattern.findall(content_no_links)

    # Step 3: Remove the lines that matched in step 2 from the content
    content_no_terms_only = re.sub(term_only_pattern, '', content_no_links)

    # Step 4: Match words/phrases with definitions in the remaining text
    terms_with_definitions = dict(term_with_definition_pattern.findall(content_no_terms_only))

    return terms_without_definitions, terms_with_definitions


import sqlite3

def get_timestamp():
    return dt_to_filetime(datetime.datetime.now())    

def get_hash():
    # Placeholder function to get a new hash
    # Replace this with your actual logic to get a new hash
    return "new_hash"

# note that there appear to be small floating point errors in the following functions,
# if you chain them you won't get quite back to where you started. But we're just using
# them for approximate timestamps so I think it's okay. 

def filetime_to_dt(filetime):
    # FILETIME is the number of 100-nanosecond intervals since start of calendar
    # Convert it to a datetime object.
    return datetime.datetime(1, 1, 1) + datetime.timedelta(microseconds=filetime // 10)

def dt_to_filetime(dt):
    delta = dt - datetime.datetime(1, 1, 1)
    # Convert the difference to 100-nanosecond intervals
    filetime = int(delta.total_seconds() * 10**7)
    return filetime

def get_timestamp():
    return dt_to_filetime(datetime.datetime.now())    

# For a pageset, update all the synchronisation timestamps to "now"
def update_timestamps(filename):
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(filename)
        cursor = conn.cursor()
        
        # Update the Page table
        new_timestamp = get_timestamp()
        new_hash = get_hash()
        cursor.execute("UPDATE Page SET TimeStamp = ?", (new_timestamp, ))
        
        # Update the Synchronization table
        cursor.execute("UPDATE Synchronization SET PageSetTimestamp = ? ", (new_timestamp,))
        
        # Update the PageSetProperties table
        cursor.execute("UPDATE PageSetProperties SET TimeStamp = ? ", (new_timestamp,))
        
        # Commit the changes
        conn.commit()
        
    finally:
        # Close the connection to the database
        if conn:
            conn.close()

def get_static_path(fname):

    fname = os.path.join(os.path.dirname(__file__), 'static/' + fname)
    fname = os.path.abspath(fname)  # Convert to absolute path
    return fname

def find_symbol_ids(words):
    """Find symbol IDs for a list of words."""
    # Connect to the SQLite database

    db_path = get_static_path('symbols.sqlite5')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Prepare the output list
    output = []
    
    # Lambda to lookup a normalised version of a word/phrase in DB
    lookup = lambda w: cursor.execute("SELECT SymbolId FROM FilteredSymbols WHERE Label = ?", (normalize_string(w),)).fetchone()
        
    for word in words:
        
        # Query the database for a matching symbol ID        

        # First with original word
        result = lookup(word)
        
        # Fallback to trying singular/plural
        if not result:
            result = lookup(change_singular_plural(word))
            
        # Or lemmatized root
        if not result:
            result = lookup(get_root(word))
        
        # If a match was found, append the (word, symbolId) tuple to the output list
        if result:    
            output.append((word, result[0]))
        else:
            output.append((word, None))
        
    # Close the database connection
    conn.close()
    
    return output


def add_home_button(pageset_db_filename, reference_db_filename):
    
    # Connect to the pageset database
    conn_pageset = sqlite3.connect(pageset_db_filename)    
    
    try:
        
        # Check if any buttons already exist in the pageset database
        cursor_pageset = conn_pageset.cursor()
        cursor_pageset.execute("SELECT COUNT(*) FROM Button")
        if cursor_pageset.fetchone()[0] > 0:
            print("Error: Buttons already exist in the pageset database. No changes were made.")
            conn_pageset.close()
            return
        
        # Attach the reference database to the pageset database connection
        conn_pageset.execute(f"ATTACH DATABASE '{reference_db_filename}' AS ref_db")

        # Copy the single entries from various tables in the reference database
        conn_pageset.execute("INSERT INTO Button SELECT * FROM ref_db.Button")
        conn_pageset.execute("INSERT INTO ElementReference SELECT * FROM ref_db.ElementReference")
        conn_pageset.execute("INSERT INTO ElementPlacement SELECT * FROM ref_db.ElementPlacement")
        conn_pageset.execute("INSERT INTO CommandSequence SELECT * FROM ref_db.CommandSequence")

        # Commit the changes
        conn_pageset.commit()

        # Detach the reference database
        conn_pageset.execute("DETACH DATABASE ref_db")
    
    finally:
        # Close the pageset database connection
        conn_pageset.close()
        

# Change the background colour of all word keys
def update_colors_by_label_first_letter(db_path):
        
    letter_colors, letter_symbols = get_letter_colours_symbols()
    
    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Fetch Label and ElementReferenceId from Button
    cursor.execute("SELECT Label, ElementReferenceId FROM Button")
    buttons = cursor.fetchall()
    
    # Dictionary to hold the new color for each ElementReferenceId
    color_updates = {}
    
    for label, element_ref_id in buttons:
        if label == "Home" or label == None or len(label) == 0:
            continue

        color = None
        if (len(label) > 1): # try 2-letters, then 1
            color = letter_colors.get(label[0:2].upper(), None)  
        if color == None:
            color = letter_colors.get(label[0].upper(), None)
        if type(color) == tuple:
            color = rgb_to_int(*color)
            
        if color:
            # Prepare update dictionary
            color_updates[element_ref_id] = color
    
    # Update ElementReference with new colors
    for element_ref_id, color in color_updates.items():
        cursor.execute("UPDATE ElementReference SET BackgroundColor = ? WHERE Id = ?",
                       (color, element_ref_id))
    
    # Commit the changes and close the connection
    conn.commit()
    conn.close()
    
    
def add_command_nothing(cursor, buttonId):
    content = '\'{"$type":"1","$values":[]}\'' # this means no action
    
    cmd = f"""
    INSERT INTO CommandSequence (SerializedCommands, ButtonId)
    VALUES ({content}, "{buttonId}")
    """
    cursor.execute(cmd)
    
    
def add_command_speak_message(cursor, buttonId):
    content = '\'{"$type":"1","$values":[{"$type":"3","MessageAction":0}]}\'' # this means "speak message" action
    
    cmd = f"""
            INSERT INTO CommandSequence (SerializedCommands, ButtonId)
            VALUES ({content}, "{buttonId}")
            """
    cursor.execute(cmd)

def add_button(cursor, buttonId, refId, label, symbol):
    
    #i am here - trying to make generic method to use from both places. I think i was a bit inconsistent with the 'ownership' columns
    #tried to fix it, but the images aren't showing up for letter keys
    
    label_ownership = 0 if label is None else 3
    image_ownership = 0 if symbol is None else 3
    
    new_uuid = str(uuid.uuid1())
    cursor.execute("""
                INSERT INTO Button (Id, Label, ImageOwnership, BorderColor, BorderThickness, LabelOwnership, CommandFlags, ContentType, UniqueId, ElementReferenceId, ActiveContentType, LibrarySymbolId, PageSetImageId, SymbolColorDataId, MessageRecordingId)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (buttonId, label, image_ownership, '-132102', 0.0, label_ownership, 8, 6, new_uuid, refId, 0, symbol, 0, 0, 0)    )


def add_element_reference_with_color(cursor, word, pageId, refId):
    letter_colors, letter_symbols = get_letter_colours_symbols()

    # Get appropriate colour per starting letter
    color = letter_colors.get(word[0], None)
    if type(color) == tuple:
        color = rgb_to_int(*color)
    
    if color is None:
        print("Could not find color")
        backgroundColor = '-132102'
    else:
        backgroundColor = color
    
    foregroundColor = '-14934754'
    
    # Add entry to ElementReference 
    cursor.execute("""
        INSERT INTO ElementReference 
        (Id, ElementType, ForegroundColor, BackgroundColor, AudioCueRecordingId, PageId) 
        VALUES (?, ?, ?, ?, ?, ?)
        """, (refId, 0, foregroundColor, backgroundColor, 0, pageId))
