from deplatformer_webapp.app import app

if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"])
