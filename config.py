from ConfigParser import SafeConfigParser

def parser():
    return SafeConfigParser({
        "db_address": "127.0.0.1",
        "db_username": "root",
        "db_password": "space",
        "db_name": "mp_properties",
        "asset_dir": "assets/",
        "alcdef_dir": "alcdef/",
        "api_mime": "text/plain",
    })
