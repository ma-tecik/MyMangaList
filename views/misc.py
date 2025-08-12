from flask import Blueprint, request, Response, jsonify, current_app as app
import requests
from utils.line import get_thumbnail as line_thumbnail
misc_bp = Blueprint("misc", __name__)


@misc_bp.route("/thumbnail-proxy", methods=["GET"]) # url: "/thumbnail-proxy?url={mangadex_url}" or "/thumbnail-proxy?url=line://{/thumbnail_url}"
def proxy_image():
    url = request.args.get('url')
    if not url:
        return jsonify({"result": "KO", "error": "Missing url parameter"}), 400
    if url.startswith("https://uploads.mangadex.org/"):
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                app.logger.error(f"for {url}, upstream returned {resp.status_code}")
                return jsonify({"status": "KO", 'message': "Upstream error"}), 502
            return Response(resp.content, mimetype=resp.headers.get("content-type", "image/jpeg")), 200
        except Exception as e:
            app.logger.error(f"for {url}, {e}")
            return jsonify({"result": "KO", "error": "Unexpected error"}), 500
    elif url.startswith("line://"):
        try:
            return Response(line_thumbnail(url [6:]), mimetype="image/jpeg"), 200
        except Exception as e:
            app.logger.error(f"for {url}, {e}")
            return jsonify({"result": "KO", "error": "Unexpected error"}), 500
    else:
        return jsonify({"status": "KO", "error": "Invalid URL"}), 400

@misc_bp.route("/api/openapi.yaml" , methods=["GET"])
def openapi_spec():
    try:
        with open("static/openapi.yaml", "r") as f:
            return Response(f.read(), mimetype="application/x-yaml")
    except Exception as e:
        app.logger.error(f"Failed to return openapi.yaml, {e}")
        return jsonify({"result": "KO", "error": "Internal server error"}), 500