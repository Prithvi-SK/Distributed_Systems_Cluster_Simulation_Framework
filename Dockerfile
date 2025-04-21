FROM python:3.9-slim
COPY node.py /app/node.py
WORKDIR /app
RUN pip install requests
ENTRYPOINT ["python", "node.py"]