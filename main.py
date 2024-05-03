from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os


MOVIE_DB_API_KEY = os.environ["MOVIE_DB_API_KEY"]
MOVIE_DB_ACCESS_TOKEN = os.environ["MOVIE_DB_ACCESS_TOKEN"]
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ["SECRET_KEY"]
Bootstrap5(app)

class EditForm(FlaskForm):
    rating = StringField("Your Rating Out Of 10 e.g. 7.5")
    review = StringField("Your Review")
    submit = SubmitField("Done")

class AddForm(FlaskForm):
    title = StringField("Movie Title")
    submit = SubmitField("Add Movie")

# CREATE DB
class Base(DeclarativeBase):
    pass

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movies.db"

db = SQLAlchemy(model_class=Base)
db.init_app(app)

# CREATE TABLE
class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=False, nullable=True)
    year: Mapped[int] = mapped_column(Integer, nullable=True, unique=False)
    description: Mapped[str] = mapped_column(String(500), unique=False, nullable=True)
    rating: Mapped[int] = mapped_column(Float, unique=False, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, unique=False, nullable=True)
    review: Mapped[str] = mapped_column(String(250), unique=False, nullable=True)
    img_url: Mapped[str] = mapped_column(String(250), unique=False, nullable=True)

with app.app_context():
    db.create_all()

@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(Movie.rating))
    all_movies = result.scalars().all()
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies)- i
    db.session.commit()
    return render_template("index.html", movies=all_movies)

@app.route("/update", methods=["GET", "POST"])
def update():
    form = EditForm()
    movie_id = request.args.get("id")
    movie = db.get_or_404(Movie, movie_id)
    if form.validate_on_submit():
        movie.rating = form.rating.data
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("edit.html", form=form, movie=movie)

@app.route("/delete", methods=["GET", "POST"])
def delete_movie():
    movie_id = request.args.get("id")
    movie_to_delete = db.get_or_404(Movie, movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/add", methods=["GET", "POST"])
def add_movie():
    add_form = AddForm()
    if add_form.validate_on_submit():
        url = "https://api.themoviedb.org/3/search/movie"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {MOVIE_DB_ACCESS_TOKEN}"
        }
        params = {
            "query": add_form.title.data,
            "language": "en-US"
        }
        response = requests.get(url=f"{url}", headers=headers, params=params)
        movie_data = response.json()["results"]
        return render_template("select.html", movies=movie_data)
    return render_template("add.html", form=add_form)

@app.route('/find', methods=["GET", "POST"])
def find_movie():
    movie_api_id = request.args.get("id")
    if movie_api_id:
        url = "https://api.themoviedb.org/3/search/movie"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {MOVIE_DB_ACCESS_TOKEN}"
        }
        params = {
            "query": request.args.get("title"),
            "language": "en-US"
        }
        response = requests.get(url=f"{url}", headers=headers, params=params)
        movie_data = response.json()["results"][0]
        movie_to_add = Movie(title=f"{movie_data['original_title']}",
                             year=f"{movie_data['release_date'].split('-')[0]}",
                             img_url=f"{MOVIE_DB_IMAGE_URL}{movie_data['poster_path']}",
                             description=f"{movie_data['overview']}")
        db.session.add(movie_to_add)
        db.session.commit()
        return redirect(url_for("update", id=movie_to_add.id))

if __name__ == '__main__':
    app.run(debug=True, port=5003)
