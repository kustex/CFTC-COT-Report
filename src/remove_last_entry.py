import sqlite3

'''
THIS SCRIPT IS SOLELY FOR DEBUGGING PURPOSES

'''


def print_table_contents(cursor):
    """Print all contents of the zip_files table."""
    cursor.execute("SELECT * FROM zip_files")
    rows = cursor.fetchall()
    if rows:
        print("Current contents of zip_files table:")
        for row in rows:
            print(row)
    else:
        print("The zip_files table is empty.")

def remove_last_entry(db_name='cftc_data.db'):
    """Remove the last entry from the zip_files table in the database."""
    try:
        # Connect to the database
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # Print table contents before removal
        print("Before deletion:")
        print_table_contents(cursor)

        # Get the latest entry (last row based on the primary key 'year')
        cursor.execute("SELECT * FROM zip_files ORDER BY year DESC LIMIT 1")
        last_entry = cursor.fetchone()

        if last_entry:
            # Extract the year (primary key) from the last entry
            year_to_delete = last_entry[0]
            print(f"\nLast entry found: {last_entry}. Deleting entry for year: {year_to_delete}")

            # Delete the last entry
            cursor.execute("DELETE FROM zip_files WHERE year = ?", (year_to_delete,))
            conn.commit()

            print(f"Successfully removed the last entry: {year_to_delete}")
        else:
            print("No entries found in the zip_files table.")

        # Print table contents after removal
        print("\nAfter deletion:")
        print_table_contents(cursor)

    except sqlite3.Error as e:
        print(f"An error occurred while accessing the database: {e}")

    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    remove_last_entry()
