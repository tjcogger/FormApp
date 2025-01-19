# -*- coding: utf-8 -*-
"""
Created on Sat Jan 18 20:04:21 2025

@author: Thomas
"""

from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    # This tells Flask to look in the "templates" folder for "home.html"
    return render_template('home.html')

if __name__ == '__main__':
    # Start the Flask development server
    app.run(debug=True)

