from celery import Celery
import redis
import pymysql
import requests
import json
from config import *
import urllib.request
import os
import time
import math

celery = Celery('worker', broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)


@celery.task(bind=True)
def deezer_query_artists(self, start, end):
    connection = None
    try:
        connection = pymysql.connect(host=MYSQL_DATABASE_HOST, user=MYSQL_DATABASE_USER,
                                     passwd=MYSQL_DATABASE_PASSWORD, db=MYSQL_DATABASE_DB)
        with connection:
            cursor = connection.cursor()
            for iter in range(start, end):
                response_art = requests.get(URL_ARTIST+str(iter))
                try:
                    data_art = json.loads(response_art.content)
                    try:
                        file_name = os.path.normpath(IMAGE_ARTISTS_DIR + str(data_art['id']) + '-' +
                                                     data_art['picture_medium'].split('/')[-1])
                        cursor.callproc('insert_artist', (data_art['id'], data_art['name'], file_name,))
                        connection.commit()
                        urllib.request.urlretrieve(data_art['picture_medium'], '/app' + file_name)
                        response_temp = requests.get(URL_ARTIST + str(iter) + '/albums')
                        data_temp = json.loads(response_temp.content)
                        for index in range(0, math.ceil(int(data_temp['total']) / 25.0)):
                            response_alb = requests.get(URL_ARTIST + str(iter) + '/albums/?index=' + str(index * 25))
                            try:
                                data_alb = json.loads(response_alb.content)
                                for step in range(0, len(data_alb['data'])):
                                    genre_id = data_alb['data'][step]['genre_id']
                                    response_genre = requests.get(URL_GENRE+str(genre_id))
                                    file_album_name = os.path.normpath(IMAGE_ALBUMS_DIR + str(data_alb['data'][step]['id']) + '-' +
                                                     data_alb['data'][step]['cover_small'].split('/')[-1])
                                    urllib.request.urlretrieve(data_alb['data'][step]['cover_small'], '/app' + file_album_name)
                                    try:
                                        cursor.callproc('insert_album', (data_alb['data'][step]['id'], data_art['id'],
                                                                 data_alb['data'][step]['title'], file_album_name,
                                                                 json.loads(response_genre.content)['name'], data_alb['data'][step]['fans'],
                                                                 data_alb['data'][step]['release_date'],))
                                        connection.commit()
                                    except pymysql.Error as e:
                                        print(f'Ошибка работы с БД (таблица Albums): {e.args[0]}, {e.args[1]}')
                            except:
                                print('JSON ошибка обработки Альбома')
                    except pymysql.Error as e:
                        print(f'Ошибка работы с БД (таблица Artists): {e.args[0]}, {e.args[1]}')
                except:
                    print('JSON ошибка обработки Исполнителя')
                time.sleep(0.5)
    except pymysql.Error as e:
        print(f'Ошибка с оединения с БД: {e.args[0]}, {e.args[1]}')
    finally:
        print('Задание завершено')
        #connection.close() -  хз почему, но в этом месте соединение с БД уже закрыто