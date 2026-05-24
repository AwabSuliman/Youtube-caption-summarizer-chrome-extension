from flask import Flask, jsonify, request
from transformers import T5ForConditionalGeneration, T5Tokenizer
from urllib.parse import parse_qs, urlparse
from werkzeug.exceptions import HTTPException
from youtube_transcript_api import YouTubeTranscriptApi

MODEL_NAME = "t5-base"
MAX_INPUT_TOKENS = 512
CHUNK_WORD_SIZE = 220

app = Flask(__name__)

model = None
tokenizer = None


def load_model():
    global model, tokenizer

    if model is None or tokenizer is None:
        tokenizer = T5Tokenizer.from_pretrained(MODEL_NAME)
        model = T5ForConditionalGeneration.from_pretrained(MODEL_NAME)
        model.eval()

    return model, tokenizer


def get_video_id(url):
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path

    if "youtu.be" in host:
        return path.strip("/").split("/")[0] or None

    if "youtube.com" not in host:
        return None

    query_string = parse_qs(parsed.query)
    if "v" in query_string:
        return query_string["v"][0]

    for part in path.split("/"):
        if len(part) == 11:
            return part

    return None


def get_transcript(video_id):
    transcript_api = YouTubeTranscriptApi()
    transcript_items = transcript_api.fetch(video_id)
    transcript_text = [item.text for item in transcript_items]
    return " ".join(transcript_text).strip()


def split_transcript(transcript, chunk_word_size=CHUNK_WORD_SIZE):
    words = transcript.split()

    if not words:
        return []

    return [
        " ".join(words[index:index + chunk_word_size])
        for index in range(0, len(words), chunk_word_size)
    ]


def summarize_chunk(text):
    active_model, active_tokenizer = load_model()

    inputs = active_tokenizer.encode(
        "summarize: " + text,
        return_tensors="pt",
        max_length=MAX_INPUT_TOKENS,
        truncation=True
    )

    tokens = active_model.generate(
        inputs,
        max_length=150,
        length_penalty=1.5,
        num_beams=8,
        early_stopping=True
    )

    return active_tokenizer.decode(tokens[0], skip_special_tokens=True).strip()


def summarize_transcript(transcript):
    chunks = split_transcript(transcript)

    if not chunks:
        return ""

    chunk_summaries = [summarize_chunk(chunk) for chunk in chunks if chunk.strip()]
    combined_summary = " ".join(summary for summary in chunk_summaries if summary)

    if not combined_summary:
        return ""

    if len(chunk_summaries) == 1:
        return combined_summary

    return summarize_chunk(combined_summary)


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


@app.errorhandler(HTTPException)
def handle_http_error(exc):
    response = jsonify(error=exc.description or exc.name)
    response.status_code = exc.code or 500
    return response


@app.errorhandler(Exception)
def handle_unexpected_error(exc):
    app.logger.exception("Unhandled backend error")
    return jsonify(error=f"Unexpected server error: {exc}"), 500


@app.route("/api/health", methods=["GET"])
def health_check():
    return {
        "status": "ok",
        "model_loaded": model is not None and tokenizer is not None
    }


@app.route("/api/summarize", methods=["GET"])
def summarize_youtube_video():
    youtube_url = request.args.get("youtube_url", "").strip()

    if not youtube_url:
        return {"error": "Missing youtube video URL"}, 400
    
    try:
        video_id = get_video_id(youtube_url)
        if not video_id:
            return {"error": "Video ID not available"}, 400
        
        transcript = get_transcript(video_id)
        if not transcript:
            return {"error": "Transcript unavailable"}, 400
        summary = summarize_transcript(transcript)
        if not summary:
            return {"error": "Summary failed"}, 500

        return {
            "video_id": video_id,
            "summary": summary
        }, 200
    except ValueError:
        return {"error": "Invalid input format"}, 400
    except ConnectionError:
        return {"Error": "Network issue"}, 500
    except Exception as exc:
        return {"error": f"Unexpected error: {exc}"}, 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)
