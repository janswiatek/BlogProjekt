from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from flask_ckeditor import CKEditorField
from wtforms.validators import DataRequired, URL, Email

##moduł WTForm
class CreatePostForm(FlaskForm):
    title = StringField("Tytuł posta", validators=[DataRequired()])
    body = CKEditorField("Treść posta", validators=[DataRequired()])
    submit = SubmitField("Wyślij Post")

class RegisterForm(FlaskForm):
    name = StringField('Nazwa', validators=[DataRequired()])
    password = PasswordField('Hasło', validators=[DataRequired()])
    submit = SubmitField("Zarejestruj")

class LoginForm(FlaskForm):
    name = StringField('Nazwa', validators=[DataRequired()])
    password = PasswordField('Hasło', validators=[DataRequired()])
    submit = SubmitField("Zaloguj")

class CommentForm(FlaskForm):
    comment_text = CKEditorField('Komentarze:', validators=[DataRequired()] )
    submit = SubmitField("Wyślij komentarz")