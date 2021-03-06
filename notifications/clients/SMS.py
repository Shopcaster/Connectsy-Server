from api.SMS.models import SMSRegister
from api.SMS.sms_utils import format_date
from notifications import notifier
from settings import SMS_OUTPUT_URL
from urllib2 import HTTPError
import settings
import twilio

class Notifier(notifier.Notifier):
    
    def send(self, user, client_id, message):
        from api.events.models import Event
        
        if message[u'type'] not in (u'invite', u'comment'):
            return False
        
        smsee = SMSRegister.get({u'event': message[u'event_id'],
                                 u'contact_number': client_id})
        if smsee is None: return False
        
        event = Event.get(message[u'event_id'])
        if event is None: return False
        
        account = twilio.Account(settings.TWILIO_ACCOUNT_SID,
                                 settings.TWILIO_AUTH_TOKEN)
        
        texts = list()
        
        if message[u'type'] == u'invite':
            tz = smsee[u'tz'] or 'America/Toronto'
            
            t2 = ('%s shared a plan with you on '
                  'Connectsy. ' % event[u'creator'])
            if event[u'where'] is not None:
                t2 += 'Where: %s' % event[u'where']
                if event[u'when'] is not None and event[u'when'] != 0:
                    t2 += ", "
                else:
                    t2 += ". "
            if event[u'when'] is not None and event[u'when'] != 0:
                t2 += 'When: %s. ' % format_date(event[u'when'], tz=tz)
            t2 += 'Reply to send a comment, include #in to join.'
            texts.append(t2)
            
            texts.append('What\'s the plan: %(what)s' % 
                         {'username': event[u'creator'], 
                          'what': event[u'what']})
            
        elif message[u'type'] == u'comment':
            texts.append('%(commenter)s commented: %(comment)s' % message)
            if len(texts[-1]) > 160:
                texts[-1] = texts[-1][:157]+"..."
        
        try:
            for text in texts:
                account.request(SMS_OUTPUT_URL, 'POST', {
                        'To': smsee[u'contact_number'],
                        'Body': text,
                        'From': smsee[u'twilio_number'],
                    })
            return True
        except HTTPError, e:
            print e.read()
            return False
        


