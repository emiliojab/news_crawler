#!/bin/bash
echo "Starting scrapyrt from entrypoint"
nohup scrapyrt -S news_crawler.settings &> scraprt_logs.log &
echo "Starting gunicorn from entrypoint"
gunicorn --bind 0.0.0.0:5000 wsgi:app
echo "Both server started"
exec "$@"