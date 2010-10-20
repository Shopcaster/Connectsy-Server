
from db.models import Model
from utils import timestamp
import uuid

class Event(Model):
    __collection__ = 'event'
    __fields__ = {
        u'where': None,
        u'when': None,
        u'what': None,
        u'broadcast': None,
        u'posted_from': None,
        u'location': None,
        u'category': None,
        u'creator': None,
        u'created': timestamp(),
        u'revision': uuid.uuid1().hex,
    }