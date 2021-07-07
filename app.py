from flask import Flask, render_template, request, redirect, url_for
from collections import OrderedDict
import life_fountain
import mysql.connector
import os

is_development = os.environ.get("FLASK_ENV") == "development"

if is_development:
    cnx = mysql.connector.connect(user="justin", host="localhost", database="thoughts")
else:
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
    if request.method == "POST":
        print("recieved post request")
        name = request.form["name"]
        text = request.form["comment"]
        dispatch(
            "insert into posts_comments (post_url, name, text) values (%s, %s, %s)",
            (thoughtname, name, text),
        )
        cnx.commit()

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
    dispatch("select * from posts_comments where post_url = %s", (thoughtname,))
    for (posted_on, post_url, name, text) in cursor:
        comments.append(
            {"posted_on": posted_on, "post_url": post_url, "name": name, "text": text}
        )

    return render_template(
        "comments.html.jinja", navSections=sections, post=post, comments=comments
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
