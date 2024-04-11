
import sqlite3

def get_column_names(cursor, table_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [info[1] for info in cursor.fetchall() if "Id" not in info[1] and "Timestamp" not in info[1]]

def tables_equivalent(cursor, table_name, verbose=False):

    columns = get_column_names(cursor, table_name)
    if not columns:  # If there are no columns to compare, skip this table
        if verbose:            
            print(f"Skipping table {table_name} as it has no columns to compare.")
        return True
    
    columns_list = ', '.join(columns)  # Create a string of column names to include in SELECT
    
    # Compare data in both directions to find differences, excluding "Id" columns
    query1 = f"SELECT {columns_list} FROM main.{table_name} EXCEPT SELECT {columns_list} FROM attached.{table_name};"
    query2 = f"SELECT {columns_list} FROM attached.{table_name} EXCEPT SELECT {columns_list} FROM main.{table_name};"
    
    cursor.execute(query1)
    differences1 = cursor.fetchall()
    
    cursor.execute(query2)
    differences2 = cursor.fetchall()
    
    if differences1 or differences2:
        if verbose:
            print(f"Differences found in table {table_name}:")        
        if differences1:
            if verbose:
                print(f"Rows in db1 not in db2: {differences1}")
        if differences2:
            if verbose:
                print(f"Rows in db2 not in db1: {differences2}")
        
        return False
    else:
        if verbose:
            print(f"No differences found in table {table_name}.")
        return True        

def databases_equivalent(db_path1, db_path2, verbose=False):
    conn = sqlite3.connect(db_path1)
    cursor = conn.cursor()
    
    cursor.execute(f"ATTACH DATABASE '{db_path2}' AS attached")
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [table[0] for table in cursor.fetchall()]
    equivalent = True
    
    for table_name in tables:
        table_equivalent = tables_equivalent(cursor, table_name, verbose)
        equivalent = equivalent and table_equivalent
    
    cursor.execute("DETACH DATABASE 'attached'")
    conn.close()
    
    return equivalent
    
