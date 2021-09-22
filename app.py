from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from collections import OrderedDict
import life_fountain
import mysql.connector
import os
import requests

is_development = os.environ.get("FLASK_ENV") == "development"

if is_development:
    hcaptcha_secret = "0x0000000000000000000000000000000000000000"
    cnx = mysql.connector.connect(user="justin", host="localhost", database="thoughts")
else:
    hcaptcha_secret = os.environ["HCAPTCHA_SECRET"] 
    db_user = os.environ["DB_USER"]
    db_pass = os.environ["DB_PASS"]
    db_socket_dir = os.environ.get("DB_SOCKET_DIR", "/cloudsql")
    cloud_sql_connection_name = os.environ["CLOUD_SQL_CONNECTION_NAME"]
    unix_socket = db_socket_dir + "/" + cloud_sql_connection_name
    cnx = mysql.connector.connect(
        user=db_user,
        host="localhost",
        password=db_pass,
        database="thoughts",
        unix_socket=unix_socket,
    )

cursor = cnx.cursor(buffered=True)

def dispatch(query, params=None):
    print("executing query: " + query)
    cursor.execute(query, params)


app = Flask(__name__)

sections = ["Home", "Life", "Projects", "Thoughts"]

@app.route('/robots.txt')
@app.route('/sitemap.xml')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])

@app.route("/")
@app.route("/home")
def home():
    return render_template("home.html.jinja", navSections=sections, thisSection="Home")


@app.route("/life")
def life():
    fountain = life_fountain.generate()
    return render_template(
        "life.html.jinja", navSections=sections, thisSection="Life", fountain=fountain
    )


@app.route("/projects")
def projects():
    return render_template(
        "projects.html.jinja", navSections=sections, thisSection="Projects"
    )


def retrieve_posts():
    posts = OrderedDict()

    dispatch(
        "select url, title, date, coalesce(ncomments, 0) as ncomments from posts left join (select post_url, count(*) as ncomments from posts_comments group by post_url) comment_count on posts.url = comment_count.post_url order by date desc"
    )
    for (url, name, date, ncomments) in cursor:
        posts[url] = {
            "url": url,
            "name": name,
            "date": date,
            "tags": [],
            "ncomments": ncomments,
        }

    dispatch("select * from posts_tags")
    for (post_url, tag) in cursor:
        print("appending tag: ", post_url, tag)
        posts[post_url]["tags"].append(tag)

    return posts


def parse_tags(query_parameters):
    tag_query = request.args.get("tags")
    if tag_query == None:
        tag_query = []
    else:
        tag_query = tag_query.split(",")
    return tag_query


def filter_posts(posts, request_tags):
    if len(request_tags) > 0:
        to_delete = set([])

        for url in posts:
            if len(set(posts[url]["tags"]) & set(request_tags)) <= 0:
                to_delete.add(url)

        for url in to_delete:
            del posts[url]

    return posts


def paginate(posts, page_length):
    paginated = []
    index = 0
    page = []
    for key in posts:
        if index % page_length == 0 and index > 0:
            print("appending page")
            paginated.append(page)
            page = []
        page.append(posts[key])
        index += 1
    paginated.append(page)
    return paginated


def retrieve_tag_names(request_tags):
    tags = []
    dispatch("select * from tags")
    for (tag_name,) in cursor:
        if tag_name not in request_tags:
            tags.append(tag_name)
    return tags


@app.route("/thoughts")
def thoughts():
    return thoughts_page(1)


@app.route("/thoughts/<int:page_number>")
def thoughts_page(page_number):
    page_length = 1

    posts = retrieve_posts()

    tags_query = request.args.get("tags")
    ### Filter out query parameters, if they exist
    request_tags = parse_tags(tags_query)
    posts = filter_posts(posts, request_tags)
    print(posts)

    paginated = paginate(posts, page_length)
    tags = retrieve_tag_names(request_tags)

    try: 
        posts = paginated[page_number - 1]
        return render_template(
            "thoughts.html.jinja",
            navSections=sections,
            thisSection="Thoughts",
            posts=posts,
            tags=tags,
            request_tags=request_tags,
            tags_query=tags_query,
            page=page_number,
            total_pages=len(paginated),
        )
    except IndexError:
        return redirect(url_for("thoughts_page", page_number=len(paginated)) + "?tags=" + tags_query)



@app.route("/thoughts/archive")
def archive():
    posts = retrieve_posts()
    return render_template("archive.html.jinja", navSections=sections, posts=posts)


@app.route("/thoughts/<thoughtname>", methods=["GET", "POST"])
def comments(thoughtname):
    captcha_verification_failed = False    
    posted_successfully = False    

    user_name = ""
    user_comment_draft = ""

    if request.method == "POST":
        print("recieved post request")
        name = request.form["name"]
        text = request.form["comment"]
        hcaptcha_token = request.form['h-captcha-response']

        data = {}
        data["response"] = hcaptcha_token
        data["secret"] = hcaptcha_secret

        response = requests.post("https://hcaptcha.com/siteverify", data=data)

        print(response.json())
        success = response.json()['success']
        # test response in JSON format

        if success:
            dispatch(
                "insert into posts_comments (post_url, name, text) values (%s, %s, %s)",
                (thoughtname, name, text),
            )
            cnx.commit()
            posted_successfully = True
        else: 
            captcha_verification_failed = True
            user_name = name
            user_comment_draft = text

    dispatch("select * from posts where url = %s order by date desc", (thoughtname,))

    if cursor.rowcount == 0:
        return render_template("404.html.jinja", navSections=sections, resource_name=thoughtname)

    for (url, name, date, html) in cursor:
        post = {"url": url, "name": name, "date": date, "html": html, "tags": []}

    dispatch("select * from posts_tags where post_url = %s", (thoughtname,))
    for (post_url, tag) in cursor:
        print("appending tag: ", post_url, tag)
        post["tags"].append(tag)

    comments = []
    dispatch("select * from posts_comments where post_url = %s and hidden = false", (thoughtname,))
    for (posted_on, post_url, name, text, hidden) in cursor:
        comments.append(
            {"posted_on": posted_on, "post_url": post_url, "name": name, "text": text}
        )

    return render_template(
        "comments.html.jinja"
        , navSections=sections
        , post=post
        , comments=comments
        , captcha_verification_failed=captcha_verification_failed
        , posted_successfully=posted_successfully
        , user_name=user_name
        , user_comment_draft=user_comment_draft)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
