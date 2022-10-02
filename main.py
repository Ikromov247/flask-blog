from operator import length_hint
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm
from flask_gravatar import Gravatar
import os


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
ckeditor = CKEditor(app)
Bootstrap(app)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', "sqlite:///blog.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager(app)
Base = declarative_base()
gravatar = Gravatar(app,
                    size=100,
                    rating='r',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def is_admin(func):
    def wrapper(post_id):
        if current_user.get_id() == "1":
            return func(post_id)
        else:
            return render_template("unauthorized.html"), 403
    return wrapper

##CONFIGURE TABLES
class BlogPost(db.Model, UserMixin, Base):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    author_id = Column(Integer, ForeignKey('user.id'))
    author = relationship("User", back_populates="posts")
   
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(500), nullable=False)
    comments = relationship("Comment",  back_populates="post")

##CREATE TABLE IN DB
class User(UserMixin, db.Model, Base):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    posts = relationship("BlogPost",  back_populates="author")
    comments = relationship("Comment",  back_populates="author")
    

class Comment(UserMixin, db.Model, Base):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.Text, nullable=False)
    author_id = Column(Integer, ForeignKey('user.id'))
    author = relationship("User", back_populates="comments")
    post_id = Column(Integer, ForeignKey('blog_posts.id'))
    post = relationship("BlogPost", back_populates="comments")
    
if not os.path.isdir(os.environ.get('DATABASE_URL', "sqlite:///blog.db")):
    db.create_all()

@app.route('/')
def get_all_posts(): 
    posts = BlogPost.query.all()
    return render_template("index.html", all_posts=posts)


@app.route('/register', methods=["POST", "GET"])
def register():
    form = RegisterForm()
    if form.validate_on_submit() and request.method == "POST":
        if User.query.filter_by(email=request.form.get('email')).first() is None:
            hash_salted_pw = generate_password_hash(request.form.get("password"), "pbkdf2:sha256")
            new_user = User(
                email = request.form.get("email"),
                name = request.form.get("name"),
                password = hash_salted_pw
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user,remember=True)
            return redirect(url_for("get_all_posts"))
        else:
            flash(f"This email is already taken. Maybe login instead?", "info")
            return redirect(url_for("login"))
    return render_template("register.html", form=form)

# print(current_user.is_authenticated)
@app.route('/login', methods=["POST", "GET"])
def login():
    form = LoginForm()
    if form.validate_on_submit() and request.method == "POST":
        user = User.query.filter_by(email=request.form.get("email")).first()
        if user and check_password_hash(user.password, request.form.get("password")):
            login_user(user,remember=True)
            flash("You'll be redirected shortly", "info")
            return redirect(url_for("get_all_posts"))
        else:
            flash("This email is not registered or password is wrong. Maybe register instead?")
            return redirect(url_for("register"))
    return render_template("login.html", form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    comments = Comment.query.filter_by(post_id=post_id).all()
    comment_form = CommentForm()
    if comment_form.validate_on_submit() and request.method == "POST":
        new_comment = Comment(
            comment=comment_form.comment.data,
            author_id=current_user.id,
            post_id=post_id
        )
        db.session.add(new_comment)
        db.session.commit()
    requested_post = BlogPost.query.get(post_id)
    return render_template("post.html", post=requested_post, comment_form=comment_form, comments=comments)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/new-post", methods=["GET", "POST"])
@login_required
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit() and request.method == "POST":
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author_id=current_user.id,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)

@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@is_admin
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit() and request.method == "POST":
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = edit_form.author.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form)


@app.route("/delete/<int:post_id>")
# @is_admin
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))
