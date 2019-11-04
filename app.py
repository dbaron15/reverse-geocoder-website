from app import app

app = app('config.development')

if '__name__' == '__main__':
    app.run()