
from flask import Flask,jsonify, render_template, flash, redirect, url_for, session, request, logging
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
import jwt 
import datetime
from flask_pymongo import PyMongo
import bcrypt

app = Flask(__name__)

#Add your Mongo db name and URI
app.config['MONGO_DBNAME'] = 'FlaskApp'
app.config['MONGO_URI'] = 'mongodb+srv://rohit:rohit123@flaskapp-uhtlu.mongodb.net/test?retryWrites=true&w=majority'
app.config['SECRET_KEY'] = 'thisisthesecretkey'

mongo = PyMongo(app)


# Index
@app.route('/')
def index():
    return render_template('home.html')


# About
@app.route('/about')
def about():
    return render_template('about.html')

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.args.get('token') #http://127.0.0.1:5000/route?token=alshfjfjdklsfj89549834ur
        x=token
        print(token)
        if token==None:
            return token
        try: 
            data = jwt.decode(token, app.config['SECRET_KEY'])
        except:
            flash('Token is Invalid! or Expired in 2 minutes', 'danger')
            return redirect(url_for('login'))

        return f(*args, **kwargs)

    return decorated


# Register Form Class
class RegisterForm(Form):
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
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        id = mongo.db.test.users.insert(
            {'username':username,'email':email,'password':password}
        )
        
        response = jsonify({
            '_id':str(id),
            'username':username,
            'password':password,
            'email':email
        })
        response.status_code=201
        flash('You are now registered and can log in', 'success')

        return redirect(url_for('login'))
    return render_template('register.html', form=form)


# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

    
        # Get user by username
        result = mongo.db.test.users.find_one({'username':username})
        
        print(result)
        try:
            if len(result)>0 :
                # Get stored hash
                
                password = result['password']

                # Compare Passwords
                if sha256_crypt.verify(password_candidate, password):
                    #global token
                    #mention time to expire token
                    token = jwt.encode({'user' : username, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=2)}, app.config['SECRET_KEY']) 
                    global x
                    x = token
                    # Passed
                    session['logged_in'] = True
                    session['username'] = username

                    flash('You are now logged in', 'success')
                    
                    return redirect(url_for('dashboard',token=token))
                else:
                    error = 'Invalid login'
                    return render_template('login.html', error=error)
                
            else:
                error = 'Username not found'
                return render_template('login.html', error=error)
        except Exception as e:
            error = 'Username Not found or error occured'
            return render_template('login.html', error=error)

    return render_template('login.html')

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

# Dashboard
@app.route('/dashboard')
@token_required
@is_logged_in
def dashboard():
    # token = token
    # if not token:
    #     flash('Token is missing!, Please login', 'danger')
    #     return redirect(url_for('login'))

    #    try: 
    #data = jwt.decode(token, app.config['SECRET_KEY'])
    username = session['username']
    articles=mongo.db.test.articles.find({'user':username})
    print(articles)
    
    return render_template('dashboard.html', articles=articles)
    # except:
    #     flash('Token is Invalid! or Expired ', 'danger')
    #     return redirect(url_for('login'))

    
# Article Form Class
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    amazon_url = StringField('Amazon_url',[validators.Length(min=4)])
    author = StringField('Author', [validators.Length(min=1, max=200)])
    genre = StringField('Genre', [validators.Length(min=1, max=200)])

# Add Article
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        amazon_url = form.amazon_url.data
        author = form.author.data
        genre = form.genre.data
        username = session['username']
        print(title,amazon_url,author,genre,username)
        mongo.db.test.articles.insert(
            {'user': username,'title':title,'amazon_url':amazon_url,'author':author,'genre':genre}
        )
        flash('List Created', 'success')

        return redirect(url_for('dashboard',token=x))

    return render_template('add_article.html', form=form)


# Edit List
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    
    # Get form
    form = ArticleForm(request.form)

    article = mongo.db.test.articles.find({'title':id})
    # # Populate article form fields
    # form.title.data = article['title']
    # form.amazon_url.data = article['amazon_url']
    # form.author.data = article['author']
    # form.genre.data = article['genre']
    # username = session['username']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        amazon_url = request.form['amazon_url']
        author = request.form['author']
        genre = request.form['genre']

        mongo.db.test.article.update_one(
            {'title':id},
            {
                '$set': {
                    'title':title,
                    'amazon_url':amazon_url,
                    'author':author,
                    'genre':genre
                }
            }
        )

        flash('List Updated', 'success')

        return redirect(url_for('dashboard',token=x))

    return render_template('edit_article.html', form=form)

# Delete List
@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    
    mongo.db.test.articles.remove({'title':id})

    flash('Article Deleted', 'success')

    return redirect(url_for('dashboard',token=x))

if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)
