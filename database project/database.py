import psycopg2
import psycopg2.extras  # 导入用于字典游标的模块
from contextlib import contextmanager
import random

# -----------数据库初始化-----------------
# 数据库连接设置
@contextmanager
def get_db_connection():
    connection = None
    try:
        connection = psycopg2.connect(
            database="postgres",
            user="admin",
            password="admin@123",
            host="192.168.135.134",
            port="7654",
            client_encoding="UTF8"
        )
        print("Database connection successful.")
        yield connection
    except Exception as e:
        print(f"Database connection failed: {e}")
        raise  # 抛出异常以便处理
    finally:
        if connection:
            connection.close()
            print("Database connection closed.")


# 删除所有数据库表
def drop_all_tables():
    with get_db_connection() as connection:
        cursor = connection.cursor()
        commands = [
            '''
            DROP TABLE IF EXISTS PlaylistSongs CASCADE
            ''',
            '''
            DROP TABLE IF EXISTS Playlists CASCADE
            ''',
            '''
            DROP TABLE IF EXISTS Songs CASCADE
            ''',
            '''
            DROP TABLE IF EXISTS Albums CASCADE
            ''',
            '''
            DROP TABLE IF EXISTS Artists CASCADE
            ''',
            '''
            DROP TABLE IF EXISTS Users CASCADE
            ''',
            '''
            DROP TABLE IF EXISTS Favorites CASCADE
            '''
        ]
        try:
            for command in commands:
                cursor.execute(command)
            connection.commit()
        except Exception as e:
            print(f"Error occurred: {e}")
        finally:
            cursor.close()


# 创建数据库表
def create_tables():
    with get_db_connection() as connection:
        cursor = connection.cursor()
        commands = [
            '''
            CREATE TABLE IF NOT EXISTS Artists (
                artist_id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                bio TEXT,
                country VARCHAR(100),
                gender VARCHAR(100)
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS Albums (
                album_id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                artist_id INT,
                FOREIGN KEY (artist_id) REFERENCES Artists(artist_id)
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS Users (
                user_id SERIAL PRIMARY KEY,
                user_name VARCHAR(30) NOT NULL UNIQUE,
                password VARCHAR(15) NOT NULL,
                email VARCHAR(30),
                tel VARCHAR(11),
                year INT,
                month INT,
                day INT
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS Songs (
                song_id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL UNIQUE,
                artist_id INT,
                album_id INT,
                genre VARCHAR(100),
                audio_url VARCHAR(255) NOT NULL,
                language VARCHAR(100),
                FOREIGN KEY (artist_id) REFERENCES Artists(artist_id),
                FOREIGN KEY (album_id) REFERENCES Albums(album_id)
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS Playlists (
                playlist_id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS Favorites (
                user_id INT NOT NULL,
                song_id INT NOT NULL,
                PRIMARY KEY (user_id, song_id),
                FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (song_id) REFERENCES Songs(song_id) ON DELETE CASCADE
            )
            '''
        ]
        try:
            for command in commands:
                cursor.execute(command)
            connection.commit()
        except Exception as e:
            print(f"Error occurred: {e}")
        finally:
            cursor.close()

# -----------登录注册相关函数-----------------
# 验证用户信息
def validate_user(user_name, password, connection):
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT password, user_id FROM Users WHERE user_name=%s", (user_name,))
        result = cursor.fetchone()
        if result and result[0] == password:
            return result[1]
        else:
            return None
    finally:
        cursor.close()


