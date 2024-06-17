import logging
from app import create_app

app = create_app()

#if __name__ == "__main__":
#    @app.route('/')
#    def helloworld():
#        return __name__'

@app.route('/')
def helloworld():
    return '__main__'

#app.run()


#if __name__ == "__main__":
#    logging.info("Flask app started")
#    app.run(host="0.0.0.0", port=8000)


#if __name__ == "__main__":
#    @app.route('/')
#    def helloworld():
#       return 'The app working!'

#W:Got host and post away,so to run on python anywhere.
#if __name__ == "__main__":
#   logging.info("Flask app started")
#    app.run()

