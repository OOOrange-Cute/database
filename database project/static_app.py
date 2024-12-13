import os
import psycopg2
from psycopg2 import sql
from jinja2 import Template
from database import create_connection, insert_user  # 从 database.py 导入函数

# 简单的登录逻辑
def login(user_name, password):
    connection = create_connection()
    if connection is None:
        return False, "Database connection failed"

    cursor = connection.cursor()
    try:
        cursor.execute("SELECT * FROM Users WHERE user_name=%s", (user_name,))
        user = cursor.fetchone()

        if user and user[2] == password:
            return True, "Login successful"
        elif not user:
            # 使用 insert_user 函数插入新用户
            insert_user(user_name, password)
            return True, "User created and logged in"
        else:
            return False, "Incorrect password"
    except Exception as e:
        print(f"Error during login operation: {e}")
        return False, "An error occurred"
    finally:
        cursor.close()
        connection.close()

# 生成 HTML 文件
def generate_html():
    # 加载模板并渲染 HTML
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')

    # 登录页面
    with open(os.path.join(templates_dir, 'login.html'), 'w') as f:
        login_template = Template("""
        <!doctype html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>NNMusic - Login</title>
            <style>
                body {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    flex-direction: column;
                    background-color: #f0f0f0;
                    font-family: Arial, sans-serif;
                }
                .login-container {
                    text-align: center;
                    background: #ffffff;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                }
                img {
                    max-width: 400px;
                    margin-bottom: 30px;
                }
                h2 {
                    font-size: 2em;
                    margin-bottom: 20px;
                }
                label {
                    font-size: 1.2em;
                }
                input[type="text"], input[type="password"] {
                    font-size: 1em;
                    padding: 10px;
                    margin: 10px 0;
                    width: 100%;
                    box-sizing: border-box;
                }
                button {
                    font-size: 1.2em;
                    padding: 10px 20px;
                    background-color: #007bff;
                    color: #ffffff;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                }
                button:hover {
                    background-color: #0056b3;
                }
                p {
                    font-size: 1em;
                    color: #666;
                }
            </style>
        </head>
        <body>
            <div class="login-container">
                <img src="../static/images/cover.png" alt="cover image">
                <h2>Login to NNMusic</h2>
                <form action="home.html" method="post">
                    <label for="user_name">User_name:</label>
                    <input type="text" id="user_name" name="user_name" required><br>
                    <label for="password">Password:</label>
                    <input type="password" id="password" name="password" required><br>
                    <button type="submit">Login</button>
                </form>
                <p>Note: If the username does not exist, a new user will be created automatically.</p>
            </div>
        </body>
        </html>
        """)
        f.write(login_template.render())

    # 主页
    connection = create_connection()
    if connection is None:
        print("Error: Unable to connect to the database to generate home page.")
        return
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT * FROM Albums")
        albums = cursor.fetchall()
        cursor.execute("SELECT * FROM Artists")
        artists = cursor.fetchall()
        cursor.execute("SELECT * FROM Songs")
        songs = cursor.fetchall()
    except Exception as e:
        print(f"Error fetching data for home page: {e}")
        albums = []
        artists = []
        songs = []
    finally:
        cursor.close()
        connection.close()

    with open(os.path.join(templates_dir, 'home.html'), 'w') as f:
        home_template = Template("""
        <!doctype html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>NNMusic - Home</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background-color: #f0f0f0;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    margin: 0;
                }
                .cover-image {
                    width: 100%;
                    max-width: 1200px;
                    height: auto;
                    margin-bottom: 30px;
                }
                .container {
                    width: 80%;
                    max-width: 1200px;
                    background: #ffffff;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                    display: flex;
                    justify-content: space-around;
                }
                .box {
                    width: 30%;
                    padding: 20px;
                    border: 2px solid #007bff;
                    border-radius: 10px;
                    text-align: center;
                    cursor: pointer;
                    transition: background-color 0.3s, color 0.3s;
                }
                .box:hover {
                    background-color: #007bff;
                    color: white;
                }
                a {
                    text-decoration: none;
                    color: inherit;
                    display: block;
                    height: 100%;
                }
                h2 {
                    font-size: 2em;
                    margin-bottom: 20px;
                }
            </style>
        </head>
        <body>
            <img src="../static/images/cover.png" alt="NNMusic Cover Image" class="cover-image">
            <div class="container">
                <!-- 推荐专辑方框 -->
                <div class="box">
                    <a href="albums.html">
                        <h2>Recommended Albums</h2>
                    </a>
                </div>

                <!-- 推荐歌手方框 -->
                <div class="box">
                    <a href="artists.html">
                        <h2>Recommended Artists</h2>
                    </a>
                </div>

                <!-- 推荐歌曲方框 -->
                <div class="box">
                    <a href="songs.html">
                        <h2>Recommended Songs</h2>
                    </a>
                </div>
            </div>
        </body>
        </html>
        """)
        f.write(home_template.render())

    # 添加专辑页面
    with open(os.path.join(templates_dir, 'albums.html'), 'w') as f:
        albums_template = Template("""
        <!doctype html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>NNMusic - Albums</title>
        </head>
        <body>
            <h2>All Albums</h2>
            <ul>
                {% for album in albums %}
                    <li>
                        <strong>{{ album[1] }}</strong><br>
                        Artist ID: {{ album[2] }}
                        <form action="play.html" method="get">
                            <button type="submit">View Album</button>
                        </form>
                    </li>
                {% endfor %}
            </ul>
        </body>
        </html>
        """)
        f.write(albums_template.render(albums=albums))

    # 添加歌手页面
    with open(os.path.join(templates_dir, 'artists.html'), 'w') as f:
        artists_template = Template("""
        <!doctype html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>NNMusic - Artists</title>
        </head>
        <body>
            <h2>All Artists</h2>
            <ul>
                {% for artist in artists %}
                    <li>
                        <strong>{{ artist[1] }}</strong><br>
                        Country: {{ artist[3] }}
                        <form action="play.html" method="get">
                            <button type="submit">View Artist</button>
                        </form>
                    </li>
                {% endfor %}
            </ul>
        </body>
        </html>
        """)
        f.write(artists_template.render(artists=artists))

    # 添加歌曲页面
    with open(os.path.join(templates_dir, 'songs.html'), 'w') as f:
        songs_template = Template("""
        <!doctype html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>NNMusic - Songs</title>
        </head>
        <body>
            <h2>All Songs</h2>
            <ul>
                {% for song in songs %}
                    <li>
                        <strong>{{ song[1] }}</strong><br>
                        Genre: {{ song[4] }}<br>
                        <audio controls>
                            <source src="{{ song[5] }}" type="audio/mpeg">
                            Your browser does not support the audio element.
                        </audio>
                    </li>
                {% endfor %}
            </ul>
        </body>
        </html>
        """)
        f.write(songs_template.render(songs=songs))

if __name__ == "__main__":
    generate_html()