# 更新用户信息
def update_user_info(user_id, user_name, email, tel, year, month, day):
    with get_db_connection() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                UPDATE Users
                SET user_name = %s,
                    email = %s,
                    tel = %s,
                    year = %s,
                    month = %s,
                    day = %s
                WHERE user_id = %s
                """,
                (user_name, email, tel, year, month, day, user_id)
            )
            connection.commit()
            print(f"用户ID {user_id} 的信息已更新。")
            return True
        except Exception as e:
            print(f"更新用户ID {user_id} 信息时出错: {e}")
            connection.rollback()
            return False
        finally:
            cursor.close()


# -----------去除信息-----------------
# 移除用户收藏的歌曲（如果需要独立的移除功能）
def remove_favorites(user_name, song_name):
    with get_db_connection() as connection:
        cursor = connection.cursor()
        try:
            # 获取 user_id
            cursor.execute("SELECT user_id FROM Users WHERE user_name = %s", (user_name,))
            user = cursor.fetchone()
            if not user:
                print(f"用户 '{user_name}' 未找到。")
                return
            user_id = user[0]

            # 获取 song_id，确保歌曲名和艺术家名匹配
            cursor.execute(
                """
                SELECT Songs.song_id
                FROM Songs
                JOIN Artists ON Songs.artist_id = Artists.artist_id
                WHERE Songs.title = %s
                """,
                (song_name,)
            )
            song = cursor.fetchone()
            if not song:
                print(f"歌曲 '{song_name}' 的记录未找到。")
                return
            song_id = song[0]

            # 删除 Favorites 表中的记录
            cursor.execute(
                """
                DELETE FROM Favorites WHERE user_id = %s AND song_id = %s
                """,
                (user_id, song_id)
            )
            connection.commit()
            if cursor.rowcount > 0:
                print(f"歌曲 '{song_name}' 已从用户 '{user_name}' 的收藏中移除。")
            else:
                print(f"未找到歌曲 '{song_name}' 在用户 '{user_name}' 的收藏中。")
        except Exception as e:
            print(f"移除收藏时发生错误: {e}")
            connection.rollback()
        finally:
            cursor.close()


# -----------获取信息get-----------------
# 获取当前用户的信息
def get_user_info(user_name):
    with get_db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Users WHERE user_name = %s", (user_name,))
        user = cursor.fetchone()
        return user


# 获取用户收藏的歌曲
def get_user_favorites(connection, user_name):
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        # 首先获取 user_id
        cursor.execute("SELECT user_id FROM Users WHERE user_name = %s", (user_name,))
        user = cursor.fetchone()

        if not user:
            print(f"用户 '{user_name}' 未找到。")
            return []

        user_id = user['user_id']

        # 使用 user_id 获取收藏的歌曲详情
        query = """
            SELECT 
                Songs.song_id, 
                Songs.title, 
                Artists.name AS artist_name, 
                Albums.title AS album_title, 
                Songs.genre, 
                Songs.language, 
                Songs.audio_url
            FROM Favorites
            JOIN Songs ON Favorites.song_id = Songs.song_id
            JOIN Artists ON Songs.artist_id = Artists.artist_id
            LEFT JOIN Albums ON Songs.album_id = Albums.album_id
            WHERE Favorites.user_id = %s
        """
        cursor.execute(query, (user_id,))
        favorites = cursor.fetchall()
        return favorites
    except Exception as e:
        print(f"获取用户 '{user_name}' 收藏的歌曲时出错: {e}")
        return []
    finally:
        cursor.close()


# 获取所有歌曲并展示，联合查询艺术家姓名和专辑名称
def get_all_songs(conn):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cursor.execute("""
            SELECT 
                Songs.song_id, 
                Songs.title, 
                Artists.name AS artist_name, 
                Albums.title AS album_title, 
                Songs.genre, 
                Songs.language, 
                Songs.audio_url
            FROM Songs
            JOIN Artists ON Songs.artist_id = Artists.artist_id
            LEFT JOIN Albums ON Songs.album_id = Albums.album_id
        """)
        songs = cursor.fetchall()
        return songs
    except Exception as e:
        print(f"获取所有歌曲时出错: {e}")
        return []
    finally:
        cursor.close()



# 获得详细歌曲信息
def get_song_by_id(connection, song_id):
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        query = """
            SELECT Songs.song_id, Songs.title, Songs.artist_id, Artists.name AS artist_name, Songs.language,
                   Songs.album_id, Albums.title AS album_title, Songs.genre, Songs.audio_url
            FROM Songs
            JOIN Artists ON Songs.artist_id = Artists.artist_id
            JOIN Albums ON Songs.album_id = Albums.album_id
            WHERE Songs.song_id = %s
        """
        cursor.execute(query, (song_id,))
        song = cursor.fetchone()
        return song
    except Exception as e:
        print(f"Error while getting song by id {song_id}: {e}")
        return None
    finally:
        cursor.close()


# 获取所有专辑并展示，联合查询歌手姓名和歌曲数量
def get_all_albums(connection):
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        query = """
            SELECT Albums.album_id, Albums.title AS album_title, Artists.name AS artist_name
            FROM Albums
            JOIN Artists ON Albums.artist_id = Artists.artist_id
        """
        cursor.execute(query)
        albums = cursor.fetchall()
        return albums
    except Exception as e:
        print(f"Error while getting albums: {e}")
        return []
    finally:
        cursor.close()


# 根据专辑查询歌曲
def get_songs_by_album(connection, album_id):
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        query = """
            SELECT Songs.song_id, Songs.title, Songs.artist_id, Artists.name AS artist_name,
                   Songs.album_id, Albums.title AS album_title, Songs.genre, Songs.audio_url
            FROM Songs
            JOIN Artists ON Songs.artist_id = Artists.artist_id
            JOIN Albums ON Songs.album_id = Albums.album_id
            WHERE Songs.album_id = %s
        """
        cursor.execute(query, (album_id,))
        songs = cursor.fetchall()
        return songs
    except Exception as e:
        print(f"Error while getting songs for album {album_id}: {e}")
        return []
    finally:
        cursor.close()


# 根据id获取专辑名称
def get_album_name_by_id(conn, album_id):
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT title FROM Albums WHERE album_id = %s
        """, (album_id,))
        album = cursor.fetchone()
        if album:
            return album[0]
        else:
            return ""
    except Exception as e:
        print(f"获取专辑名称时出错: {e}")
        return ""
    finally:
        cursor.close()

