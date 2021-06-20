from flask import Flask, render_template, flash, redirect, url_for, session, request, logging,jsonify
from flask_mysqldb  import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import  sha256_crypt
from functools import wraps
app = Flask(__name__)

# Configure MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'gklct345'
app.config['MYSQL_DB'] = 'flaskassess'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# initialize MYSQL
mysql = MySQL(app)

@app.route('/')
def index():
    return render_template('home.html')


class RegistrationForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')


# User Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('index'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    # session.pop('username', None)
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

# Decorator method to check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('User not logged in please log in', 'danger')
            return redirect(url_for('login'))
    return wrap

# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    return render_template('dashboard.html')

# Add Post
@app.route('/add_post', methods=['GET', 'POST'])
@is_logged_in
def add_post():
    if request.method == 'POST':
        title = request.json['title']
        author = request.json['author']
        body = request.json['body']

        # Create Cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("INSERT INTO posts(title, body, author) VALUES(%s, %s, %s)",(title, body, author))

        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        return "Success"

    return "Failure"

@app.route('/get_post/<string:title>', methods=['GET'])
@is_logged_in
def edit_post(title):
    # Create cursor
    cur = mysql.connection.cursor()
    # Get post by name
    cur.execute("SELECT * FROM posts WHERE title = %s", [title])
    data = cur.fetchone()
    return jsonify(data)


# Retrieve All posts
@app.route('/posts', methods=['GET'])
def get_posts():
    cur = mysql.connection.cursor()
    # Get all posts
    cur.execute("SELECT * FROM posts ")
    data = cur.fetchall()
    return jsonify(data)

# Edit a post
@app.route('/edit_post/<string:title>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(title):

    if request.method == 'POST':
        # Create Cursor
        cur = mysql.connection.cursor()
        app.logger.info(title)
        # Execute
        cur.execute ("UPDATE posts SET title=%s, body=%s WHERE title=%s",("new title", "new body", title))
        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        return "Success"

    return "Failure"

# Delete Post
@app.route('/delete_post/<string:title>', methods=['POST'])
# @is_logged_in
def delete_article(title):
    # Create cursor
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("DELETE FROM posts WHERE title = %s", [title])

    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    return "Success"

if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)