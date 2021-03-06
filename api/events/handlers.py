from api.events.attendance.models import Attendant
from api.events.models import Event
from api.users.models import User
from base_handlers import BaseHandler
from pymongo import DESCENDING
from pymongo.objectid import ObjectId
from tornado.web import HTTPError
from utils import require_auth
import db
import re
import pytz


# Events occuring more than UNTIL_LIMIT milliseconds from now won't
# be displayed
UNTIL_LIMIT = 1000 * 60 * 60 * 24 * 30 # 30d
# Events occuring more than SINCE_LIMIT millie seconds before now
# won't be displayed
SINCE_LIMIT = 1000 * 60 * 60 * 24 * 10 # 10d

# Any character matching this regex is stripped from the username
username_sanitizer = re.compile(r"\W")

class EventsHandler(BaseHandler):
    @require_auth
    def post(self):
        '''
        Creates a new event
        '''
        req_body = self.body_dict()
        event = Event(creator=self.get_session()[u'username'])
        
        #grab data from the user-supplied dict
        what = req_body.get(u'what')
        if what is None:
            self.output({'error': 'MISSING_FIELDS',
                         'field': 'what'}, 400)
            return
        elif len(what) > 140:
            self.output({'error': 'FIELD_LENGTH',
                         'field': 'what'}, 400)
            return
        event[u'what'] = what
        
        where = req_body.get(u'where')
        if where is not None and len(where) > 25:
            self.output({'error': 'FIELD_LENGTH',
                         'field': 'where'}, 400)
            return
        event[u'where'] = where
        
        #optional:
        event[u'broadcast'] = req_body.get(u'broadcast', True)
        event[u'when'] = req_body.get(u'when')
        event[u'posted_from'] = req_body.get(u'posted_from')
        event[u'location'] = req_body.get(u'location')
        event[u'category'] = req_body.get(u'category')
        event[u'client'] = req_body.get(u'client')
    
        event.save()
        resp = dict()
        resp_status = 201
        
        if event[u'broadcast']:
            usernames = self.get_user().followers()
        else:
            usernames = req_body.get(u'users', list())
        
        tz = req_body.get(u'timezone', 'America/Toronto')
        
        out_of_numbers = event.invite(usernames=usernames, 
                                      contacts=req_body.get(u'contacts'),
                                      tz=tz)
        if out_of_numbers is not None:
            resp = {'error': 'OUT_OF_NUMBERS',
                    'contacts': out_of_numbers,
                    'event_revision': event[u'revision']}
            resp_status = 409
        
        resp[u'revision'] = event[u'revision']
        resp[u'id'] = event[u'id']
        self.output(resp, resp_status)

    @require_auth
    def get(self):
        '''
        Gets a list of events
        '''
        #store username for later use
        username = self.get_session()[u'username']
        user = User.get({u'username': username})

        #grab the sorting/filtering types from the args
        #funky names avoid conflict with python builtins
        q_sort = self.get_argument(u'sort', u'soon')
        q_filter = self.get_argument(u'filter', u'invited')
        category = self.get_argument(u'category', None)
        
        if not q_filter in (u'invited', u'creator', u'public'):
            raise HTTPError(404)

        #prep the geospatial info
        lat = self.get_argument('lat', None)
        lng = self.get_argument('lng', None)
        if lat is not None and lng is not None:
            where = [float(lat), float(lng)]
        elif q_sort == u'nearby':
            raise HTTPError(403)

        events_invited = [ObjectId(att[u'event']) for att in 
                          Attendant.find({u'user': user[u'id']})]
        #prep filtering
        if q_filter == 'invited':
            q_filter = {'$or': [
                            {u'creator': username},
                            {u'_id': {'$in': events_invited}},
                            {
                                u'broadcast': True, 
                                u'creator': {'$in': user.following()}
                            }
                        ]}
        elif q_filter == u'creator':
            q_filter = {u'creator': self.get_argument(u'username', username),
                        u'$or': [{u'_id': {'$in': events_invited}},
                                 {u'broadcast': True},
                                 {u'broadcast': False, u'creator': username}]}
        elif q_filter == u'public':
            q_filter = {u'broadcast': True}
            if category is not None:
                q_filter[u'category'] = category 
        
        # This can be uncommented when mongogb gets support for $and
#        # Limit to nearby times
#        q_filter.update({'$or': [{u'when': {u'$lt': timestamp() + UNTIL_LIMIT,
#                                            u'$gt': timestamp() - SINCE_LIMIT}},
#                                 {u'when': None}]})
        
        # Handle geo sorting
        if q_sort == u'nearby':
            #set the sort
            q_filter.update({u'posted_from': {u'$near': where}})
            #use 'soon' as a secondary sort
            q_sort = u'soon'
        
        # Run the query
        events = db.objects.event.find(q_filter, limit=30)

        #perform the required sorting
        if q_sort == u'created':
            events.sort(u'created', direction=DESCENDING)
        elif q_sort == u'soon':
            events.sort(u'when', direction=DESCENDING)
            events.sort(u'created', direction=DESCENDING)

        #output the results
        result = {u'events': [e[u'revision'] for e in events]}
        self.write(result)

class EventHandler(BaseHandler):

    @require_auth
    def delete(self, revision):
        '''
        Deletes an event, if the current user it that event's owner.

        TODO - remove associated attendance
        '''
        event = Event.get({u'revision': revision})
        if event is None: 
            raise HTTPError(404)
        if event[u'creator'] != self.get_user()[u'username']: 
            raise HTTPError(403)

        db.objects.event.remove(event[u'id'], safe=True)
        self.finish()

    @require_auth
    def get(self, revision):
        '''
        TODO - enforce user restrictions
        '''
        #grab the event from the database
        event = Event.get({u'revision': revision})
        if event is None: raise HTTPError(404)
        
        if not event.user_can_access(self.get_user()):
            raise HTTPError(401)
        
        response = {'event': event.serializable()}

        #give the user the attendance info if they asked for it
        if self.request.arguments.get('attendants'):
            response['attendants'] = Attendant.find({u'event': 
                                         event[u'id']}).serializable(name=True)
        self.output(response)