def get_artist_bio_by_name(conn, artist_name):
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT bio FROM Artists WHERE name = %s
        """, (artist_name,))
        artist = cursor.fetchone()
        if artist:
            return artist[0]
        else:
            return ""
    except Exception as e:
        print(f"获取艺术家简介时出错: {e}")
        return ""
    finally:
        cursor.close()

# 获取所有艺术家信息
def get_all_artists(connection):
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        query = """
            SELECT artist_id, name, country, gender
            FROM Artists
        """
        cursor.execute(query)
        artists = cursor.fetchall()  # 获取所有艺术家信息
        return artists
    except Exception as e:
        print(f"Error while getting artists: {e}")
        return []
    finally:
        cursor.close()


def get_songs_by_artist(connection, artist_id):
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        query = """
            SELECT Songs.song_id, Songs.title, Songs.artist_id, Artists.name AS artist_name, Songs.language,
                   Songs.album_id, Albums.title AS album_title, Songs.genre, Songs.audio_url
            FROM Songs
            JOIN Artists ON Songs.artist_id = Artists.artist_id
            JOIN Albums ON Songs.album_id = Albums.album_id
            WHERE Songs.artist_id = %s
        """
        cursor.execute(query, (artist_id,))
        songs = cursor.fetchall()
        return songs
    except Exception as e:
        print(f"Error while getting songs by artist: {e}")
        return []
    finally:
        cursor.close()


def get_artist_info_by_artist(connection, artist_id):
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        query = """
            SELECT Artists.name AS artist_name, bio
            FROM Artists
            WHERE Artists.artist_id = %s
        """
        cursor.execute(query, (artist_id,))
        result = cursor.fetchone()
        artist_name = result['artist_name']
        artist_bio = result['bio']
        return artist_name, artist_bio
    except Exception as e:
        print(f"Error while getting songs by artist: {e}")
        return []
    finally:
        cursor.close()


# -----------插入功能-----------------

# 插入用户数据
def insert_user(user_name, password, email, tel, year, month, day):
    with get_db_connection() as connection:
        cursor = connection.cursor()
        """id = random.uniform(1, 1000000)"""
        try:
            # 首先检查用户名是否已存在
            cursor.execute("SELECT * FROM Users WHERE user_name = %s", (user_name,))
            if cursor.fetchone():
                print(f"User '{user_name}' already exists.")
            else:
                # 用户不存在，插入新用户
                cursor.execute(
                    """
                    INSERT INTO Users (user_name, password, email, tel, year, month, day)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (user_name, password, email, tel, year, month, day)
                )
                connection.commit()
                print(f"User '{user_name}' inserted successfully.")
        except Exception as e:
            print(f"Error inserting user '{user_name}': {e}")
        finally:
            cursor.close()


