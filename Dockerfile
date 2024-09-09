# Step 1: Use the Python 3.12 base image
FROM python:3.12-slim

# Step 2: Set the working directory
WORKDIR /app

# Step 3: Copy the current directory contents into the container
COPY . /app

# Step 4: Create a virtual environment and install dependencies
RUN python3.12 -m venv venv
RUN ./venv/bin/pip install --upgrade pip && ./venv/bin/pip install -r requirements.txt

# Step 5: Expose port 80 to allow external traffic to reach the app
EXPOSE 80

# Step 6: Specify the command to run the app with gunicorn, listening on port 80
CMD ["./venv/bin/gunicorn", "--bind", "0.0.0.0:80", "app:app"]
