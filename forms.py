from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Email, Length, ValidationError, EqualTo, URL
from flask_ckeditor import CKEditorField

##WTForm
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")

class RegisterForm(FlaskForm):
    email = StringField("Your email", validators=[DataRequired(), Email()])
    name = StringField("Your name", validators=[DataRequired(),Length(min=4, max=30)])
    password = PasswordField("Your password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField("Confirm your password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("SIGN ME UP!")

class LoginForm(FlaskForm):
    email = StringField("Your email", validators=[DataRequired(), Email()])
    name = StringField("Your name", validators=[DataRequired(), Length(min=4, max=30)])
    password = PasswordField("Your password", validators=[DataRequired(), Length(min=6)])
    submit = SubmitField("LET ME IN!")
    
class CommentForm(FlaskForm):
    comment = CKEditorField("Write your comment", validators=[DataRequired()])
    submit = SubmitField("Comment")