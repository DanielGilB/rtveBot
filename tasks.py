from celery import Celery
import tweepy
import json
import urllib.request
import random
#from celery.task.schedules import crontab
from celery.decorators import periodic_task
import dropbox
import tempfile

#dropbox access data
token = "..."
dbx = dropbox.Dropbox(token)


# Twitter access data
consumer_key = '...'
consumer_secret = '...'
access_token = '...'
access_token_secret = '...'

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

api = tweepy.API(auth)
# account name
botName = api.me().name

print ("----------------------------------------------------")
print ("|| Bot lanzado en la cuenta de twitter: %s ||" % botName) 
print ("----------------------------------------------------")

#using Celery with RabbitMQ
app = Celery('tasks',backend='rpc://', broker='pyamqp://guest@localhost//')

#@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Calls UpdateNews() every 30 seconds.
    sender.add_periodic_task(30.0, UpdateNews())

    # Calls Response() every 10 seconds
    sender.add_periodic_task(10.0, Response(), name)

    # Calls Followers() every 30 seconds
    sender.add_periodic_task(30.0, Followers())

  
#@periodic_task(run_every=crontab(hour="1"))
@app.task
def UpdateNews():
    print ("------------------------------------------------------------------")
    print ("|| Procediendo a publicar las ultimas 20 noticias mas populares ||")
    print ("------------------------------------------------------------------")

    programas = json.load(urllib.request.urlopen('http://api.rtve.es/api/noticias/mas-populares.json'))
    for programa in programas['page']['items']:
        try:
            if api.update_status(status=programa['longTitle'] + "\n" + programa['htmlShortUrl']):
                print(programa['longTitle'])
        except tweepy.error.TweepError as e:
            print("noticia ya publicada")


def Recomendation():
    print ("-----------------------------")
    print ("|| Realizando recomendacion ||")
    print ("-----------------------------")
    
    r = random.randrange(0, 19)
    programas = json.load(urllib.request.urlopen('http://api.rtve.es/api/multimedias/mas-populares.json'))
    
    return (programas['page']['items'][r]['longTitle'] + "\n" + programas['page']['items'][r]['htmlShortUrl'])
    
@app.task
def Response():

    tweets = api.search(q="@%s" % botName)     
     
    for tw in tweets:
        user = tw.user.screen_name

        message = "Hola, @%s has visto....\n" % user + Recomendation()
        try:
            if api.create_favorite(tw.id):
                if api.update_status(message, tw.id):
                    print(message)
        except tweepy.error.TweepError as e:
            print("Rescomendacion ya realizada")

#@periodic_task(run_every=crontab(hour="1"))
@app.task
def Followers():
    print ("-------------------------")
    print ("|| Lista de seguidores ||")
    print ("-------------------------")
    print ("Tienes %s seguidores" % api.me().followers_count)

    LocalFile = "followers.txt"
    
    try:
        file = open(LocalFile, 'rb')
    except IOError:
        print ("Generando %s" % LocalFile)
        file = open(LocalFile, 'w')
        file = open(LocalFile, 'rb')
    

    with open(LocalFile, 'w') as f:
        for follower in tweepy.Cursor(api.followers).items():
            f.write(follower.screen_name + '\n')
    
    data = file.read()

    RemoteFile = "/" + LocalFile
    response = dbx.files_upload(data, RemoteFile, mode=dropbox.files.WriteMode.overwrite)
    print("Archivo Dropbox actualizado")
