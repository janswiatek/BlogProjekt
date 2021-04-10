from datetime import date

from flask import Flask, render_template,request, redirect,url_for,session,abort, flash
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_migrate import Migrate
from functools import wraps
from flask_bootstrap import Bootstrap
import sqlite3

from flask_sqlalchemy import SQLAlchemy
from flask_ckeditor import CKEditor
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm

app = Flask(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'SECRET_KEY'

#config
app.config.update(
    DEBUG=True,
    SECRET_KEY = 'sekretny_klucz'
)

Bootstrap(app)

##POLACZENIE Z BAZA DANYCH
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#moduł formatowania postów
ckeditor = CKEditor(app)


##KONFIGURACJA TABEL W BAZIE DANYCH
class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("User.id"))
    author = db.relationship("User", back_populates="posts")
    title = db.Column(db.String(250), unique=True, nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    comments = db.relationship('Comment', back_populates="parent_post")

class User(UserMixin, db.Model):
    __tablename__ = "User"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    password = db.Column(db.String(250), nullable=False)
    isadmin = db.Column(db.Boolean, default=False, nullable=False)
    posts = db.relationship("BlogPost", back_populates="author")
    comments = db.relationship('Comment', back_populates="comment_author")

    def __str__(self):
        return self.name

    #sprawdzenie, czy user ma uprawnienia admina
    @property
    def is_admin(self):
        return self.isadmin

class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('User.id'))
    comment_author = db.relationship("User", back_populates="comments")
    post_id = db.Column(db.Integer, db.ForeignKey('blog_posts.id'))
    parent_post = db.relationship('BlogPost', back_populates="comments")
    text = db.Column(db.Text, nullable=False)

    def __str__(self):
        return self.text

#dodawanie panelu /admin/
class MyAdminIndexView(AdminIndexView):
    #sprawdzenie, czy użytkownik jest zalogowany i ma uprawnienia admina
    def is_accessible(self):
       #  return True   #jakby skasowało się admina
        return current_user.is_admin

#widoki w panelu admina
class MyModelView(ModelView):
    form_columns = ['name', 'password', 'isadmin']
class MyPostView(ModelView):
    form_columns = ['title', 'date', 'body']


admin = Admin(app, index_view=MyAdminIndexView())
admin.add_view(MyPostView(BlogPost, db.session))
admin.add_view(MyModelView(User, db.session))

db.create_all()

login_manager = LoginManager()
login_manager.init_app(app)

#Migrate wspomaga edycje bazy danych SQLAlchemy
migrate = Migrate(app, db)

#dekorator dla rzeczy zarezerwowanych dla adminów
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Jeśli user nie ma uprawnień admina zwróć błąd 403 (brak uprawnień)
        if current_user.is_admin == False:
            return abort(403)
        # W innym wypadku kontynuuj routing
        return f(*args, **kwargs)
    return decorated_function

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


#############################routing
@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    return render_template("index.html", all_posts=posts, is_login=current_user.is_authenticated)


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if request.method == "POST" and form.validate_on_submit():
        if User.query.filter_by(name=form.name.data).first():
            flash('nazwa użytkownika już zajęta, spróbuj inną')
            return redirect(url_for('register'))
        user = User(name=form.name.data,
                    password=form.password.data) # potem dodać jakieś moduły do hashowania
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('get_all_posts'))
    return render_template("register.html", form=form)

@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if request.method == "POST":
        user = User.query.filter_by(name=form.name.data).first()
        if not user:
            flash('Nie ma użytkownika o takiej nazwie')
            return redirect(url_for('login'))
        elif not (user.password == form.password.data):
            flash('Hasło niepoprawne')
            return redirect(url_for('login'))
        else:
            login_user(user)
        return redirect(url_for('get_all_posts'))

    return render_template("login.html", form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>", methods=["POST", "GET"])
def show_post(post_id):
    form = CommentForm()
    requested_post = BlogPost.query.get(post_id)

    if request.method == "POST" and form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("Zaloguj się przed komentowaniem")
            return redirect(url_for('login'))
        else:

            comment = Comment(text=request.form.get('comment_text'),
                              comment_author=current_user,
                              parent_post=requested_post)
            db.session.add(comment)
            db.session.commit()
            return redirect(url_for('show_post', post_id=post_id))

    return render_template("post.html", form=form, post=requested_post, is_login=current_user.is_authenticated)


@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            body=form.body.data,
            author=current_user,
            date=date.today().strftime("%d, %m, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form, is_login=current_user.is_authenticated)


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit() and request.method == "POST":
        post.title = edit_form.title.data
        # post.author = edit_form.author.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form, is_login=current_user.is_authenticated)


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))

@app.route("/delete_comment/<int:comm_id>")
@admin_only
def delete_comment(comm_id):
    comment_to_delete = Comment.query.get(comm_id)
    db.session.delete(comment_to_delete)
    db.session.commit()
    return redirect(url_for('show_post', post_id=comment_to_delete.post_id))

if __name__ == '__main__':
    app.run(debug=True)

