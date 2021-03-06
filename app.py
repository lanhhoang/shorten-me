#app.py
from flask import Flask, request, render_template, redirect
from flask_heroku import Heroku
import os
import random
import string
import psycopg2
import urlparse

urlparse.uses_netloc.append("postgres")
url = urlparse.urlparse(os.environ["DATABASE_URL"])

db = psycopg2.connect(
    database=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port
)

#connecting to database
# db = psycopg2.connect("dbname=postgres")
#set this mode so every statement is invoked immediately
db.autocommit = True

#cursor to operate database
cursor = db.cursor()

#setup database
# cursor.execute('''
# DROP TABLE IF EXISTS urls;
# CREATE TABLE urls (
#     id SERIAL PRIMARY KEY NOT NULL,
#     url               TEXT NOT NULL,
#     code              TEXT NOT NULL,
#     hits              INTEGER
# );
# ''')

#Building web app
host = 'https://me-url-shorterner.herokuapp.com/'
# host = 'http://127.0.0.1:5000/'
app = Flask(__name__)
heroku = Heroku(app)

@app.route('/', methods=['GET', 'POST'])
def home():
	if request.method == 'POST':
		original_url = request.form.get('original-url')
		code = code_generator()
		if not valid_url_checker(original_url):
			return render_template('index.html',err_msg = "Please enter a valid URL")
		try:
			cursor.execute("INSERT INTO urls (url,code,hits) VALUES (%s, %s, 0)",(original_url,code))
			print "Insert successfully"
		except:
			print "Cannot insert"
		return render_template('index.html',shorten_url=host+code)
	return render_template('index.html')

@app.route('/<code>')
def original_redirect(code):
	try:
		cursor.execute("SELECT url FROM urls WHERE code = %s",(code,))
		print "Select successfully" 
		original_url = cursor.fetchone()[0]
		cursor.execute("UPDATE urls SET hits = hits + 1 WHERE code = %s",(code,))
		print original_url
		return redirect(original_url)
	except:
		print "Cannot select"
		return redirect('/')

@app.route('/analytics')
def urls_analytics():
	cursor.execute("SELECT * FROM urls ORDER BY id;")
	urls_array = cursor.fetchmany(10)
	print urls_array
	return render_template('analytics.html',host=host,urls_array=urls_array)

@app.route('/<code>+')
def url_analytics(code):
	cursor.execute("SELECT * FROM urls WHERE code = %s",(code,))
	id,original_url,code,hits = cursor.fetchone()
	print cursor.fetchone()
	return render_template('analytics.html',id=id,original_url=original_url,shorten_url=host+code,hits=hits)

def valid_url_checker(original_url):
	protocol_exist = False
	protocols = ["http://","https://"]
	if "." not in original_url:
		return False
	for protocol in protocols:
		if protocol in original_url:
			protocol_exist = True
	return protocol_exist

def code_generator(size=8, letter=string.ascii_letters + string.digits):
	return ''.join(random.choice(letter) for _ in range(size))

if __name__ == '__main__':
	app.run(debug=True)