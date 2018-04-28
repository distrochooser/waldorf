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

@app.route("/distributions/<lang>/")
@checkLanguage
def getDistribution(lang: str):
  result = []
  with database.cursor() as cursor:
    query = "Select *, (Select translation from i18n where langCode = %s and val = concat('d.', Distro.id, '.description')) as description from Distro"
    cursor.execute(query, (
      lang
    ))
    tuples = cursor.fetchall()
    for tuple in tuples:
      d = Distro()
      for key, value in tuple.items():
        if hasattr(d, key) and key != "tags":
          setattr(d, key, value)
        elif key == "tags":
          setattr(d, key, loads(value))
      result.append(d)        
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