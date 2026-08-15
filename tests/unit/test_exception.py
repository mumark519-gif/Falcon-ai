from app.core.exceptions import FalconException

try:
    raise FalconException("This is a Falcon AI test error.")
except FalconException as e:
    print(e.message)