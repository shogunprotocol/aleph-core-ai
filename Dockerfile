FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
ENV PORT=8080
CMD ["langserve", "start", "app.api:rebalance_chain", "--host", "0.0.0.0", "--port", "8080"] 