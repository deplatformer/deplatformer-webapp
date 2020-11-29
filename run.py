from deplatformer_webapp.app import app

print("debug %s" % app.config["DEBUG"])

if __name__ == "__main__":
    app.run(debug=False, use_reloader=False) #debug=app.config["DEBUG"])  ###FIXME
