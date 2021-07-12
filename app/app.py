import celery
import redis
from flask import Flask, render_template, url_for, flash
from flask_bootstrap import Bootstrap
from flask_nav import Nav
from flask_nav.elements import *
from flask_paginate import Pagination, get_page_parameter
from flask import jsonify
import json
import pymysql

from config import *
from celery_tasks import deezer_query_artists
from forms import *

app = Flask('__name__')
app.config.from_pyfile('config.py')
Bootstrap(app)
nav = Nav()
topbar = Navbar(View('Главная', 'index_view'),
                View('Исполнители', 'artists_view'),
                View('Альбомы', 'albums_view')
                )
nav.register_element('top', topbar)
nav.init_app(app)
cache = redis.Redis(host='redis', port=6379)


@app.route('/', methods = ['GET', 'POST'])
def index_view():
    task = None
    start_id = None
    try:
        connection = pymysql.connect(host=MYSQL_DATABASE_HOST, user=MYSQL_DATABASE_USER, passwd=MYSQL_DATABASE_PASSWORD,
                                 db=MYSQL_DATABASE_DB)
        flash("Соединение с БД установлено", 'success')
        with connection:
            cursor = connection.cursor()
            cursor.execute('SELECT MAX(Id) FROM Artists;')
            count = cursor.fetchone()
            start_id = count[0]
            flash(f"Последний ИД в БД: {start_id}", 'info')

    except pymysql.Error as e:
        flash(f'Ошибка соединения с БД: {e.args[0]}, {e.args[1]}', 'danger')
    form_task = TaskForm()
    if form_task.validate_on_submit():
        task = deezer_query_artists.delay(start_id, 100)
        return render_template('index.html', form_task=form_task, task_id=task.id)
    return render_template('index.html', form_task=form_task)


@app.route('/status/<task_id>')
def status_view(task_id):
    task = deezer_query_artists.AsyncResult(task_id)
    status = ''
    if task.state == 'PENDING':
        status = 'Задание ожидает запуск'
        flash(status, 'info')
    elif task.state != 'FAILURE':
        status = f'Задание выполняется, статус: {task.info.get("status", "")}, текущее: {task.info.get("current", 0)}'
        flash(status, 'success')
    else:
        status = f'Задание не выполняется, статус: {task.info}'
        flash(status, 'danger')
    return render_template('status.html', task_status=status)


@app.route('/artist/<int:artist_id>')
def artist_view(artist_id):
    error_message = ''
    result = None
    try:
        connection = pymysql.connect(host=MYSQL_DATABASE_HOST, user=MYSQL_DATABASE_USER, passwd=MYSQL_DATABASE_PASSWORD,
                                 db=MYSQL_DATABASE_DB)
        with connection:
            cursor = connection.cursor()
            try:
                cursor.callproc('get_artist_by_id', (artist_id,))
                result = cursor.fetchall()
            except pymysql.Error as e:
                error_message = f'Ошибка работы с БД: {e.args[0]}, {e.args[1]}'
    except pymysql.Error as e:
        error_message = f'Ошибка соединения с БД: {e.args[0]}, {e.args[1]}'
    flash(error_message, 'danger')
    return render_template('artists.html', artists_data=result)


@app.route('/artists', methods=['GET', 'POST'])
def artists_view():
    error_message = ''
    page = request.args.get(get_page_parameter(), type=int, default=1)
    start_at = (page-1) * ROWS_PER_PAGE
    result = None
    pagination = None
    search_form = SearchForm()
    if search_form.validate_on_submit():
        search_word = search_form.title.data
        try:
            connection = pymysql.connect(host=MYSQL_DATABASE_HOST, user=MYSQL_DATABASE_USER,
                                         passwd=MYSQL_DATABASE_PASSWORD,
                                         db=MYSQL_DATABASE_DB)
            with connection:
                cursor = connection.cursor()
                try:
                    cursor.callproc('get_artist_by_name', (search_word,))
                    result = cursor.fetchall()
                except pymysql.Error as e:
                    error_message = f'Ошибка работы с БД: {e.args[0]}, {e.args[1]}'
                return render_template('artists.html', artists_data=result, search_form = search_form)
        except pymysql.Error as e:
            error_message = f'Ошибка соединения с БД: {e.args[0]}, {e.args[1]}'
    try:
        connection = pymysql.connect(host=MYSQL_DATABASE_HOST, user=MYSQL_DATABASE_USER, passwd=MYSQL_DATABASE_PASSWORD,
                                 db=MYSQL_DATABASE_DB)
        with connection:
            cursor = connection.cursor()
            try:
                cursor.execute('SELECT COUNT(*) FROM Artists;')
                count = cursor.fetchone()
                cursor.callproc('get_artists', (' ', start_at, ROWS_PER_PAGE,))
                result = cursor.fetchall()
                pagination = Pagination(page=page, total=int(count[0]), search=False, record_name='Исполнители', per_page=ROWS_PER_PAGE, css_framework='bootstrap3')
            except pymysql.Error as e:
                error_message = f'Ошибка работы с БД: {e.args[0]}, {e.args[1]}'
    except pymysql.Error as e:
        error_message = f'Ошибка соединения с БД: {e.args[0]}, {e.args[1]}'
    flash(error_message, 'danger')
    return render_template('artists.html', pagination=pagination, artists_data=result, search_form = search_form)


