# Use Python base image
FROM python:3.11-slim

# Set working directory in container
WORKDIR /app

# Copy requirements and install dependencies
COPY requirement.txt ./
RUN pip install --no-cache-dir -r requirement.txt

# Copy the rest of the app
COPY . .

# Expose the port the app runs on
EXPOSE 5000

# Command to run the app
CMD ["python", "app.py"]