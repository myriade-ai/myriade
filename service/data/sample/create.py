"""
Create sqlite database from sample.sql
"""

import os
import sqlite3

# Get the directory of the current script
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

# Absolute path to the .sql file (same folder as this file)
SQL_PATH = os.path.join(SCRIPT_DIR, "sample.sql")
SQLITE_PATH = os.path.join(SCRIPT_DIR, "sample.sqlite")


def create_database_from_sql_file(sql_file_path, db_name):
    # Check if sql file exists
    if not os.path.isfile(sql_file_path):
        print(f"File {sql_file_path} does not exist.")
        return

    # Connect to SQLite database
    conn = sqlite3.connect(db_name)

    # Open and read the file as a single buffer
    fd = open(sql_file_path, "r")
    sql_file = fd.read()
    fd.close()

    # all SQL commands (split on ';')
    sql_commands = sql_file.split(";")

    # Execute every command from the input file
    for command in sql_commands:
        try:
            conn.execute(command)
        except Exception as e:
            print(f"Failed to execute command: {e}")

    # Close connection
    conn.close()


def create_sample_database():
    # Call the function with your .sql file path and desired database name
    create_database_from_sql_file(SQL_PATH, SQLITE_PATH)
    return SQLITE_PATH


def delete_sample_database():
    os.remove(SQLITE_PATH)
