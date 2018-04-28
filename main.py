from flask import Flask, Response, request, abort
from functools import wraps
from core.classes import Visitor, Tag, Result, Distro, Question, Answer
import argparse
import pymysql.cursors
from jsonpickle import loads, dumps


parser = argparse.ArgumentParser()
parser.add_argument('--langs', help='Comma separated list of lang codes')
args = parser.parse_args()

app = Flask(__name__)
allowLanguages = args.langs.split(",")

database = pymysql.connect(
  host="localhost",
  user="user",
  password="test",
  db="ldc4",
  charset="utf8",
  cursorclass=pymysql.cursors.DictCursor
)

def checkLanguage(f):
  @wraps(f)
  def decorated_function(*args, **kwargs):
      if 'lang' in kwargs and kwargs['lang'] in allowLanguages:
        return f(*args, **kwargs)
      else:
        abort(404)
  return decorated_function

@app.route("/")
def hello():
  return "Hello, I'm not that rusty"

@app.route("/<path:path>", methods=['OPTIONS'])
def handleOptions():
  return "ok"


@app.route("/distributions/<lang>/<id>/")
@checkLanguage
def getDistribution(lang: str, id: int):
  with database.cursor() as cursor:
    query = "Select *, (Select translation from i18n where langCode = %s and val = concat('d.', Distro.id, '.description')) as description from Distro where id = %s"
    cursor.execute(query, (
      lang,
      id
    ))
    tuple = cursor.fetchone()
    d = Distro()
    d.fromTuple(tuple)    
  return dumps(d, unpicklable=False)

@app.route("/distributions/<lang>/")
@checkLanguage
def getDistributions(lang: str):
  result = []
  with database.cursor() as cursor:
    query = "Select *, (Select translation from i18n where langCode = %s and val = concat('d.', Distro.id, '.description')) as description from Distro"
    cursor.execute(query, (
      lang
    ))
    tuples = cursor.fetchall()
    for tuple in tuples:
      d = Distro()
      d.fromTuple(tuple)   
      result.append(d)        
  return dumps(result, unpicklable=False)

def getAnswersForQuestion(lang: str, question:id ) -> list():
  result = []
  with database.cursor() as cursor:
    query = "Select * from Answer where questionID = %s"
    cursor.execute(query,  (
      question
    ))
    tuples = cursor.fetchall()
   
    for tuple in tuples:
      a = Answer()
      a.fromTuple(tuple)
      i18nQuery = "Select * from i18n where val like 'a.%s.%%' and langCode = %s"
      cursor.execute(i18nQuery, (
        tuple["id"],
        lang,
      ))
      translations = cursor.fetchall()
      for translation in translations:
        for needle in ["title", "text"]:
          if "." + needle in translation["val"]:
            setattr(a, needle,translation["translation"])
      result.append(a)        
  return result

@app.route("/questions/<lang>/")
@checkLanguage
def getQuestions(lang: str):
  result = []
  with database.cursor() as cursor:
    query = "Select * from Question order by orderIndex"
    cursor.execute(query)
    tuples = cursor.fetchall()

    
    for tuple in tuples:
      q = Question()
      q.fromTuple(tuple)
      q.answered = False
      q.answers = getAnswersForQuestion(lang, q.id)
      
      i18nQuery = "Select * from i18n where val like 'q.%s.%%' and langCode = %s"
      cursor.execute(i18nQuery, (
        tuple["id"],
        lang,
      ))
      translations = cursor.fetchall()
      for translation in translations:
        for needle in ["title", "text"]:
          if "." + needle in translation["val"]:
            setattr(q, needle,translation["translation"])
      result.append(q)        
  return dumps(result, unpicklable=False)

@app.after_request
def addCors(response: Response):
  """
  Add needed CORS headers
  """
  headers = {
    "content-type": "application/json",
    "server": "foo",
    "Access-Control-Allow": "*",
    "Access-Control-Allow-Method": "GET,OPTIONS,POST",
    "Access-Control-Allow-Headers": "content-type",
    "Cache-Contol": "must-revalidate, max-age=259200",
    "Pragma": "no-cache",
    "Expires": "Sat, 26. Jul 1997 06:00:00 GMT",
  }
  for key, value in headers.items():
    response.headers.add(key, value)
  return response

try:
  app.run(
    host="0.0.0.0",
    port=8181,
    debug=True
  )
finally:
  database.close()