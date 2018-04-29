from jsonpickle import loads


class Base():
  def fromTuple(self, tuple: dict):
    for key, value in tuple.items():
      if key in ["tags", "excludedBy", "excludeTags"]:
        setattr(self, key, loads(value))     
      elif hasattr(self, key) and key != "tags":
        if isinstance(getattr(self, key), bool):
          setattr(self, key, (False, True)[value == 1])
        else:
          setattr(self, key, value)
     

class Visitor():
  """
  Client related data
  """
  useragent: str = ""
  referrer: str = ""
  prerender: bool = False
  id: int = 0
  i18n: dict = dict()
  distros: list() = None

class Result():
  """
  User answer data
  """
  answers: list = list() # of int
  tags: list = list() # of Tag

class Tag():
  name: str = ""
  weight: int = 0
  amount: int = 0
  negative: bool = False

class Distro(Base):
  id: int = 0
  name: str = ""
  website: str = ""
  textSource: str = ""
  imageSource: str = ""
  image: str = ""
  tags: list() = list() # of string
  description: str = ""
  

class Question(Base):
  id: int = 0
  orderIndex: int = 0
  text: str = ""
  title: str = ""
  isText: bool = False
  isSingle: bool = False
  excludedBy: list() # of string
  answers: list() # of Answer
  answered: bool = False

class Answer(Base):
  id: int = 0
  text: str = ""
  tags: list = list() # of string
  excludeTags: list = list() # of string
  selected: bool = False
