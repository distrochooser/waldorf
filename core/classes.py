class Visitor():
  """
  Client related data
  """
  useragent: str = ""
  referrer: str = ""
  prerender: bool = False

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

class Distro():
  id: int = 0
  name: str = ""
  website: str = ""
  textSource: str = ""
  imageSource: str = ""
  image: str = ""
  tags: list() = list() # of string
  description: str = ""

class Question():
  id: int = 0
  orderIndex: int = 0
  text: str = ""
  title: str = ""
  isText: bool = False
  isSingle: bool = False
  excludedBy: list() # of string
  answers: list() # of Answer
  answered: bool = False

class Answer():
  id: int = 0
  text: str = ""
  tags: list = list() # of string
  excludeTags: list = list() # of string
  selected: bool = False
