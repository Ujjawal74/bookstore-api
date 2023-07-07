import os
from flask import Flask, make_response, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from pytz import timezone
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from time import time

# flask app instance
app = Flask(__name__)
# marshmallow instance
ma = Marshmallow(app)
# Using SQLite Database
db = SQLAlchemy()
# configure the SQLite database # creating database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///books.db"
# initialize the app with the extension
db.init_app(app)
# For Cors Policy
CORS(app)

# Book Model


class Books(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), unique=True, nullable=False)
    author = db.Column(db.String(500), nullable=False)
    description = db.Column(db.String, nullable=False)
    cover = db.Column(db.String, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    rating = db.Column(db.Float, nullable=False)
    genre = db.Column(db.String, nullable=False)
    publication_date = db.Column(db.DateTime, nullable=False)
    createdAt = db.Column(
        db.DateTime, server_default=db.func.now(), nullable=False)
    updatedAt = db.Column(db.DateTime, server_default=db.func.now(),
                          onupdate=db.func.now(), nullable=False)

    # overwriting dunder method
    def __repr__(self) -> str:
        return f'{self.id} -> {self.title}'

# For serialize into readable json to front-end


class BookSchema(ma.Schema):
    class Meta:
        # expose fields to be serialize
        fields = ('id', 'title', 'author', 'description', 'cover',
                  'price', 'rating', 'genre', 'publication_date')


book_schema = BookSchema()  # one row
books_schema = BookSchema(many=True)  # multiple rows

# # create database first time
# with app.app_context():
#     db.create_all()


# uploads of images dierctory & configuration
UPLOAD_FOLDER = "uploads"
# ALLOWED_EXTENSIONS = {'jpeg', 'jpg', 'png', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# method to get date from string into datetime object for sqlite


def getDate(date: str):
    arr = date.split('-')
    y = int(arr[0])
    m = int(arr[1])
    d = int(arr[2])
    dateObj = datetime(y, m, d, 00, 00, 00, 00,
                       tzinfo=timezone("Asia/Kolkata"))
    return dateObj

# Home Route


@app.route("/", methods=['GET'])
def index():
    return make_response(jsonify({"msg": "welcome to book store api"}))

# Get all books data


@app.route("/get", methods=['GET', 'POST'])
def get():
    if request.method == 'GET':
        allBooks = db.session.execute(
            db.select(Books).order_by(Books.title)).scalars()

        books = books_schema.dump(allBooks)
        return make_response(jsonify({"books": books}))

    if request.method == 'POST':
        filter = request.get_json()['filter']
        if filter == 'rating':
            allBooks = db.session.execute(
                db.select(Books).order_by(Books.rating)).scalars()
        elif filter == 'price':
            allBooks = db.session.execute(
                db.select(Books).order_by(Books.price)).scalars()
        elif filter == 'publication_date':
            allBooks = db.session.execute(
                db.select(Books).order_by(Books.publication_date)).scalars()
        else:
            allBooks = db.session.execute(
                db.select(Books).order_by(Books.title)).scalars()

        books = books_schema.dump(allBooks)
        return make_response(jsonify({"books": books}))

# upload image route


@app.route("/upload", methods=['POST'])
def upload():
    file = request.files['image']
    curr_time = round(time())
    filename = secure_filename(f"cover_{curr_time}.jpg")
    target = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(target)
    return make_response(jsonify({"url": f"http://localhost:5000/{target}"}))

# serve uploaded file


@app.route('/uploads/<name>')
def download_file(name):
    return send_from_directory(app.config["UPLOAD_FOLDER"], name)

# adding a new book


@app.route("/add-book", methods=['GET', 'POST'])
def add():
    if request.method == "POST":
        try:
            obj = request.get_json()
            book = Books(title=obj['title'], author=obj['author'], description=obj['description'], cover=obj['cover'],
                         price=int(obj['price']), rating=float(obj['rating']), genre=obj['genre'], publication_date=getDate(obj['publication_date']))
            db.session.add(book)
            db.session.commit()
            return make_response(jsonify({'status': 'ok', 'msg': 'book added sucessfully'}))
        except Exception as e:
            return make_response(jsonify({'status': 'error', 'error': e}))

# edit an existing book


@app.route("/edit-book", methods=['GET', 'POST'])
def edit():
    if request.method == 'POST':
        obj = request.get_json()
        book = db.session.execute(
            db.select(Books).filter_by(id=int(obj['id']))).scalar_one()

        book.title = obj['title']
        book.author = obj['author']
        book.description = obj['description']
        book.cover = obj['cover']
        book.price = int(obj['price'])
        book.rating = float(obj['rating'])
        book.genre = obj['genre']
        d = obj['publication_date']
        d = d.split('T')[0]
        book.publication_date = getDate(d)
        db.session.add(book)
        db.session.commit()

        return make_response(jsonify({'status': 'ok', 'msg': 'Updated sucessfully'}))

# deleting a record with id


@app.route("/book/delete", methods=['GET', 'POST'])
def delete():
    if request.method == 'POST':
        id = request.get_json()['id']
        book = db.session.execute(
            db.select(Books).filter_by(id=int(id))).scalar_one()
        db.session.delete(book)
        db.session.commit()
        return make_response(jsonify({'status': 'ok', 'msg': 'deletion success'}))

# serach with name


@app.route("/search", methods=['POST'])
def find():
    if request.method == 'POST':
        query = request.get_json()['query']
        books = db.session.execute(
            db.select(Books).filter(Books.title.like(f'{query}%'))).scalars()
        res = books_schema.dump(books)

        return make_response(jsonify({'status': 'ok', 'books': res}))


# staring the flask server on custom socket
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
