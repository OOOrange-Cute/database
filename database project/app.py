from flask import Flask, request, redirect, render_template, flash, jsonify, session, url_for
import database as db
import psycopg2
import psycopg2.extras
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.secret_key = 'super_secret_key'  # 用于会话管理和消息提示


# 开始页面：跳转到登录页面
@app.route('/')
def index():
    print("Redirecting to login page...")
    return redirect('/login')


# 注册页面的路由
@app.route('/register', methods=['GET', 'POST'])
@app.route('/register.html', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # 获取表单数据
        user_name = request.form['user_name']
        password = request.form['password']
        email = request.form['email']
        tel = request.form['tel']
        year = int(request.form['year'])
        month = int(request.form['month'])
        day = int(request.form['day'])

        # 检查用户名是否已存在
        with db.get_db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT user_name FROM Users WHERE user_name = %s", (user_name,))
            existing_user = cursor.fetchone()
            cursor.close()

        if existing_user:
            flash("用户名已存在，请选择其他用户名。", "error")
            print(f"注册失败：用户名 '{user_name}' 已存在。")
            return redirect(url_for('register'))

        # 哈希密码
        hashed_password = generate_password_hash(password)

        print(f"注册新用户: {user_name}, 哈希密码: {hashed_password}, 邮箱: {email}, 电话: {tel}, 生日: {year}-{month}-{day}")
        db.insert_user(user_name, hashed_password, email, tel, year, month, day)
        flash("注册成功！", "success")
        print(f"用户 '{user_name}' 注册成功。")
        return redirect(url_for('register'))
    return render_template('register.html')  # GET 请求，显示注册页面

# 登录页面的路由
@app.route('/login', methods=['GET', 'POST'])
@app.route('/login.html', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_name = request.form['user_name']
        password = request.form['password']

        print(f"用户尝试登录: {user_name}")
        with db.get_db_connection() as connection:
            user_id = db.validate_user(user_name, password, connection)

        if user_id:
            session['user_id'] = user_id  # 将 user_id 存入会话
            session['user_name'] = user_name  # 将 user_name 存入会话
            flash("登录成功！", "success")
            print(f"用户 '{user_name}' 登录成功，用户ID: {user_id}")
            return redirect(url_for('login'))
        else:
            flash('用户名或密码错误，登录失败！', 'error')
            print(f"用户 '{user_name}' 登录失败：用户名或密码错误。")
            return redirect(url_for('login'))
    return render_template('login.html')  # GET 请求，显示登录页面


# 默认账号登录的路由
@app.route('/default_login', methods=['GET'])
def default_login():
    default_user = 'Tank'
    default_password = 'Tank2028085771'

    print(f"默认用户尝试登录: {default_user}")
    with db.get_db_connection() as connection:
        user_id = db.validate_user(default_user, default_password, connection)

    if user_id:
        session['user_id'] = user_id  # 将 user_id 存入会话
        session['user_name'] = default_user  # 将 user_name 存入会话
        flash("默认账号登录成功！", "success")
        print(f"默认用户 '{default_user}' 登录成功，用户ID: {user_id}")
        return redirect(url_for('login'))
    else:
        flash('默认账号登录失败！', 'error')
        print(f"默认用户 '{default_user}' 登录失败。")
        return redirect(url_for('login'))

# 主页
@app.route('/home', methods=['GET', 'POST'])
@app.route('/home.html', methods=['GET', 'POST'])
def home():
    user_id = session.get('user_id')
    user_name = session.get('user_name')
    user_favorites = []  # 设置默认值，防止UnboundLocalError

    if not user_id or not user_name:
        flash("请先登录。", "error")
        print("用户未登录，重定向到登录页面。")
        return redirect(url_for('login'))

    print(f"访问主页，用户ID: {user_id}, 用户名: {user_name}")

    with db.get_db_connection() as conn:
        try:
            # 获取用户收藏
            user_favorites = db.get_user_favorites(conn, user_name)
            print(f"用户 '{user_name}' 的收藏: {user_favorites}")

            # 获取筛选选项
            countries = db.get_unique_artist_countries(conn)
            genders = db.get_unique_artist_genders(conn)
            languages = db.get_unique_song_languages(conn)
            genres = db.get_unique_song_genres(conn)
            print(f"获取筛选选项 - 国籍: {countries}, 性别: {genders}, 语言: {languages}, 风格: {genres}")

            # 不获取所有歌曲、专辑、艺术家
            songs = []
            albums = []
            artists = []
            print("主页不展示所有内容，等待搜索。")
        except Exception as e:
            print(f"主页加载错误: {e}")
            flash(f"主页加载错误: {e}", "error")
            songs = []
            albums = []
            artists = []
            countries = []
            genders = []
            languages = []
            genres = []

    return render_template('home.html',
                           user_id=user_id,
                           user_name=user_name,
                           Favorites=user_favorites,
                           songs=songs,
                           albums=albums,
                           artists=artists,
                           countries=countries,
                           genders=genders,
                           languages=languages,
                           genres=genres)


# 显示个人资料
@app.route('/profile/<int:user_id>')
@app.route('/profile.html/<int:user_id>')
def profile(user_id):
    user_name = session.get('user_name')
    if not user_name:
        flash("请先登录。", "error")
        print("用户未登录，无法访问个人资料。")
        return redirect(url_for('login'))

    print(f"访问用户 '{user_name}' 的个人资料。")
    user_info = db.get_user_info(user_name)
    if user_info is None or user_info[0] != user_id:
        flash("无法访问该用户的个人资料。", "error")
        return redirect(url_for('login'))
    return render_template('profile.html', user_info=user_info)


# 显示编辑个人资料表单
@app.route('/edit_profile/<int:user_id>', methods=['GET'])
def edit_profile(user_id):
    user_name = session.get('user_name')
    if not user_name:
        flash("请先登录。", "error")
        print("用户未登录，无法编辑个人资料。")
        return redirect(url_for('login'))

    user_info = db.get_user_info(user_name)
    if user_info is None or user_info[0] != user_id:
        flash("无法编辑该用户的个人资料。", "error")
        return redirect(url_for('profile', user_id=user_id))

    return render_template('edit_profile.html', user_info=user_info)


# 处理编辑个人资料的表单提交
@app.route('/update_profile/<int:user_id>', methods=['POST'])
def update_profile(user_id):
    user_name = session.get('user_name')
    if not user_name:
        flash("请先登录。", "error")
        print("用户未登录，无法更新个人资料。")
        return redirect(url_for('login'))

    user_info = db.get_user_info(user_name)
    if user_info is None or user_info[0] != user_id:
        flash("无法更新该用户的个人资料。", "error")
        return redirect(url_for('profile', user_id=user_id))

    # 获取表单数据
    new_username = request.form.get('username')
    new_email = request.form.get('email')
    new_tel = request.form.get('tel')
    new_year = request.form.get('year')
    new_month = request.form.get('month')
    new_day = request.form.get('day')

    # 验证输入数据（这里可以根据需要添加更多的验证）
    if not all([new_username, new_email, new_tel, new_year, new_month, new_day]):
        flash("所有字段都是必填的。", "error")
        return redirect(url_for('edit_profile', user_id=user_id))

    try:
        new_year = int(new_year)
        new_month = int(new_month)
        new_day = int(new_day)
    except ValueError:
        flash("年份、月份和日期必须是数字。", "error")
        return redirect(url_for('edit_profile', user_id=user_id))

    # 更新数据库
    success = db.update_user_info(user_id, new_username, new_email, new_tel, new_year, new_month, new_day)
    if success:
        flash("个人资料已成功更新。", "success")
        # 更新会话中的用户名，如果用户名被更改
        session['user_name'] = new_username
        return redirect(url_for('profile', user_id=user_id))
    else:
        flash("更新个人资料时出错。", "error")
        return redirect(url_for('edit_profile', user_id=user_id))


# 登录后显示所有歌曲的路由
@app.route('/songs', methods=['GET', 'POST'])
@app.route('/songs.html', methods=['GET', 'POST'])
def songs():
    user_id = session.get('user_id')
    user_name = session.get('user_name')

    if not user_id or not user_name:
        flash("请先登录。", "error")
        print("用户未登录，重定向到登录页面。")
        return redirect(url_for('login'))

    with db.get_db_connection() as conn:
        all_songs = []  # 初始化 all_songs 以避免未定义错误
        if not conn:
            flash("数据库连接失败。", "error")
            print("数据库连接失败，无法获取歌曲列表。")
            return render_template('songs.html', songs=[], user_id=user_id, user_name=user_name)
        try:
            all_songs = db.get_all_songs(conn)  # 调用 get_all_songs 获取歌曲信息
            favorites = db.get_user_favorites(conn, user_name)
            favorite_song_titles = set(song['title'] for song in favorites)
            # 为每首歌曲添加 is_favorited 属性
            for song in all_songs:
                song['is_favorited'] = song['title'] in favorite_song_titles
            print(f"获取所有歌曲，共 {len(all_songs)} 首。")
        except Exception as e:
            print(f"Error fetching songs: {e}")
            flash(f"获取歌曲时发生错误: {e}", "error")
            all_songs = []

    return render_template('songs.html', songs=all_songs, user_id=user_id, user_name=user_name)

# 专辑页面
@app.route('/albums', methods=['GET', 'POST'])
@app.route('/albums.html', methods=['GET', 'POST'])
def albums():
    with db.get_db_connection() as conn:
        if not conn:
            flash("数据库连接失败。", "error")
            print("数据库连接失败，无法获取专辑列表。")
            return render_template('albums.html')
        try:
            # 获取所有专辑及其艺术家信息
            album_list = db.get_all_albums(conn)
            print(f"获取所有专辑，共 {len(album_list)} 个。")
            if album_list:
                return render_template('albums.html', albums=album_list)
            else:
                flash("数据库中未找到专辑。", "error")
                print("数据库中未找到任何专辑。")
        except Exception as e:
            print(f"Error fetching albums: {e}")
            flash(f"获取专辑信息出错: {e}", "error")
        return render_template('albums.html')


# 专辑中歌曲页面
@app.route('/album/<int:album_id>/songs', methods=['GET'])
@app.route('/album/<int:album_id>/songs.html', methods=['GET'])
def album_songs(album_id):
    # 获取当前用户的ID和用户名
    user_id = session.get('user_id')
    user_name = session.get('user_name')

    # 检查用户是否已登录
    if not user_id or not user_name:
        flash("请先登录。", "error")
        print("用户未登录，重定向到登录页面。")
        return redirect(url_for('login'))

    with db.get_db_connection() as conn:
        if not conn:
            flash("数据库连接失败。", "error")
            print("数据库连接失败，无法获取歌曲列表。")
            return render_template('album_songs.html', songs=[], album_name="", album_id=album_id, artist_name="", artist_bio="", user_id=user_id, user_name=user_name)
        try:
            # 获取该专辑的所有歌曲
            songs = db.get_songs_by_album(conn, album_id)
            print(f"获取专辑ID {album_id} 的歌曲，共 {len(songs)} 首。")

            # 获取该专辑的名称
            album_name = db.get_album_name_by_id(conn, album_id)
            print(f"专辑ID {album_id} 的名称: {album_name}")

            # 获取用户的收藏歌曲
            favorites = db.get_user_favorites(conn, user_name)
            favorite_song_ids = set(song['song_id'] for song in favorites)
            print(f"用户 '{user_name}' 的收藏歌曲ID: {favorite_song_ids}")

            # 为每首歌曲添加 is_favorited 属性
            for song in songs:
                song['is_favorited'] = song['song_id'] in favorite_song_ids

            # 获取艺术家信息（假设每首歌有 artist_name 和 artist_bio）
            # 如果专辑有一个主要艺术家，可以通过专辑获取
            if songs:
                # 假设所有歌曲的 artist_name 和 artist_bio 相同
                artist_name = songs[0].get('artist_name', '')
                artist_bio = db.get_artist_bio_by_name(conn, artist_name)
            else:
                artist_name = ""
                artist_bio = ""

        except Exception as e:
            print(f"Error fetching songs for album {album_id}: {e}")
            flash(f"获取专辑 {album_id} 歌曲信息出错: {e}", "error")
            songs = []
            album_name = ""
            artist_name = ""
            artist_bio = ""

    # 返回渲染的 HTML 页面，将歌曲数据传递给前端进行显示
    return render_template('album_songs.html',
                           songs=songs,
                           album_name=album_name,
                           album_id=album_id,
                           artist_name=artist_name,
                           artist_bio=artist_bio,
                           user_id=user_id,
                           user_name=user_name)



# 艺术家页面
@app.route('/artists', methods=['GET', 'POST'])
@app.route('/artists.html', methods=['GET', 'POST'])
def artists():
    with db.get_db_connection() as conn:
        try:
            # 获取所有艺术家信息，包括国籍等信息
            artists = db.get_all_artists(conn)  # 通过 get_all_artists 获取艺术家信息
            print(f"获取所有艺术家，共 {len(artists)} 位。")
        except Exception as e:
            print(f"Error fetching artists: {e}")
            artists = []
    # 返回渲染的 HTML 页面，将艺术家数据传递给前端进行显示
    return render_template('artists.html', artists=artists)


# 艺术家歌曲页面
@app.route('/artist/<int:artist_id>/songs', methods=['GET'])
@app.route('/artist/<int:artist_id>/songs.html', methods=['GET'])
def artist_songs(artist_id):
    # 获取当前用户的ID和用户名
    user_id = session.get('user_id')
    user_name = session.get('user_name')

    # 检查用户是否已登录
    if not user_id or not user_name:
        flash("请先登录。", "error")
        print("用户未登录，重定向到登录页面。")
        return redirect(url_for('login'))

    with db.get_db_connection() as conn:
        if not conn:
            flash("数据库连接失败。", "error")
            print("数据库连接失败，无法获取歌曲列表。")
            return render_template('artist_songs.html', songs=[], artist_id=artist_id, artist_name="", artist_bio="", user_id=user_id, user_name=user_name)
        try:
            # 获取该艺术家的所有歌曲信息
            songs = db.get_songs_by_artist(conn, artist_id)  # 通过 artist_id 获取该艺术家的所有歌曲
            artist_name, artist_bio = db.get_artist_info_by_artist(conn, artist_id)
            print(f"艺术家ID {artist_id} 的歌曲数量: {len(songs)}")
            print(f"艺术家名称: {artist_name}, 简介: {artist_bio}")

            # 获取用户的收藏歌曲
            favorites = db.get_user_favorites(conn, user_name)
            favorite_song_ids = set(song['song_id'] for song in favorites)

            # 为每首歌曲添加 is_favorited 属性
            for song in songs:
                song['is_favorited'] = song['song_id'] in favorite_song_ids

            print(f"用户 '{user_name}' 的收藏歌曲ID: {favorite_song_ids}")

        except Exception as e:
            print(f"Error fetching songs for artist {artist_id}: {e}")
            songs = []
            artist_name = ""
            artist_bio = ""

    # 返回渲染的 HTML 页面，将歌曲数据传递给前端进行显示
    return render_template('artist_songs.html',
                           songs=songs,
                           artist_id=artist_id,
                           artist_name=artist_name,
                           artist_bio=artist_bio,
                           user_id=user_id,
                           user_name=user_name)



# -----------搜索功能页面-----------------
@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '').strip()
    country = request.args.get('country', '').strip()
    gender = request.args.get('gender', '').strip()
    language = request.args.get('language', '').strip()
    genre = request.args.get('genre', '').strip()

    print(f"搜索请求 - 查询: '{query}', 国籍: '{country}', 性别: '{gender}', 语言: '{language}', 风格: '{genre}'")

    with db.get_db_connection() as conn:
        if not conn:
            print("数据库连接失败，无法进行搜索。")
            return jsonify({'error': 'Database connection failed'}), 500
        try:
            # 初始化搜索结果
            songs = []
            albums = []
            artists = []

            if query or country or gender or language or genre:
                # 搜索歌曲，应用语言和风格筛选
                if query or language or genre:
                    songs = db.search_songs_with_filters(
                        query=query if query else None,
                        language=language if language else None,
                        genre=genre if genre else None,
                        connection=conn
                    )
                    print(f"搜索歌曲结果: {len(songs)} 首歌曲匹配。")

                # 搜索专辑，仅基于查询关键词
                if query:
                    albums = db.search_albums(query, conn)
                    print(f"搜索专辑结果: {len(albums)} 个专辑匹配。")

                # 搜索艺术家，应用国籍和性别筛选
                if query or country or gender:
                    artists = db.search_artists_with_filters(
                        query=query if query else None,
                        country=country if country else None,
                        gender=gender if gender else None,
                        connection=conn
                    )
                    print(f"搜索艺术家结果: {len(artists)} 个艺术家匹配。")
            else:
                # 如果没有搜索关键词和筛选条件，不返回任何结果
                print("搜索框为空，且没有筛选条件，返回空结果。")

            # 返回所有搜索结果
            return jsonify({
                'songs': [dict(song) for song in songs],
                'albums': [dict(album) for album in albums],
                'artists': [dict(artist) for artist in artists],
            }), 200
        except Exception as e:
            print(f"搜索时发生错误: {e}")
            return jsonify({'error': f"搜索时发生错误: {e}"}), 500


# -----------收藏相关功能页面-----------------

@app.route('/favorites/<string:user_name>', methods=['GET'])
def favorites(user_name):
    with db.get_db_connection() as conn:
        try:
            # 获取用户收藏的歌曲信息
            songs = db.get_user_favorites(conn, user_name)
            print(f"用户 '{user_name}' 的收藏: {songs}")
            return render_template('favorites.html', songs=songs, user_name=user_name)
        except Exception as e:
            print(f"Error fetching favorites for user '{user_name}': {e}")
            flash(f"获取收藏歌曲失败: {e}", "error")
            return render_template('favorites.html', songs=[], user_name=user_name)


# 切换收藏（添加或移除）
@app.route('/toggle_favorite', methods=['POST'])
def toggle_favorite():
    data = request.get_json()
    user_name = data.get('user_name')
    song_name = data.get('song_name')
    artist_name = data.get('artist_name')

    print(f"切换收藏 - 用户: {user_name}, 歌曲: {song_name}, 艺术家: {artist_name}")

    with db.get_db_connection() as connection:
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            # 获取 user_id
            cursor.execute("SELECT user_id FROM Users WHERE user_name = %s", (user_name,))
            user = cursor.fetchone()
            if not user:
                message = f"用户 '{user_name}' 未找到。"
                print(message)
                return jsonify({'success': False, 'message': message}), 404
            user_id = user['user_id']

            # 获取 song_id，确保歌曲名和艺术家名匹配
            cursor.execute(
                """
                SELECT Songs.song_id
                FROM Songs
                JOIN Artists ON Songs.artist_id = Artists.artist_id
                WHERE Songs.title = %s AND Artists.name = %s
                """,
                (song_name, artist_name)
            )
            song = cursor.fetchone()
            if not song:
                message = f"歌曲 '{song_name}' 由艺术家 '{artist_name}' 演唱的记录未找到。"
                print(message)
                return jsonify({'success': False, 'message': message}), 404
            song_id = song['song_id']

            # 检查是否已经收藏
            cursor.execute(
                """
                SELECT 1 FROM Favorites WHERE user_id = %s AND song_id = %s
                """,
                (user_id, song_id)
            )
            favorite_exists = cursor.fetchone()

            if favorite_exists:
                # 已经收藏，执行移除操作
                cursor.execute(
                    """
                    DELETE FROM Favorites WHERE user_id = %s AND song_id = %s
                    """,
                    (user_id, song_id)
                )
                connection.commit()
                message = f"歌曲 '{song_name}' 已从用户 '{user_name}' 的收藏中移除。"
                print(message)
                return jsonify({'success': True, 'action': 'removed', 'message': message}), 200
            else:
                # 未收藏，执行添加操作
                cursor.execute(
                    """
                    INSERT INTO Favorites (user_id, song_id)
                    VALUES (%s, %s)
                    """,
                    (user_id, song_id)
                )
                connection.commit()
                message = f"歌曲 '{song_name}' 已添加到用户 '{user_name}' 的收藏中。"
                print(message)
                return jsonify({'success': True, 'action': 'added', 'message': message}), 200

        except Exception as e:
            print(f"切换收藏时发生错误: {e}")
            connection.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500
        finally:
            cursor.close()


# -----------播放页面-----------------


# 播放页面
@app.route('/play/<int:song_id>', methods=['GET'])
@app.route('/play/<int:song_id>.html', methods=['GET'])
def play(song_id):
    with db.get_db_connection() as conn:
        try:
            song = db.get_song_by_id(conn, song_id)  # 获取歌曲信息
            print(f"播放歌曲ID {song_id}: {song}")
            if song:
                return render_template('play.html', song=song)
            else:
                flash("未找到歌曲", "error")
                print(f"未找到歌曲ID {song_id}。")
        except Exception as e:
            flash(f"获取歌曲信息失败: {e}", "error")
            print(f"Error fetching song {song_id}: {e}")
    return redirect(url_for('songs'))


@app.route('/play/<int:song_id>', methods=['GET'])
def play_song(song_id):
    with db.get_db_connection() as conn:
        try:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute("""
                SELECT Songs.song_id, Songs.title, Artists.name AS artist_name, Albums.title AS album_title, 
                       Songs.genre, Songs.language, Songs.audio_url
                FROM Songs
                JOIN Artists ON Songs.artist_id = Artists.artist_id
                JOIN Albums ON Songs.album_id = Albums.album_id
                WHERE Songs.song_id = %s
            """, (song_id,))
            song = cursor.fetchone()
            if song:
                return render_template('play.html', song=song)
            else:
                flash("未找到该歌曲。", "error")
                return redirect(url_for('home'))
        except Exception as e:
            print(f"播放歌曲时发生错误: {e}")
            flash("播放歌曲时发生错误。", "error")
            return redirect(url_for('home'))
        finally:
            cursor.close()



if __name__ == '__main__':
    app.run(debug=True)
