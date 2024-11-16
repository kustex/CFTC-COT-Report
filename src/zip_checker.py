import os
import logging
import requests
import sqlite3
import shutil
import stat
import ssl
import time
import smtplib
import zipfile

from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("log/cftc_downloader.log"),
        logging.StreamHandler()
    ]
)

class CFTCDataDownloader:
    """Class to manage downloading and extracting CFTC data zip files."""

    def __init__(self, db_name='data/cftc_data.db', data_dir='data/cftc_data', xls_data_dir='data/xls_data'):
        self.db_name = db_name
        self.data_dir = data_dir
        self.xls_data_dir = xls_data_dir
        self.latest_update_timestamp = self.get_last_modified(2024) 
        self.setup_database()
        
        # Ensure directories exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.xls_data_dir, exist_ok=True)

    def check_zip_updates(self, sleep_interval=3600):
        """Check for zip updates every hour."""
        while True:
            logging.info("Starting the zip file update check.")
            self.check_and_update_zip_files()
            time.sleep(sleep_interval)  

    def ensure_file_permissions(self, file_path):
        """Ensure the file has the necessary permissions for renaming."""
        try:
            os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)  
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
            file_name = list_of_file_names[0] 

            extracted_file_path = os.path.join(self.xls_data_dir, file_name)
            new_file_path = os.path.join(self.xls_data_dir, f'{year}.xls')

            if os.path.exists(new_file_path):
                try:
                    os.remove(new_file_path)
                except PermissionError as e:
                    print(f"Could not delete {new_file_path}: {e}")
                    return

            try:
                shutil.move(extracted_file_path, new_file_path)  
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

    def send_email_notification(self, updated_years):
        """Send an email notification listing the years with new files downloaded."""
        sender_email = os.environ.get("EMAIL_USER")
        receiver_email = os.environ.get("EMAIL_USER")  
        password = os.environ.get("EMAIL_PASSWORD")
        print(receiver_email, password)

        subject = "New CFTC Zip Files Downloaded"
        body = "The following years had new zip files downloaded:\n\n" + "\n".join(map(str, updated_years))

        # Create a multipart email message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = subject

        # Attach the email body to the message
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        try:
            context = ssl.create_default_context()
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls(context=context)
                server.login(sender_email, password)
                server.sendmail(sender_email, receiver_email, msg.as_string())
            logging.info(f"Email notification successfully sent for updated years: {', '.join(map(str, updated_years))}")
        except Exception as e:
            logging.error(f"Failed to send email notification: {e}")

    def check_and_update_zip_files(self):
        """Check for updates, download new zip files if available, and send email notification for updated years."""
        years = [2020, 2021, 2022, 2023, 2024]
        updated_years = []  

        for year in years:
            last_modified = self.get_last_modified(year)
            if last_modified is None:
                logging.warning(f"No 'Last-Modified' header for {year}.zip, skipping...")
                continue
            try:
                current_date = datetime.strptime(last_modified, '%a, %d %b %Y %H:%M:%S %Z')
            except ValueError:
                logging.error(f"Could not parse 'Last-Modified' date for {year}.zip, skipping...")
                continue

            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute('SELECT last_modified FROM zip_files WHERE year = ?', (year,))
            row = c.fetchone()
            conn.close()

            if row:
                db_last_modified = datetime.strptime(row[0], '%a, %d %b %Y %H:%M:%S %Z')
                if current_date > db_last_modified:
                    logging.info(f'Updating: {year}.zip')
                    self.download_and_extract_zip(f'https://www.cftc.gov/files/dea/history/dea_com_xls_{year}.zip', year)
                    self.update_zip_file(year, last_modified)
                    updated_years.append(year)
                else:
                    logging.info(f'No update needed for {year}.zip')
            else:
                logging.info(f'Downloading: {year}.zip')
                self.download_and_extract_zip(f'https://www.cftc.gov/files/dea/history/dea_com_xls_{year}.zip', year)
                self.update_zip_file(year, last_modified)
                updated_years.append(year)

        if updated_years:
            logging.info(f"Updated years: {', '.join(map(str, updated_years))}")
            self.send_email_notification(updated_years)
        else:
            logging.info("No updates detected for any years.")




