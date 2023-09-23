# Use an official Python runtime as the base image
FROM python:3.11.5-alpine3.17

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install the required packages
RUN pip install --no-cache-dir beautifulsoup4
RUN pip install requests

# Define the command to run your script
CMD ["python", "-u", "./scraper.py"]