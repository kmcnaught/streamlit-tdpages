import sqlite3
import uuid
import os
import shutil


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
    

def add_button(fname, pageId, label, elementId, elementRefId, position):

    connection = sqlite3.connect(fname)
    crsr = connection.cursor()    

    try: 
        # Add button 
        
        cmd = f"""INSERT INTO Button 
          (Id, Label, ImageOwnership, BorderColor, BorderThickness, LabelOwnership, CommandFlags, ContentType, UniqueId, ElementReferenceId, ActiveContentType, LibrarySymbolId, PageSetImageId, SymbolColorDataId, MessageRecordingId) 
          VALUES 
          ({elementId}, '{label}', '0', '-132102', '0.0', '3', '8', '6', '{str(uuid.uuid1())}', {elementRefId}, '0', '0', '0', '0', '0')"""

        print(cmd)   
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
    MaxId = int(res.fetchone()[0])
    
    res = crsr.execute("SELECT MAX(ElementReferenceId) as max_items FROM Button")
    MaxRefId = int(res.fetchone()[0])

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
    available_positions = find_available_positions(fname, ncols, nrows)

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
    available_positions = find_available_positions(new_fname, ncols, nrows)

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


def find_available_positions(db_filename, ncols, nrows):
    
    # Generate all possible positions
    all_positions = [(c, r) for r in range(nrows) for c in range(ncols)]
    
    # Connect to DB and fetch occupied positions
    conn = sqlite3.connect(db_filename)
    cursor = conn.cursor()
    cursor.execute("SELECT GridPosition FROM ElementPlacement;")
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
    