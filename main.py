from flask import Flask, Response, request, abort
from functools import wraps
from core.classes import Visitor, Tag, Result, Distro, Question, Answer, Statistics
import argparse
import pymysql.cursors
from datetime import datetime
from jsonpickle import loads, dumps
from flask_cors import CORS
from flask_compress import Compress
from os import environ

parser = argparse.ArgumentParser()
parser.add_argument('--langs', help='Comma separated list of lang codes')
args = parser.parse_args()

app = Flask(__name__)
CORS(app)
Compress(app)
allowLanguages = args.langs.split(",")

database = pymysql.connect(
  host="localhost",
  user="user",
  password=environ["PASS"],
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


def queryDistributions(lang: str):
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
  return result

@app.route("/stats/")
def getStats():
  with database.cursor() as cursor:
    query = "Select count(id) as visitors, ( Select count(id) from Result) as tests from Visitor"
    cursor.execute(query)
    tuples = cursor.fetchone()
    v = Statistics()
    v.visitor = tuples["visitors"]
    v.test = tuples["tests"]
    return dumps(v, unpicklable=False)

@app.route("/distributions/<lang>/")
@checkLanguage
def getDistributions(lang: str):
  return dumps(queryDistributions(lang), unpicklable=False)

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

def queryQuestions(lang: str):
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
  return result

@app.route("/questions/<lang>/")
@checkLanguage
def getQuestions(lang: str):
  return dumps(queryQuestions(lang), unpicklable=False)

@app.route("/addresult/<lang>/<rating>/<visitor>/", methods=["POST"])
def addResult(lang: str, rating: int, visitor: int):
  body = request.get_json(silent=True)
  with database.cursor() as cursor:
    query = "Insert into Result (rating, visitorId, lang) values (%s, %s, %s)"
    cursor.execute(query, (
      rating,
      visitor,
      lang
    ))
    resultId = cursor.lastrowid
    #insert answers
    for answer in body["answers"]:
      query = "Insert into ResultAnswers (resultId, answer) VALUES (%s,%s)"
      cursor.execute(query, (
        resultId,
        answer
      ))
    for tag in body["tags"]:
      query = "Insert into ResultTags (resultId, tag,weight,isNegative,amount) VALUES (%s,%s, %s, %s, %s)"
      cursor.execute(query, (
        resultId,
        tag["name"],
        tag["weight"],
        tag["negative"],
        tag["amount"]
      ))
    database.commit() 
  return str(resultId)

@app.route("/addrating/<test>/<rating>")
def addRating(test: int, rating: int):
  with database.cursor() as cursor:
    query = "Update Result set rating=%s, updated=1 where id=%s and updated =0"
    got = cursor.execute(query, (
      rating,
      test
    ))
    database.commit()
    return dumps(got)

@app.route("/getresult/<id>/")
def getResult(id: int):
  with database.cursor() as cursor:
    query = "Select * from ResultAnswers  where resultId = %s"
    cursor.execute(query, (
      id
    ))
    results = cursor.fetchall()
    r = Result()
    r.answers = []
    for tuple in results:
      r.answers.append(tuple["answer"])

    query = "Select * from ResultTags  where resultId = %s"
    cursor.execute(query, (
      id
    ))
    results = cursor.fetchall()
    r.tags = []
    for tuple in results:
      t = Tag()
      t.name = tuple["tag"]
      t.amount = tuple["amount"]
      t.negative = (False, True)[tuple["isNegative"] == 1]
      t.weight = tuple["weight"]
      r.tags.append(t)

  return dumps(r, unpicklable=False)

@app.route("/get/<lang>/", methods=["POST"])
@checkLanguage
def newVisitor(lang: str):
  with database.cursor() as cursor:
    visitorData = request.get_json(silent=True)
    query = "Insert into Visitor (visitDate, userAgent, referrer, lang, prerender) VALUES (%s, %s, %s, %s, %s)"
    visitDate = datetime.now()
    userAgent = request.headers.get("user-agent")
    referrer = request.headers.get("referrer")
    prerender = visitorData["prerender"]
    got = cursor.execute(query, (
      visitDate,
      userAgent,
      referrer,
      lang,
      prerender
    ))

    v = Visitor()
    v.id = cursor.lastrowid
    v.useragent = userAgent
    v.visitDate = visitDate
    v.referrer = referrer
    v.questions = queryQuestions(lang)
    v.distros = queryDistributions(lang)
    query = "Select val, translation from i18n where langCode = %s and val not like 'd.%%' and val not like 'a.%%' and val not like 'q.%%'"
    cursor.execute(query, (
      lang
    ))
    v.i18n = {}
    results = cursor.fetchall()
    for tuple in results:
      v.i18n[tuple["val"]] = tuple

    database.commit()
  return dumps(v, unpicklable=False)


@app.after_request
def addCors(response: Response):
  """
  Add needed CORS headers
  """
  headers = {
    "Content-Type": "application/json",
    "Server": "waldorf",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Method": "GET,OPTIONS,POST",
    "Access-Control-Allow-Headers": "content-type",
    "Cache-Contol": "must-revalidate, max-age=259200",
    "Pragma": "no-cache",
    "Expires": "Sat, 26. Jul 1997 06:00:00 GMT",
  }
  for key, value in headers.items():
    if response.headers.get(key) != None:
      response.headers[key] = value
    else:
      response.headers.add(key, value)
  return response

try:
  app.run(
    host="0.0.0.0",
    port=8181,
    debug=False
  )
finally:
  database.close()