# 插入歌曲数据
def insert_song(title, artist_id, album_id, genre, audio_url, language):
    with get_db_connection() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO Songs (title, artist_id, album_id, genre, audio_url, language)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (title, artist_id, album_id, genre, audio_url, language)
            )
            connection.commit()
            print(f"Song '{title}' inserted successfully.")
        except Exception as e:
            print(f"Error inserting song '{title}': {e}")
        finally:
            cursor.close()


# 插入用户收藏的歌曲
def insert_favorites(user_name, song_name, artist_name):
    with get_db_connection() as connection:
        cursor = connection.cursor()
        try:
            # 获取 user_id
            cursor.execute("SELECT user_id FROM Users WHERE user_name = %s", (user_name,))
            user = cursor.fetchone()
            if not user:
                print(f"用户 '{user_name}' 未找到。")
                return
            user_id = user[0]

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
                print(f"歌曲 '{song_name}' 由艺术家 '{artist_name}' 演唱的记录未找到。")
                return
            song_id = song[0]

            # 插入到 Favorites 表
            cursor.execute(
                """
                INSERT INTO Favorites (user_id, song_id)
                VALUES (%s, %s)
                ON CONFLICT (user_id, song_id) DO NOTHING
                """,
                (user_id, song_id)
            )
            connection.commit()
            print(f"歌曲 '{song_name}' 已添加到用户 '{user_name}' 的收藏中。")
        except Exception as e:
            print(f"将歌曲 '{song_name}' 添加到用户 '{user_name}' 的收藏时出错: {e}")
            connection.rollback()
        finally:
            cursor.close()


