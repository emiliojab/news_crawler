""" Used with gunicorn to serve the flask application app.py
"""
from app import app

if __name__ == "__main__":
    app.run(debug=True)
