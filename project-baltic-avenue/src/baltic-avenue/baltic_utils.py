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
    
    class C(object):
        pass
    
    rt = C()
    
    acp = find_one(dom,'AccessControlPolicy')
    
   
    rt.owner = C()
    owner = find_one(acp,'Owner')
    rt.owner.id = find_one(owner,'ID').childNodes[0].data
    rt.owner.display_name = find_one(owner,'DisplayName').childNodes[0].data
    rt.grants = []
    
    acl = find_one(acp,'AccessControlList')
    
    for grant_node in find_all(acl,'Grant'):
    
        grant = C()
        grant.grantee = C()
        grantee = find_one(grant_node,'Grantee')
        grant.grantee.id = find_one(grantee,'ID').childNodes[0].data
        display_name_node = find_one(grantee,'DisplayName')
        if display_name_node:
            grant.grantee.display_name = display_name_node.childNodes[0].data
        grant.permission = find_one(grant_node,'Permission').childNodes[0].data      
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
        
    
    