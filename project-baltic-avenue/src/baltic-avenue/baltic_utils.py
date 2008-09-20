import re
from xml.sax import saxutils


def date_format_1(value):
    return value.strftime("%Y-%m-%dT%H:%M:%S.000Z")

def date_format_2(value):
    return value.strftime('%a, %d %b %Y %H:%M:%S GMT')

def escape_xml(value):
    return saxutils.quoteattr("'" + value)[2:-1]

def string_to_sign_bytes(value):
    return ' '.join(['%02x' % ord(b) for b in value.encode('utf-8')])

def parse_url_path(url_path):
    """ returns bucket, key parsed from the path """

    m = re.match('^/([^/]+)/?$',url_path)
    if m:
        return (m.group(1),None)
    
    m = re.match('^/([^/]+)/(.+)$',url_path)
    if m:
        return (m.group(1),m.group(2).replace('%25','%'))
    
    return (None,None)

def url_unencode(value):
    return value.replace('%2f','/')

def url_encode(value):
    return value.replace('/','%2f').replace('_','%5f').replace('-','%2d')

def compute_common_prefix(key):
    i = key.rfind('/')
    return '' if i==-1 else key[:i+1]
    
def is_development_server_request(request):
    return request.environ.get('SERVER_SOFTWARE') == 'Development/1.0'

def parse_acl(acl_xml):
    
    import xml.dom.minidom
    
    dom = xml.dom.minidom.parseString(acl_xml)
    xmlns = 'http://s3.amazonaws.com/doc/2006-03-01/'
    
    def find_one(parent, elementName):
        for n in parent.childNodes:
            if n.namespaceURI == xmlns and n.localName == elementName:
                return n
    
    def find_all(parent, elementName):
        for n in parent.childNodes:
            if n.namespaceURI == xmlns and n.localName == elementName:
                yield n
    
    class ClientACL(object):
        def distinct_grants(self):
            for grant in self.grants:
                if grant.grantee.type == 'Group':
                    if len([g for g in self.grants if g != grant and g.grantee.type == 'Group' and g.grantee.uri == grant.uri and g.permission == 'FULL_CONTROL'  ]) ==0:
                        yield grant
                if grant.grantee.type == 'CanonicalUser':
                    if len([g for g in self.grants if g != grant and g.grantee.type == 'CanonicalUser' and g.grantee.id == grant.id and g.permission == 'FULL_CONTROL'  ]) ==0:
                        yield grant
    
    class DynamicObject(object):    # surely there must be a better way to do this
        pass
    
    class Error(Exception):
        pass
    
    class BalticError(Error):
        def __init__(self, message):
            self.message = message
    
    rt = ClientACL()
    
    acp_node = find_one(dom,'AccessControlPolicy')
    
    rt.owner = DynamicObject()
    owner_node = find_one(acp_node,'Owner')
    rt.owner.id = find_one(owner_node,'ID').childNodes[0].data
    rt.owner.display_name = find_one(owner_node,'DisplayName').childNodes[0].data
    rt.grants = []
    
    acl_node = find_one(acp_node,'AccessControlList')
    
    for grant_node in find_all(acl_node,'Grant'):
    
        grant = DynamicObject()
        grant.grantee = DynamicObject()
        grantee_node = find_one(grant_node,'Grantee')
        
        grant.grantee.type = grantee_node.getAttributeNS('http://www.w3.org/2001/XMLSchema-instance','type')
        if not grant.grantee.type in ['CanonicalUser','Group']:
            raise BalticError('Unsupported grantee type [%s]' % grant.grantee.type)
        
        id_node = find_one(grantee_node,'ID')
        if id_node:
            grant.grantee.id = id_node.childNodes[0].data
            
        display_name_node = find_one(grantee_node,'DisplayName')
        if display_name_node:
            grant.grantee.display_name = display_name_node.childNodes[0].data
            
        grant.permission = find_one(grant_node,'Permission').childNodes[0].data   
        
        
        if grant.grantee.type == 'Group':
            grant.grantee.uri = find_one(grantee_node,'URI').childNodes[0].data
        
        rt.grants.append(grant)
     
     
    
    return rt

    
def combine(expensive_seq, inexpensive_seq,fn):
    
    inexpensive_list = list(inexpensive_seq)
    
    for e in expensive_seq:
        
        while len(inexpensive_list) > 0 and fn(inexpensive_list[0]) < fn(e):
            yield inexpensive_list.pop(0)
        
        yield e
    
    while len(inexpensive_list) > 0:
        yield inexpensive_list.pop(0)
        
    
    