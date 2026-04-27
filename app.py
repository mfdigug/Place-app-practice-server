from flask import Flask, request, jsonify
import requests, os
from dotenv import load_dotenv


load_dotenv()

app = Flask(__name__)
API_KEY = os.ggetenv("GOOGLE_API_KEY")