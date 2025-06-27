from flask import Flask, render_template, request, redirect, url_for, flash, session
import boto3
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta

app = Flask(__name__)
app.secret_key = "JDehVR/0u+boLBIo/HO7hGU4wgvbTAwe/XqEsoly"
app.permanent_session_lifetime = timedelta(minutes=30)

# AWS S3 Config
S3_BUCKET = 'aws-project-virtualclassroom'
S3_REGION = 'eu-north-1'
s3 = boto3.client('s3', region_name=S3_REGION)

# MySQL Config
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = 'Prachi0328'
DB_NAME = 'my-db'

def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (email, hashed_password))
            conn.commit()
        except Exception as e:
            flash(f"Registration failed: {str(e)}", "danger")
        finally:
            cursor.close()
            conn.close()

        flash("Registered successfully!", "success")
        return render_template('register.html', redirect_to_login=True)
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=%s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['username'] = email
            flash("Login successful!", "success")
            return render_template('login.html', redirect_to_content=True)
        else:
            flash("Invalid credentials", "danger")

    return render_template('login.html')

@app.route('/content', methods=['GET', 'POST'])
def content():
    if 'username' not in session:
        flash('Please log in to access content!', 'warning')
        return redirect(url_for('login'))

    # Example static course data
    courses = [
    {
        'title': 'Python Basics',
        'description': 'Learn the fundamentals of Python.',
        'badge': 'Beginner',
        'image': 'https://www.python.org/static/community_logos/python-logo.png',
        'link': 'python-basics'
    },
    {
        'title': 'Web Development',
        'description': 'Intro to HTML, CSS, and JS.',
        'badge': 'Intermediate',
        'image': 'https://upload.wikimedia.org/wikipedia/commons/6/61/HTML5_logo_and_wordmark.svg',
        'link': 'web-dev'
    },
    {
        'title': 'Machine Learning',
        'description': 'Supervised and unsupervised learning.',
        'badge': 'Advanced',
        'image': 'https://upload.wikimedia.org/wikipedia/commons/0/05/Scikit_learn_logo_small.svg',
        'link': 'ml-course'
    }
]

    # Optional: S3 upload code (if you're keeping file upload)
    if request.method == 'POST':
        file = request.files['file']
        if file:
            if file.content_length > 5 * 1024 * 1024:
                flash("File size exceeds 5MB limit", "danger")
            elif file.mimetype not in ['application/pdf', 'image/jpeg', 'image/png']:
                flash("Invalid file type!", "danger")
            else:
                try:
                    s3.upload_fileobj(file, S3_BUCKET, file.filename)
                    flash("File uploaded successfully", "success")
                except Exception as e:
                    flash(f"Upload failed: {str(e)}", "danger")

    return render_template('content.html', courses=courses)


@app.route('/enroll/<course_name>')
def enroll(course_name):
    return f"You enrolled in: {course_name}"


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'info')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
