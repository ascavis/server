from ascavis_data import alcdef, sha, mpc
import httplib2
import simplejson as json
import glob
import os
from flask import Flask, Response, send_from_directory, request


API_MIME = "text/plain"
DB_SOURCE = '192.168.100.1'
DB_user = 'root'
DB_pw = 'space'
DB_name = 'mp_properties'
ASSET_DIR = "assets/"
ALCDEF_DIR = "alcdef/"

app = Flask(__name__)
spitzer = sha.SpitzerHeritageArchive(httplib2.Http(".cache"))


@app.route("/")
def hello_world():
    return 'Hello World!'


@app.route("/spectrum/<int:jpl>")
def spectrum(jpl):
    observations = sha.parse_table(spitzer.query_by_jpl(jpl)[1])
    spectra = map(
        lambda obs: sha.parse_table(spitzer.download_spectrum(obs)[1]),
        filter(sha.is_spectrum, observations)
    )
    return Response(json.dumps(spectra), mimetype=API_MIME)


@app.route("/lightcurve/<int:jpl>")
def lightcurve(jpl):
    """Lightcurve API

    Returns a list of lightcurve observations available for a given JPL
    asteroid number.

    Note: for now, this route assumes the lightcurve data to be available as
    files in some directory and just picks the first one that appears to be
    appropriate (i.e. named ALCDEF_<jpl>_*).

    """
    files = glob.glob(os.path.join(ALCDEF_DIR, "ALCDEF_{}_*".format(jpl)))
    parsed = alcdef.alcdef.parse_string(open(files[0]).read())
    return Response(json.dumps(parsed), mimetype=API_MIME)


@app.route("/mpc/<int:jpl>")
def mpc_call(jpl):
    mpc_data = mpc.query_mpc_db(DB_SOURCE,DB_user,DB_pw,DB_name,max_amount_of_data=1, parameters_to_limit=['number='+str(jpl)], order_by=[])
    return Response(json.dumps(mpc_data[0]), mimetype=API_MIME)


@app.route('/mpc_more/',methods=['POST','GET'])
def mpc_more_call():
    #e.g. http://localhost:5000/mpc_more/?orderby=absolute_magnitude%20DESC&no=2&paramlim=residual_rms=0.2 (%20 is space, leave DESC or put ASC to turn around)
    # can also concatenate conditions: http://localhost:5000/mpc_more/?orderby=absolute_magnitude%20DESC&no=10&paramlim=residual_rms%3E0.2%20AND%20inclination%3E6
    #second value of get is the default value for when the key is not given
    mpc_more_dataamount = request.args.get('no',1)
    param_limit = request.args.get('paramlim','')
    orderby = request.args.get('orderby','')
    mpc_data_more = mpc.query_mpc_db(DB_SOURCE,DB_user,DB_pw,DB_name,max_amount_of_data=mpc_more_dataamount, parameters_to_limit=[param_limit], order_by=[orderby])
    return Response(json.dumps(mpc_data_more), mimetype=API_MIME)


@app.route('/app/<path:filename>')
def send_file(filename):
    return send_from_directory(ASSET_DIR, filename)


if __name__ == "__main__":
    app.debug = True
    app.run()
