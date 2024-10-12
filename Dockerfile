# Use an official Python runtime as a parent image
FROM python:3.10.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --upgrade pip &&\
		pip install -r requirements.txt

# Expose the port the app runs on
EXPOSE 80

# Run the app
CMD ["python", "app_cftc.py"]
