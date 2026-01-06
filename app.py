from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
from transformers import pipeline 
import json

# app = Flask(__name__)

# @app.route("/main", methods = ["GET"])
# def main():
#     return jsonify(message= "This is our main page")



 
def get_transcript(videoID):
    text = []
    yt_api = YouTubeTranscriptApi()
    fetchedTranscript = yt_api.fetch(videoID)
    for snippet in fetchedTranscript:
        text.append(snippet.text)
    transcript = " ".join(text)
    return transcript


print(get_transcript("O1pL5Anel80"))







