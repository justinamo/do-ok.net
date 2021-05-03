from flask import Flask, render_template
app = Flask(__name__)

sections = ['Home', 'Projects', 'Thoughts', 'Contact']

@app.route('/')
@app.route('/home')
def home():
  return render_template('home.html', navSections=sections, thisSection='Home')

@app.route('/projects')
def projects():
  return render_template('projects.html', navSections=sections, thisSection='Projects')

@app.route('/thoughts')
def thoughts():
  return render_template('thoughts.html', navSections=sections, thisSection='Thoughts')

@app.route('/thoughts/<thoughtname>')
def thoughtdetail(thoughtname):
  return render_template(['comments.html', 'thoughts/' + thoughtname + '-comments.html'], navSections=sections)

@app.route('/contact')
def contact():
  return render_template('contact.html', navSections=sections, thisSection='Contact')
