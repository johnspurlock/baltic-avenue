
from google.appengine.api import users
from baltic_model import *

import logging
import cgi

class AdminPage():
    
    def __init__(self,request,response):
        self.response = response
        self.request = request
        
    def go(self):
        
        # forward all logging calls to the html output
        class HtmlHandler():
            
            def __init__(self,response):
                self.response = response
                
            def handle(self,record):
                if not self.response.out.closed:
                    self.response.out.write(u'<pre>%s</pre>'%  cgi.escape(str(record.getMessage()),True))
                    
            level = 0
           
        logging.getLogger().addHandler(HtmlHandler(self.response))
         
         
         
         
        # write out page header
        self.response.set_status(200)
        self.response.headers['Content-Type'] = 'text/html'
        
        self.response.out.write(u'<html><head><title>baltic admin</title></head><body>')
        
        # write out user section
        user = users.get_current_user()
        if user:
            greeting = u'welcome, %s (<a href=\"%s\">sign out</a>)' % (user.nickname(), users.create_logout_url(self.request.path))
        else:
            greeting = u'<a href=\"%s\">sign in</a>' % users.create_login_url(self.request.path)

        self.response.out.write(u'<div>%s</div>' % greeting)
        
        if not users.is_current_user_admin():
            return
        
        
        
        # if admin, write out action list
        self.response.out.write(u'<ul>')
        self.response.out.write(u'<li><a href="?principals">update principals</a></li>')
        self.response.out.write(u'<li><a href="?cleardata=all">clear data - all</a></li>')
        self.response.out.write(u'<li><a href="?cleardata=log-record">clear data - log records</a></li>')
        self.response.out.write(u'</ul>')
        
        
        # if param supplied, perform action
        cleardata = self.request.params.get('cleardata')
        if cleardata:
            self.response.out.write(u'<div>clear data!</div>')
            self.clear_data(cleardata)
            
        if self.request.params.has_key('principals'):
            self.response.out.write(u'<div>update principals!</div>')
            self.update_principals()
              
        
        # write page footer
        self.response.out.write(u'</body></html>')
        
      
    
   
    
    def update_principals(self):
        
        # reloads principals from principals files and re-persists to datastore
        for p in self.find_principals('principals_public') + self.find_principals('principals_private'):
            q = db.GqlQuery("SELECT * FROM %s WHERE id = :1 LIMIT 1" %  p.__class__.__name__,p.id).get()
            if q:
                logging.info('updated %s [%s]' % (p.display_name,p.id))
                
                q.display_name = p.display_name
                if q.__class__ == UserPrincipal:
                    q.aws_key = p.aws_key
                    q.aws_secret = p.aws_secret
                    q.email = p.email
                if q.__class__ == GroupPrincipal:
                    q.uri = p.uri
                q.put()
            else:
                logging.info('creating %s [%s]' % (p.display_name, p.id))
                p.put()
        
        
    def find_principals(self, module_name):
        
        try:
            module = __import__(module_name)
            logging.info('module [%s] found, loading principals...' % module_name)
        except ImportError:
            logging.info('module [%s] not found, no principals loaded' % module_name)
            return []
        except:
            logging.info('error occurred while loading module [%s], no principals loaded' % module_name)
            return []
        return [module.__dict__[x] 
                for x in module.__dict__ 
                if module.__dict__[x].__class__ in (GroupPrincipal,UserPrincipal)]
        
        
        
    def clear_data(self, type):
        
        types = [LogRecord] if type == 'log-record' else [Bucket,ACL,ACLGrant,CommonPrefix,ObjectContents,ObjectInfo,LogRecord]
        
        for t in types:
            c = 0
            items = t.all().fetch(100)
            while len(items)>0:
                for i in items: 
                    i.delete()
                    c += 1
                items = t.all().fetch(100)
            logging.info('deleted %s %s items' % (c,t.__name__))
