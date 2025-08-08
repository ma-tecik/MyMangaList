from flask import Blueprint, request, Response, jsonify, send_from_directory
import requests
import logging

misc_bp = Blueprint('misc', __name__)


@misc_bp.route('/proxy-image', methods=['GET']) # image_url: "/proxy-image?url={mangadex_url}"
def proxy_image():
    url = request.args.get('url')
    if not url or not url.startswith('https://uploads.mangadex.org/'):
        return jsonify({"result": "KO", "error": "Invalid or missing url"}), 400
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            logging.error(f"Error in proxy_image: {url}, upstream returned {resp.status_code}")
            return jsonify({'status': 'KO', 'message': "Upstream error"}), 502
        return Response(resp.content, mimetype=resp.headers.get('content-type', 'image/jpeg')), 200
    except requests.exceptions.Timeout as e:
        logging.error(f"Error in proxy_image: {url}, timeout occurred, {e}")
        return jsonify({"result": "KO", "error": "Timeout"}), 504
    except Exception as e:
        logging.error(f"Error in proxy_image: {url}, unexpected error occurred, {e}")
        return jsonify({"result": "KO", "error": "Unexpected error"}), 500

@misc_bp.route("/api/openapi.yaml" , methods=["GET"])
def openapi_spec():
    return send_from_directory("static", "openapi.yaml")