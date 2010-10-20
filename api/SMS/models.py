from db.models import Model
from utils import timestamp
import db

class SMSRegister(Model):
    __collection__ = 'sms_reg'
    __fields__ = {
        u'contact_number': None,
        u'twilio_number': None,
        u'expires': timestamp(),
        u'event': None,
        u'user': None,
    }
    
    def save(self):
        find = {
            u'contact_number': self[u'contact_number'],
            u'twilio_number': self[u'twilio_number'],
        }
        db.objects.sms_reg.update(find, self.__data__, upsert=True)

    

