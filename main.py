from ascavis_data import alcdef, sha
from ascavis_data.mpc import MpcSqlConnection, mpc_db_query
import httplib2
import simplejson as json
import glob
import os
from flask import Flask, Response, send_from_directory, request
import config

# Parse configuration
cfg_parser = config.parser()
cfg_parser.read(["server.cfg", os.path.expanduser("~/.config/ascavis/server.cfg")])
options = dict(cfg_parser.items("ascavis_server"))

ASSET_DIR = options["asset_dir"]
ALCDEF_DIR = options["alcdef_dir"]
API_MIME = options["api_mime"]


# Setup server
app = Flask(__name__)

# Setup SHA client
spitzer = sha.SpitzerHeritageArchive(httplib2.Http(".cache"))


@app.route("/")
def root():
    """Base route"""
    return send_from_directory(ASSET_DIR, "index.html")


@app.route("/spectrum/<int:jpl>")
def spectrum(jpl):
    """Retrieve spectra of an asteroid

    Returns a list of spectra available for an asteroid given its JPL number.

    """
    observations = sha.parse_table(spitzer.query_by_jpl(jpl))
    spectra = map(
        lambda obs: sha.parse_table(spitzer.download_spectrum(obs)),
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
    """Get detailed MPC metadata for an asteroid

    Given its JPL number, this route returns an object containing metadata
    about an asteroid from the database of the Minor Planet Center.

    """
    query = mpc_db_query(max_amount_of_data=1, parameters_to_limit=['number='+str(jpl)])
    with MpcSqlConnection(options["db_address"], options["db_username"],
            options["db_password"], options["db_name"]) as mpc:
        mpc_data = mpc.retrieve_data(query)
    return Response(json.dumps(mpc_data[0]), mimetype=API_MIME)


@app.route('/mpc_more/',methods=['POST','GET'])
def mpc_more_call():
    """Selective queries to Minor Planet Center database

    Returns a list of asteroids from the MPC database including properties
    specified by some query.

    GET parameters:

    - `orderby`: by which fields the query is ordered,
      e.g. `absolute_magnitude DESC`
    - `no`: maximum number of asteroids to output
    - `paramlim`: limits for parameters, e.g. `residual_rms=0.2` or
      `inclination<6`; can be concatenated.

    Example queries:

    /mpc_more/?orderby=absolute_magnitude%20DESC&no=2&paramlim=residual_rms=0.2
    /mpc_more/?orderby=absolute_magnitude%20DESC&no=10&paramlim=residual_rms%3E0.2%20AND%20inclination%3E6

    """
    with MpcSqlConnection(options["db_address"], options["db_username"],
            options["db_password"], options["db_name"]) as mpc:
        # second parameter of get is the default value for when the key is not given
        mpc_more_dataamount = request.args.get('no',1)
        param_limit = request.args.get('paramlim','')
        orderby = request.args.get('orderby','')
        query = mpc_db_query(max_amount_of_data=mpc_more_dataamount,
            parameters_to_limit=[param_limit], order_by=[orderby])
        mpc_data_more = mpc.retrieve_data(query)
    return Response(json.dumps(mpc_data_more), mimetype=API_MIME)


@app.route('/app/<path:filename>')
def send_file(filename):
    """Simple assets route

    Serves plain files, e.g. JS client, CSS.

    """
    return send_from_directory(ASSET_DIR, filename)


if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0')
