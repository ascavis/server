from ascavis_data import alcdef, sha
import httplib2
import json
from flask import Flask, Response, send_from_directory


API_MIME = "text/plain"
ASSET_DIR = "assets/"

app = Flask(__name__)
spitzer = sha.SpitzerHeritageArchive(httplib2.Http(".cache"))


@app.route("/")
def hello_world():
    return 'Hello World!'


@app.route("/spectrum/<int:jpl>")
def spectrum(jpl):
    observations = sha.parse_table(spitzer.query_by_jpl(253)[1])
    spectrum = sha.parse_table(
        spitzer.download_spectrum(filter(sha.is_spectrum, observations)[0])[1]
    )
    return Response(json.dumps(spectrum), mimetype=API_MIME)


@app.route('/app/<path:filename>')
def send_file(filename):
    return send_from_directory(ASSET_DIR, filename)


if __name__ == "__main__":
    app.debug = True
    app.run()
