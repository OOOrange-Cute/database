import os
import psycopg2
from flask import Flask, request, render_template, redirect, url_for, flash, session
from database import create_connection, insert_user

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # 用于 session 加密

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

# 登录页面
@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        user_name = request.form['user_name']
        password = request.form['password']
        success, message = login(user_name, password)
        if success:
            session['user_name'] = user_name  # 记录登录用户
            flash(message, 'success')
            return redirect(url_for('home_page'))
        else:
            flash(message, 'danger')
    return render_template('login.html')

# 主页
@app.route('/home')
def home_page():
    connection = create_connection()
    if connection is None:
        flash("Error: Unable to connect to the database to generate home page.", 'danger')
        return render_template('home.html', albums=[], artists=[], songs=[])

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

    return render_template('home.html', albums=albums, artists=artists, songs=songs)

# 注销功能
@app.route('/logout')
def logout():
    session.pop('user_name', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login_page'))

if __name__ == "__main__":
    app.run(debug=True)
