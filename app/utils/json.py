import json
def dumps(data):return json.dumps(data,ensure_ascii=False,default=str)
