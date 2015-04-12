from ascavis_data import alcdef, sha, mpc
import httplib2
import simplejson as json
from flask import Flask, Response, send_from_directory, request


API_MIME = "text/plain"
DB_SOURCE = '192.168.100.1'
DB_user = 'root'
DB_pw = 'space'
DB_name = 'mp_properties'
ASSET_DIR = "assets/"

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

@app.route("/mpc/<int:jpl>")
def mpc_call(jpl):
    mpc_data = mpc.query_mpc_db(DB_SOURCE,DB_user,DB_pw,DB_name,max_amount_of_data=1, parameters_to_limit=['number='+str(jpl)], order_by=[])
    return Response(json.dumps(mpc_data[0]), mimetype=API_MIME)

@app.route('/mpc_more/',methods=['POST','GET'])
def mpc_more_call():
    mpc_more_dataamount = request.args.get('no','')
    #if (mpc_more_dataamount == ''):
    #    mpc_more_dataamout = 1
    param_limit = request.args.get('paramlim','')
    orderby = request.args.get('orderby','')
    mpc_data_more = mpc.query_mpc_db(DB_SOURCE,DB_user,DB_pw,DB_name,max_amount_of_data=mpc_more_dataamount, parameters_to_limit=[], order_by=[])
    return Response(json.dumps(mpc_data_more), mimetype=API_MIME)

@app.route('/app/<path:filename>')
def send_file(filename):
    return send_from_directory(ASSET_DIR, filename)

if __name__ == "__main__":
    app.debug = True
    app.run()