@app.route('/albums')
def albums_view():
    error_message = ''
    page = request.args.get(get_page_parameter(), type=int, default=1)
    start_at = (page-1) * ROWS_PER_PAGE
    result = None
    pagination = None
    try:
        connection = pymysql.connect(host=MYSQL_DATABASE_HOST, user=MYSQL_DATABASE_USER, passwd=MYSQL_DATABASE_PASSWORD,
                                    db=MYSQL_DATABASE_DB)
        with connection:
            cursor = connection.cursor()
            try:
                cursor.execute('SELECT COUNT(*) FROM Albums;')
                count = cursor.fetchone()
                cursor.callproc('get_albums', (start_at, ROWS_PER_PAGE,))
                result = cursor.fetchall()
                pagination = Pagination(page=page, total=int(count[0]), search=False, record_name='Альбомы', per_page=ROWS_PER_PAGE, css_framework='bootstrap3')
            except pymysql.Error as e:
                error_message = f'Ошибка работы с БД: {e.args[0]}, {e.args[1]}'
    except pymysql.Error as e:
        error_message = f'Ошибка соединения с БД: {e.args[0]}, {e.args[1]}'
    flash(error_message, 'danger')
    return render_template('albums.html', pagination=pagination, albums_data=result)


@app.route('/album/<int:album_id>')
def album_view(album_id):
    error_message = ''
    result = None
    try:
        connection = pymysql.connect(host=MYSQL_DATABASE_HOST, user=MYSQL_DATABASE_USER, passwd=MYSQL_DATABASE_PASSWORD,
                                     db=MYSQL_DATABASE_DB)
        with connection:
            cursor = connection.cursor()
            try:
                cursor.callproc('get_album_by_id', (album_id,))
                result = cursor.fetchall()
            except pymysql.Error as e:
                error_message = f'Ошибка работы с БД: {e.args[0]}, {e.args[1]}'
    except pymysql.Error as e:
        error_message = f'Ошибка соединения с БД: {e.args[0]}, {e.args[1]}'
    flash(error_message, 'danger')
    return render_template('albums.html', albums_data=result)

##REST


@app.route('/api/v1/artist/<int:artist_id>')
def api_artist_get(artist_id):
    error_message = ''
    result = None
    try:
        connection = pymysql.connect(host=MYSQL_DATABASE_HOST, user=MYSQL_DATABASE_USER, passwd=MYSQL_DATABASE_PASSWORD,
                                     db=MYSQL_DATABASE_DB)
        with connection:
            cursor = connection.cursor()
            try:
                cursor.callproc('get_artist_by_id', (artist_id,))
                row_headers = [x[0] for x in cursor.description]
                result = cursor.fetchall()
                json_data = []
                for res in result:
                    json_data.append(dict(zip(row_headers, res)))
                return jsonify(json.dumps(json_data))
            except pymysql.Error as e:
                error_message = f'Ошибка работы с БД: {e.args[0]}, {e.args[1]}'
    except pymysql.Error as e:
        error_message = f'Ошибка соединения с БД: {e.args[0]}, {e.args[1]}'
    return jsonify(json.dumps(error_message))


@app.route('/api/v1/artists')
def api_artists_get():
    error_message = ''
    result = None
    try:
        connection = pymysql.connect(host=MYSQL_DATABASE_HOST, user=MYSQL_DATABASE_USER, passwd=MYSQL_DATABASE_PASSWORD,
                                     db=MYSQL_DATABASE_DB)
        with connection:
            cursor = connection.cursor()
            try:
                cursor.callproc('get_artists', (' ', 0, 500,))
                row_headers = [x[0] for x in cursor.description]
                result = cursor.fetchall()
                json_data = []
                for res in result:
                    json_data.append(dict(zip(row_headers, res)))
                return jsonify(json.dumps(json_data))
            except pymysql.Error as e:
                error_message = f'Ошибка работы с БД: {e.args[0]}, {e.args[1]}'
    except pymysql.Error as e:
        error_message = f'Ошибка соединения с БД: {e.args[0]}, {e.args[1]}'
    return jsonify(json.dumps(error_message))


@app.route('/api/v1/album/<int:album_id>')
def api_album_get(album_id):
    error_message = ''
    result = None
    try:
        connection = pymysql.connect(host=MYSQL_DATABASE_HOST, user=MYSQL_DATABASE_USER, passwd=MYSQL_DATABASE_PASSWORD,
                                     db=MYSQL_DATABASE_DB)
        with connection:
            cursor = connection.cursor()
            try:
                cursor.callproc('get_album_by_id', (album_id,))
                row_headers = [x[0] for x in cursor.description]
                result = cursor.fetchall()
                json_data = []
                for res in result:
                    json_data.append(dict(zip(row_headers, res)))
                return jsonify(json.dumps(json_data))
            except pymysql.Error as e:
                error_message = f'Ошибка работы с БД: {e.args[0]}, {e.args[1]}'
    except pymysql.Error as e:
        error_message = f'Ошибка соединения с БД: {e.args[0]}, {e.args[1]}'
    return jsonify(json.dumps(error_message))


@app.route('/api/v1/albums')
def api_albums_get():
    error_message = ''
    result = None
    try:
        connection = pymysql.connect(host=MYSQL_DATABASE_HOST, user=MYSQL_DATABASE_USER, passwd=MYSQL_DATABASE_PASSWORD,
                                     db=MYSQL_DATABASE_DB)
        with connection:
            cursor = connection.cursor()
            try:
                cursor.callproc('get_albums', (0, 500,))
                row_headers = [x[0] for x in cursor.description]
                result = cursor.fetchall()
                json_data = []
                for res in result:
                    json_data.append(dict(zip(row_headers, res)))
                return jsonify(json.dumps(json_data))
            except pymysql.Error as e:
                error_message = f'Ошибка работы с БД: {e.args[0]}, {e.args[1]}'
    except pymysql.Error as e:
        error_message = f'Ошибка соединения с БД: {e.args[0]}, {e.args[1]}'
    return jsonify(json.dumps(error_message))


if __name__ == '__main__':
    app.run(host=APP_ADDRESS, port=APP_PORT)
