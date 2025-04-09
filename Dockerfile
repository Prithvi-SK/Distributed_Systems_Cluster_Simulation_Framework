FROM python:3.9
WORKDIR /app
COPY node.py .
RUN pip install requests
ENTRYPOINT ["python", "node.py"]