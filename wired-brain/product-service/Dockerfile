# Set base image (hose OS)
FROM python

# Set the working directory in the container.
WORKDIR /code

# Copy dependencies file to the working directory.
COPY requirements.txt .

# Install dependencies.
RUN pip install -r requirements.txt

# Copy the content of the local src directory to the working directory
COPY src/ .

# Command to run on the container when it starts
CMD [ "python", "./app.py" ]
