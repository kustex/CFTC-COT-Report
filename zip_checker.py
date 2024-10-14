import os
import requests
import sqlite3
import shutil
import stat
from datetime import datetime
import zipfile

class CFTCDataDownloader:
    """Class to manage downloading and extracting CFTC data zip files."""

    def __init__(self, db_name='cftc_data.db', data_dir='cftc_data', xls_data_dir='xls_data'):
        self.db_name = db_name
        self.data_dir = data_dir
        self.xls_data_dir = xls_data_dir
        self.setup_database()

        # Create directories if they don't exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.xls_data_dir, exist_ok=True)

    def ensure_file_permissions(self, file_path):
        """Ensure the file has the necessary permissions for renaming."""
        try:
            os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)  # rw-r--r--
        except PermissionError as e:
            print(f"Failed to set permissions on {file_path}: {e}")

    def setup_database(self):
        """Create the database and the necessary table if it doesn't exist."""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS zip_files (
                year INTEGER PRIMARY KEY,
                last_modified TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def get_last_modified(self, year):
        """Get the last modified date for the zip file from the server."""
        url = f'https://www.cftc.gov/files/dea/history/dea_com_xls_{year}.zip'
        response = requests.get(url, stream=True)
        return response.headers.get('Last-Modified')

    def download_and_extract_zip(self, url, year):
        zip_file_path = os.path.join(self.data_dir, f'dea_com_xls_{year}.zip')
        response = requests.get(url, stream=True)
        with open(zip_file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=512):
                if chunk:
                    f.write(chunk)

        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(self.xls_data_dir)
            list_of_file_names = zip_ref.namelist()
            file_name = list_of_file_names[0]  # Assuming there's only one file

            extracted_file_path = os.path.join(self.xls_data_dir, file_name)
            new_file_path = os.path.join(self.xls_data_dir, f'{year}.xls')

            # Delete the old file if it exists before renaming
            if os.path.exists(new_file_path):
                try:
                    os.remove(new_file_path)
                except PermissionError as e:
                    print(f"Could not delete {new_file_path}: {e}")
                    return

            try:
                shutil.move(extracted_file_path, new_file_path)  # Use shutil.move for better safety
                print(f"Renamed extracted file to: {new_file_path}")
            except PermissionError as e:
                print(f"Error renaming file {extracted_file_path} to {new_file_path}: {e}")

    def update_zip_file(self, year, last_modified):
        """Update the last modified date of the zip file in the database."""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute('''
            INSERT INTO zip_files (year, last_modified) VALUES (?, ?)
            ON CONFLICT(year) DO UPDATE SET last_modified = ?
        ''', (year, last_modified, last_modified))
        conn.commit()
        conn.close()

    def check_and_update_zip_files(self):
        """Check for updates and download new zip files if available."""
        years = [2020, 2021, 2022, 2023, 2024]

        for year in years:
            # Check the last modified date of the online zip file
            last_modified = self.get_last_modified(year)

            # Skip the year if no last-modified header is found
            if last_modified is None:
                print(f"No 'Last-Modified' header for {year}.zip, skipping...")
                continue

            try:
                current_date = datetime.strptime(last_modified, '%a, %d %b %Y %H:%M:%S %Z')
            except ValueError:
                print(f"Could not parse 'Last-Modified' date for {year}.zip, skipping...")
                continue

            # Check if the file is already in the database
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute('SELECT last_modified FROM zip_files WHERE year = ?', (year,))
            row = c.fetchone()
            conn.close()

            if row:
                db_last_modified = datetime.strptime(row[0], '%a, %d %b %Y %H:%M:%S %Z')
                # If the database entry is older, download the new zip file
                if current_date > db_last_modified:
                    print(f'Updating: {year}.zip')
                    self.download_and_extract_zip(f'https://www.cftc.gov/files/dea/history/dea_com_xls_{year}.zip', year)
                    self.update_zip_file(year, last_modified)
                else:
                    print(f'No update needed for {year}.zip')
            else:
                # If not in the database, download it
                print(f'Downloading: {year}.zip')
                self.download_and_extract_zip(f'https://www.cftc.gov/files/dea/history/dea_com_xls_{year}.zip', year)
                self.update_zip_file(year, last_modified)

# # Example usage:
# if __name__ == '__main__':
#     downloader = CFTCDataDownloader()
#     downloader.check_and_update_zip_files()


