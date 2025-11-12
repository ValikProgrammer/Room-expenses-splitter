FROM python:3.11
# Our base image, Debian (Linux) with installed Python
WORKDIR /app
# Set /app as workdir
COPY . /app
# Copy files from . (local) to /app (in image)
RUN pip install --no-cache-dir -r requirements.txt
# you want to execute in image
# you can use several RUN
# example: RUN pip install -r requirements.txt
# CMD <command>
# Specifies the default command to be executed
# when the container starts.
# Can be replaced by passing command in docker run
# example: CMD ["python", "server.py"]m
CMD ["python", "server.py"]
