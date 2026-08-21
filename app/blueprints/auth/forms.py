from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Regexp, Optional


class RegisterForm(FlaskForm):
    full_name = StringField("ሙሉ ስም / Full name", validators=[DataRequired(), Length(min=3, max=150)])
    username = StringField(
        "የተጠቃሚ ስም / Username",
        validators=[Optional(), Length(min=3, max=50), Regexp(r"^[a-zA-Z0-9_.]+$", message="ፊደላት፣ ቁጥሮች፣ _ እና . ብቻ / Letters, numbers, _ and . only")],
    )
    email = StringField("ኢሜይል / Email", validators=[DataRequired(), Email()])
    phone = StringField(
        "ስልክ / Phone",
        validators=[DataRequired(), Regexp(r"^\+?\d{9,15}$", message="ትክክለኛ ስልክ ቁጥር ያስገቡ / Enter a valid phone number")],
    )
    password = PasswordField("የይለፍ ቃል / Password", validators=[DataRequired(), Length(min=8, message="ቢያንስ 8 ፊደላት / At least 8 characters")])
    confirm_password = PasswordField(
        "የይለፍ ቃል ያረጋግጡ / Confirm password",
        validators=[DataRequired(), EqualTo("password", message="የይለፍ ቃላት አይመሳሰሉም / Passwords must match")],
    )
    submit = SubmitField("ተመዝገብ / Register")


class LoginForm(FlaskForm):
    # Accept either the current identifier field or the legacy email field.
    identifier = StringField("የተጠቃሚ ስም ወይም ኢሜይል / Username or Email", validators=[Optional()])
    email = StringField("ኢሜይል / Email", validators=[Optional(), Email()])
    password = PasswordField("የይለፍ ቃል / Password", validators=[DataRequired()])
    remember = BooleanField("አስታውሰኝ / Remember me")
    submit = SubmitField("ግባ / Log in")

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators=extra_validators):
            return False
        if not (self.identifier.data or self.email.data):
            self.identifier.errors.append("የተጠቃሚ ስም ወይም ኢሜይል ያስገቡ / Enter your username or email.")
            return False
        return True


class ForgotPasswordForm(FlaskForm):
    email = StringField("ኢሜይል / Email", validators=[DataRequired(), Email()])
    submit = SubmitField("ማስተካከያ ሊንክ ላክ / Send reset link")


class ResetPasswordForm(FlaskForm):
    password = PasswordField("አዲስ የይለፍ ቃል / New password", validators=[DataRequired(), Length(min=8, message="ቢያንስ 8 ፊደላት / At least 8 characters")])
    confirm_password = PasswordField(
        "የይለፍ ቃል ያረጋግጡ / Confirm new password",
        validators=[DataRequired(), EqualTo("password", message="የይለፍ ቃላት አይመሳሰሉም / Passwords must match")],
    )
    submit = SubmitField("የይለፍ ቃል ቀይር / Reset password")
