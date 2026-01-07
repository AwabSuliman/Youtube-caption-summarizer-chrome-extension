from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
from transformers import T5ForConditionalGeneration, T5Tokenizer 
import json


model = T5ForConditionalGeneration.from_pretrained("t5-base")
model.eval()
tokenizer = T5Tokenizer.from_pretrained("t5-base")

 
def get_transcript(videoID):
    text = []
    yt_api = YouTubeTranscriptApi()
    fetchedTranscript = yt_api.fetch(videoID)

    for snippet in fetchedTranscript:
        text.append(snippet.text)

    transcript = " ".join(text)
    return transcript


def summarized_transcript(transcript):

    inputs = tokenizer.encode(
        "summarize: " + transcript, 
        return_tensors="pt", 
        max_length=512, 
        truncation=True
    )

    tokens = model.generate(
        inputs, 
        max_length = 150,
        length_penalty = 1.5,
        num_beams = 8,
        early_stopping = True                                                         
    )
    summary = tokenizer.decode(tokens[0], skip_special_tokens=True)

    return summary


app = Flask(__name__)

@app.route("/api/summarize?youtube_url=<url>")
def YT(url):
    YtvideoID = request.args.get("youtube_url")
    transcript = get_transcript(YtvideoID)
    summary = summarized_transcript(transcript)

    try:
        if not YtvideoID:
            return 400
    except:



    return summary, 200


  








