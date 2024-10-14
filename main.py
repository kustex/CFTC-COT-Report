import os
import multiprocessing
import time
import sys
import smtplib
import ssl

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from zip_checker import CFTCDataDownloader


def send_email_notification(new_files):
    # Set up the email details from environment variables
    sender_email = os.environ.get("EMAIL_USER")  # GitHub Secret
    receiver_email = os.environ.get("EMAIL_USER")  # Assuming you are sending to yourself
    password = os.environ.get("EMAIL_PASSWORD")  # GitHub Secret
    subject = "New Zip Files Downloaded"
    body = f"The following new zip files have been downloaded:\n\n" + "\n".join(new_files)

    # Create a multipart email message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    # Attach the email body to the message
    msg.attach(MIMEText(body, 'plain'))

    # Send the email
    context = ssl.create_default_context()
    with smtplib.SMTP("smtp.office365.com", 587) as server: 
        server.starttls(context=context)
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())

def check_zip_updates(data_downloader):
    while True:
        try:
            new_files = data_downloader.check_and_update_zip_files()  # Use the class method and get new files
            if new_files:  # If there are new files
                send_email_notification(new_files)
            time.sleep(3600)  # Sleep for 1 hour before checking again
        except Exception as e:
            print(f"Error while checking zip updates: {e}", file=sys.stderr)

if __name__ == "__main__":
    # Create an instance of CFTCDataDownloader to manage zip file updates
    data_downloader = CFTCDataDownloader()

    # Run the zip checker first to ensure files are downloaded
    data_downloader.check_and_update_zip_files()
    
    # Now import app_cftc after the zip files have been checked/updated
    from app_cftc import app

    # Start the zip checker in a separate process for continuous checking
    zip_process = multiprocessing.Process(target=check_zip_updates, args=(data_downloader,))
    zip_process.start()

    try:
        # Run the Dash app
        app.run_server(host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        print("Keyboard interrupt received, terminating processes...")
    finally:
        zip_process.terminate()  # Ensure the subprocess is properly terminated
        zip_process.join()  # Wait for the subprocess to cleanly exit
        print("Process terminated, exiting...")

