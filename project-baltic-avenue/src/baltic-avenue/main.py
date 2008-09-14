

import wsgiref.handlers
import logging
import os

import re

from google.appengine.ext import webapp

from baltic_service_get import *

from baltic_bucket_get import *
from baltic_bucket_head import *
from baltic_bucket_put import *
from baltic_bucket_delete import *

from baltic_object_put import *
from baltic_object_delete import *
from baltic_object_head import *
from baltic_object_get import *

from baltic_utils import *
from baltic_model import *


class MainPage(webapp.RequestHandler):

   
   
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
        
        
    
   
    def update_principals(self):
        
        for p in self.find_principals('principals_public') + self.find_principals('principals_private'):
            q = db.GqlQuery("SELECT * FROM %s WHERE id = :1 LIMIT 1" %  p.__class__.__name__,p.id).get()
            if q:
                logging.info('update %s' % p.id)
                
                q.display_name = p.display_name
                if q.__class__ == UserPrincipal:
                    q.aws_key = p.aws_key
                    q.aws_secret = p.aws_secret
                    q.email = p.email
                if q.__class__ == GroupPrincipal:
                    q.uri = p.uri
                q.put()
            else:
                logging.info('creating %s' % p.id)
                p.put()
        
        
        
    def clear_data(self):
        
        types = [Bucket,ACL,ACLGrant,CommonPrefix,ObjectContents,ObjectInfo,LogRecord]
        
        for t in types:
            
            items = t.all().fetch(100)
            while len(items)>0:
                for i in items: i.delete()
                items = t.all().fetch(100)
        
      
        
        
        
        
    def temp(self):
        
        #self.update_principals()
        self.clear_data()
        return
        
        from datetime import datetime
        
        bucket = 'om2'
        
        b = Bucket.all()[0]
        
        bucket_owner = b.owner.id
        time = now = datetime.utcnow()
        remote_ip = self.request.remote_addr
        requestor = b.owner.id
        data = {'bucket_owner':bucket_owner,'bucket':bucket,'time':time,'remote_ip':remote_ip}
        
        s = '\n'.join(map(lambda x:'%s:%s'%(x,data[x]),data))
        
        self.response.out.write(s)
        return
        r = LogRecord(
                      bucket_owner=bucket_owner,
                      bucket=bucket,
                      time=time,
                      remote_ip = remote_ip)
        
        
        #self.update_principals()
        b = Bucket.gql("WHERE name1 = :1 ",  'bk2').get()
        
        key = 'x' * 512
        
        q = ObjectInfo.all().ancestor(b)
        
        q = q.filter('name1 =', key[0:500])
        q.filter('name2 =', key[500:1000])
        q.filter('name3 =', key[1000:1500])
        
        oi = q.get()
        logging.info(oi)

    def get(self):
                        
        # common to all responses
        self.response.charset = 'utf8'
        del self.response.headers['Cache-Control']
        del self.response.headers['Content-Type']
    
        # TEMP
        if self.request.path == '/test':
            self.temp()
            return
        
        # GET service
        if self.request.path == '/':
            GetServiceOperation(self.request,self.response).go_common() 
            return
        
        
        # GET bucket
        m = parse_url_path(self.request.path)
        if m[0] and not m[1]:
            GetBucketOperation(self.request,self.response).go_common(m[0]) 
            return

        # GET object
        m = parse_url_path(self.request.path)
        if m[0] and m[1]:
            GetObjectOperation(self.request,self.response).go_common(m[0],m[1]) 
            return


        # unsupported
        self.response.set_status(500)
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write(self.request.path)


    
    def put(self):
        
        # common to all responses
        self.response.charset = 'utf8'
        del self.response.headers['Cache-Control']
        del self.response.headers['Content-Type']
        
        # PUT bucket
        m = parse_url_path(self.request.path)
        if m[0] and not m[1]:
            PutBucketOperation(self.request,self.response).go_common(m[0]) 
            return
            
        # PUT object
        m = parse_url_path(self.request.path)
        if m[0] and m[1]:
            PutObjectOperation(self.request,self.response).go_common(m[0],m[1]) 
            return
 
            
        # unsupported
        self.response.set_status(500)
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write(self.request.path)
      
    def delete(self):
        
        # common to all responses
        self.response.charset = 'utf8'
        del self.response.headers['Cache-Control']
        del self.response.headers['Content-Type']
        
        # DELETE bucket
        m = parse_url_path(self.request.path)
        if m[0] and not m[1]:
            DeleteBucketOperation(self.request,self.response).go_common(m[0]) 
            return
        
        # DELETE object
        m = parse_url_path(self.request.path)
        if m[0] and m[1]:
            DeleteObjectOperation(self.request,self.response).go_common(m[0],m[1]) 
            return
            
        # unsupported
        self.response.set_status(500)
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write(self.request.path)
        
    def head(self):
        # common to all responses
        self.response.charset = 'utf8'
        del self.response.headers['Cache-Control']
        del self.response.headers['Content-Type']
        
        # HEAD bucket
        m = parse_url_path(self.request.path)
        if m[0] and not m[1]:
            HeadBucketOperation(self.request,self.response).go_common(m[0]) 
            return
        
        # HEAD object
        m = parse_url_path(self.request.path)
        if m[0] and m[1]:
            HeadObjectOperation(self.request,self.response).go_common(m[0],m[1]) 
            return
    

        
def main():
    
    
    application = webapp.WSGIApplication(
                                       [('.*', MainPage)],
                                       debug=True)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
    main()