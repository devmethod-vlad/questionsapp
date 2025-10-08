from questionsapp import create_app
import questionsapp

app = create_app(celery=questionsapp.celery)

if __name__ == "__main__":
    # app.run(host='0.0.0.0')
    app.run(host='127.0.0.1')