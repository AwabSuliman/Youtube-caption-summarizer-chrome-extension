from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
from transformers import T5ForConditionalGeneration, T5Tokenizer 
import json
from urllib.parse import urlparse, parse_qs

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



def getvideoID(url): #test later, if doesn't work try smh splitting and using len to see which has 11 characters.
    parsed = urlparse(url)
    host = parsed.netloc
    path = parsed.path

    if "youtu.be" in host:
        vid = path.split("/")

    elif "youtube.com" in host:
        qs = parse_qs(parsed.query)
        
        if "v" in qs:
            vid = qs["v"][0]

        else:
            parts = path.split("/")
            for p in parts:
                if len(p) == 11:
                    vid = p
                    break
            else:
                return None
    
    else:
        return None
    

    return vid
                




app = Flask(__name__)

@app.route("/api/summarize")
def YT():

    ytURL = request.args.get("youtube_url")

    if not ytURL:
        return "Missing youtube video URL", 400


    try:
        videoID = getvideoID(ytURL)
        if not videoID:
            return "VideoID not available", 400
        
        transcript = get_transcript(videoID)
        if not transcript:
            return "Transcript unavailable", 400
        
        summary = summarized_transcript(transcript)
        if not summary:
            return "Summary failed", 500
        
        return summary, 200
    
    except ValueError:
        return "Invalid input format", 400
    
    except ConnectionError:
        return "Network issue", 500
    
if  __name__ == '__main__':
    app.run(debug=True)



    

    
    
   




  