# 插入专辑数据
def insert_album(album_id, title, artist_id):
    with get_db_connection() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO Albums (album_id, title, artist_id)
                VALUES (%s, %s, %s)
                """,
                (album_id, title, artist_id)
            )
            connection.commit()
            print(f"Album '{title}' inserted successfully.")
        except Exception as e:
            print(f"Error inserting album '{title}': {e}")
        finally:
            cursor.close()


# 插入艺术家数据
def insert_artist(artist_id, name, bio, country, gender):
    with get_db_connection() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO Artists (artist_id, name, bio, country, gender)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (artist_id, name, bio, country, gender)
            )
            connection.commit()
            print(f"Artist '{name}' inserted successfully.")
        except Exception as e:
            print(f"Error inserting artist '{name}': {e}")
        finally:
            cursor.close()


# -----------搜索功能-----------------
def search_albums(query, connection):
    # 返回一个由字典构成的列表，每个字典表示一个专辑。
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)  # 使用字典游标
    try:
        # 执行模糊查询，查找专辑名称中包含查询关键词的专辑
        cursor.execute("SELECT * FROM Albums WHERE title ILIKE %s", ('%' + query + '%',))
        albums = cursor.fetchall()  # 获取所有匹配的专辑
        return albums  # 返回匹配的专辑列表
    except Exception as e:
        print(f"Error while searching albums: {e}")  # 打印错误信息
        return []  # 出现错误时返回空列表
    finally:
        cursor.close()  # 确保游标关闭


def search_artists(query, connection):
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)  # 使用字典游标
    try:
        # 执行模糊查询，查找艺术家名称中包含查询关键词的艺术家
        cursor.execute("SELECT * FROM Artists WHERE name ILIKE %s", ('%' + query + '%',))
        artists = cursor.fetchall()  # 获取所有匹配的艺术家
        return artists  # 返回匹配的艺术家列表
    except Exception as e:
        print(f"Error while searching artists: {e}")  # 打印错误信息
        return []  # 出现错误时返回空列表
    finally:
        cursor.close()  # 确保游标关闭


def search_songs(query, connection):
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)  # 使用字典游标
    try:
        # 联合查询：查询歌曲信息时，连接艺术家和专辑的信息
        query_string = """
            SELECT Songs.song_id, Songs.title, Songs.artist_id, Artists.name AS artist_name, 
                   Songs.album_id, Albums.title AS album_title, Songs.genre, Songs.audio_url, Songs.language
            FROM Songs
            JOIN Artists ON Songs.artist_id = Artists.artist_id
            JOIN Albums ON Songs.album_id = Albums.album_id
            WHERE Songs.title ILIKE %s
        """
        cursor.execute(query_string, ('%' + query + '%',))
        songs = cursor.fetchall()  # 获取所有匹配的歌曲
        return songs  # 返回匹配的歌曲列表
    except Exception as e:
        print(f"Error while searching songs: {e}")
        return []  # 出现错误时返回空列表
    finally:
        cursor.close()  # 确保游标关闭


# -----------新增获取筛选选项的函数-----------------
def get_unique_artist_countries(connection):
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT DISTINCT country FROM Artists WHERE country IS NOT NULL")
        countries = [row[0] for row in cursor.fetchall()]
        return countries
    except Exception as e:
        print(f"Error while getting unique artist countries: {e}")
        return []
    finally:
        cursor.close()


def get_unique_artist_genders(connection):
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT DISTINCT gender FROM Artists WHERE gender IS NOT NULL")
        genders = [row[0] for row in cursor.fetchall()]
        return genders
    except Exception as e:
        print(f"Error while getting unique artist genders: {e}")
        return []
    finally:
        cursor.close()


def get_unique_song_languages(connection):
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT DISTINCT language FROM Songs WHERE language IS NOT NULL")
        languages = [row[0] for row in cursor.fetchall()]
        return languages
    except Exception as e:
        print(f"Error while getting unique song languages: {e}")
        return []
    finally:
        cursor.close()


def get_unique_song_genres(connection):
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT DISTINCT genre FROM Songs WHERE genre IS NOT NULL")
        genres = [row[0] for row in cursor.fetchall()]
        return genres
    except Exception as e:
        print(f"Error while getting unique song genres: {e}")
        return []
    finally:
        cursor.close()


# -----------新增综合搜索和筛选的函数-----------------
# 搜索艺术家，根据查询关键词和筛选条件
def search_artists_with_filters(query=None, country=None, gender=None, connection=None):
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        base_query = "SELECT * FROM Artists WHERE TRUE"
        params = []
        if query:
            base_query += " AND name ILIKE %s"
            params.append(f"%{query}%")
        if country:
            base_query += " AND country = %s"
            params.append(country)
        if gender:
            base_query += " AND gender = %s"
            params.append(gender)

        cursor.execute(base_query, tuple(params))
        artists = cursor.fetchall()
        return artists
    except Exception as e:
        print(f"Error while searching artists with filters: {e}")
        return []
    finally:
        cursor.close()


# 搜索歌曲，根据查询关键词和筛选条件
def search_songs_with_filters(query=None, language=None, genre=None, connection=None):
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        base_query = """
            SELECT Songs.song_id, Songs.title, Songs.artist_id, Artists.name AS artist_name, 
                   Songs.album_id, Albums.title AS album_title, Songs.genre, Songs.audio_url, Songs.language
            FROM Songs
            JOIN Artists ON Songs.artist_id = Artists.artist_id
            JOIN Albums ON Songs.album_id = Albums.album_id
            WHERE TRUE
        """
        params = []
        if query:
            base_query += " AND Songs.title ILIKE %s"
            params.append(f"%{query}%")
        if language:
            base_query += " AND Songs.language = %s"
            params.append(language)
        if genre:
            base_query += " AND Songs.genre = %s"
            params.append(genre)

        cursor.execute(base_query, tuple(params))
        songs = cursor.fetchall()
        return songs
    except Exception as e:
        print(f"Error while searching songs with filters: {e}")
        return []
    finally:
        cursor.close()




# -----------初始化-----------------
if __name__ == "__main__":
    drop_all_tables()
    create_tables()

    # 插入一些示例数据
    insert_artist(1, '林俊杰', '著名歌手', '新加坡', '男')
    insert_artist(2, 'The Weeknd', '加拿大歌手和音乐制作人', '加拿大', '男')
    insert_artist(3, 'Kanye West', '美国著名说唱歌手和音乐制作人', '美国', '男')
    insert_artist(4, 'Gareth.T', '香港R&B音乐人', '中国香港', '男')
    insert_artist(5, '卫兰', '卫兰(Janice M.Vidal), 1982年4月13日出生于中国香港, 英国籍华裔女歌手', '中国香港', '女')
    insert_artist(6, '陈奕迅', '陈奕迅(Eason Chan), 1974年7月27日出生于中国香港, 话语流行乐男歌手, 演员, 作曲人',
                  '中国香港', '男')
    insert_artist(7, '陶喆', '音乐创作人, 制作人, 歌手', '中国台北', '男')
    insert_artist(8, '法老', '1992年10月11日出生于浙江省海宁市, 中国内地说唱男歌手, 词曲作者', '中国大陆', '男')

    insert_album(1, '第二天堂', 1)
    insert_album(2, 'After Hours', 2)
    insert_album(3, 'Donda', 3)
    insert_album(4, '紧急联络人', 4)
    insert_album(5, '国际孤独等级', 4)
    insert_album(6, 'Imagine', 5)
    insert_album(7, 'L.O.V.E.', 6)
    insert_album(8, 'U 87', 6)
    insert_album(9, 'Im OK', 7)
    insert_album(10, 'Lift Continues', 6)
    insert_album(11, '星空叙爱曲', 8)
    insert_album(12, '健将mixtape(Explicit)', 8)

    insert_song('After Hours', 2, 2, 'R&B', 'After_Hours.mp3', 'English')
    insert_song('Save Your Tears', 2, 2, 'R&B', 'Save_Your_Tears.mp3', 'English')
    insert_song('江南', 1, 1, 'Pop', '江南.mp3', '国语')
    insert_song('美人鱼', 1, 1, 'Pop', '美人鱼.mp3', '国语')
    insert_song('24', 3, 3, 'Hip-Hop', '24.mp3', 'English')
    insert_song('紧急联络人', 4, 4, 'R&B', '紧急联络人.mp3', '粤语')
    insert_song('国际孤独等级', 4, 5, 'R&B', '国际孤独等级.mp3', '粤语')
    insert_song('街灯晚餐', 5, 6, 'R&B', '街灯晚餐.mp3', '粤语')
    insert_song('我们万岁', 6, 7, 'R&B', '我们万岁.mp3', '粤语')
    insert_song('葡萄成熟时', 6, 8, 'R&B', '葡萄成熟时.mp3', '粤语')
    insert_song('普通朋友', 7, 9, 'R&B', '普通朋友.mp3', '国语')
    insert_song('天天', 7, 9, 'R&B', '天天.mp3', '国语')
    insert_song('找自己', 7, 9, 'R&B', '找自己.mp3', '国语')
    insert_song('最佳损友', 6, 10, 'R&B', '最佳损友.mp3', '粤语')
    insert_song('星空叙爱曲', 8, 11, 'Rap', '星空叙爱曲.mp3', '国语')
    insert_song('会魔法的老人', 8, 12, 'Rap', '会魔法的老人.mp3', '国语')

    insert_user('Tank', 'Tank2028085771', 'jzl@250.com', '1008611', '2003', '2', '30')
    insert_user('x+x', 'x+x', 'x+x@163.com', '1008611', '2003', '2', '30')
    insert_user('Bean_cock', 'Gong', 'Roman@163.com', '1008611', '2005', '2', '30')
    insert_user('Bonjour', 'Bonjour', 'Bonjour@163.com', '1008611', '2003', '2', '30')
