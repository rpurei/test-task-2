import urllib.request
import requests
import json
import os
import pymysql
import math
from config import *
ARTIST_ID = 479

#response = requests.get(URL_ARTIST+str(ARTIST_ID))
#data = json.loads(response.content)
#print(os.path.normpath(os.path.realpath('.') + IMAGE_ARTISTS_DIR + str(data['id']) + '-' + data['picture_medium'].split('/')[-1]))
#print(data)

response = requests.get(URL_ARTIST+str(ARTIST_ID)+'/albums')
#data = json.loads(response.content)
print(json.loads(response.content))
print(json.loads(response.content)['data'][0]['genre_id'])
#for index in range(0, math.ceil(int(data['total'])/25.0)):
#    response = requests.get(URL_ARTIST + str(ARTIST_ID) + '/albums/?index=' + str(index*25))
#    data = json.loads(response.content)
#    print(f'Step: {index}')
#    print('Count: ' + str(len(data['data'])))
#    print(data['data'][0]['id'])
