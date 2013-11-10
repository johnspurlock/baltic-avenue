baltic-avenue
=============


HomePage.wiki
=============

#summary Copy of home page (to allow edit previewing)

[http://baltic.s3.amazonaws.com/baltic-avenue.png]
==Description==
[http://code.google.com/p/baltic-avenue baltic-avenue] is an open source clone of the [http://aws.amazon.com/s3 Amazon S3] [http://docs.amazonwebservices.com/AmazonS3/2006-03-01/ REST API] that runs on [http://code.google.com/appengine/ Google App Engine]

==Purpose==
This project allows you to host a "private instance of S3" on top of Google's infrastructure (big table, etc), leveraging existing client S3 libraries and applications - no need to reinvent the wheel.

==Getting Started==
[http://baltic-avenue.googlecode.com/files/baltic-avenue-r34.zip Download the project] (or get the very latest [http://code.google.com/p/baltic-avenue/source/browse/#svn/trunk/project-baltic-avenue/src/baltic-avenue from source]) and run your own instance via the SDK dev server or on production GAE (see FrequentlyAskedQuestions: How do I host my own instance?)

or

Try out the public sandbox instance (see [ClientSpecificConfiguration])
 * host: [http://baltic-avenue.appspot.com]
 * access key id: `test1`
 * secret key: `password1`


==Status==
Although the core S3 operations are implemented, this project is still very much in the proof-of-concept phase. i.e. ...
 * [http://c2.com/cgi/wiki?MakeItWorkMakeItRightMakeItFast Make It Work  ← still here]
 * Make It Right
 * Make It Fast

*Currently Implemented*
  * GET service (list buckets)

  * PUT/DELETE/HEAD bucket (create/delete bucket)
  * GET/PUT bucket acl 
  * GET bucket (list bucket contents, including delimiter requests where delimiter = '/')

  * PUT/DELETE object (create/delete objects)
  * GET/HEAD object (get object contents and metadata)

  * Multiple user accounts per instance
  * User-based ACL operations (and "All Users" group to support public reads)
  * Log record info captured and saved to datastore
  * Realistic-looking error responses
  
*Limitations*
  * No ssl/https  [http://code.google.com/p/googleappengine/issues/detail?id=15 (app engine issue)]
  * Objects limited to 1MB  [http://code.google.com/p/googleappengine/issues/detail?id=78 (app engine issue)]
  * No bittorrent 
  * No vhost-style requests  [http://code.google.com/p/googleappengine/issues/detail?id=113 (app engine issue)]
  * Content-Encoding (and Content-Length) headers can be saved, but not returned  [http://code.google.com/p/googleappengine/issues/detail?id=198 (app engine issue)]

*Still Pending*
  * Support `authenticated-read` canned-access policy and `authenticated-users` group
  * Query string authentication
  * Request time too skewed
  * COPY object
  * Testing on non-ascii (and difficult chars) in bucket/keys
  * Conditional gets/range queries
  * POST object
  * Testing on concurrent access/transactions+entity groups
  * Performance tweaks - delayed imports and memcache
  * Location constraints?
  * Bucket access logging? (once/if GAE supports async processing)
  * Include object-size in log-record

==Client Support==
The following S3 client libraries/apps can be configured to use a baltic-avenue instance (see [ClientSpecificConfiguration])
  * [http://www.codeplex.com/resourceful CodePlex.Resourceful] (and [http://www.codeplex.com/spaceblock CodePlex.SpaceBlock])  _.net_
  * [https://jets3t.dev.java.net/ jets3t/cockpit]  _java_
  * [http://code.google.com/p/boto/ boto]  _python_
  * [http://s3sync.net/wiki s3sync.rb]  _ruby_

==More Info==
  * There is still quite a bit of development to be done, so any and all contributions/feedback are welcome!
  * [FrequentlyAskedQuestions]
  * [TechnicalDocumentation]


TechnicalDocumentation.wiki
===========================
  
#summary Details on the implementation
#labels Featured

==Data Model==
All model definitions reside in [http://code.google.com/p/baltic-avenue/source/browse/trunk/project-baltic-avenue/src/baltic-avenue/baltic_model.py baltic_model.py].

[http://baltic.s3.amazonaws.com/datamodel70.png]

You will see nine entity kinds in your datastore (all of the above sans the base-class Principal).


ClientSpecificConfiguration.wiki
================================

#summary How to configure various third-party S3 clients for baltic-avenue access
#labels Featured

=Client-Specific Configuration=
In general, you need to use a client that supports:
 * a configurable service host (i.e. to something other than s3.amazonaws.com)
 * a configurable service port (if you plan on running the local sdk dev server on a port != 80)
 * the older path-style S3 request convention
 * an option to choose http over https


==[http://www.codeplex.com/spaceblock CodePlex.SpaceBlock]==
Specify the baltic instance host in the S3 Settings screen (Tools->Options->S3). e.g. `baltic-avenue.appspot.com`

==[http://www.codeplex.com/resourceful CodePlex.Resourceful]==
Use the existing !S3Connection constructor that takes an !S3Client object:
{{{
S3Client balticClient = new S3Client("<access-key-id>", "<secret-access-key>", new Uri("http://baltic-avenue.appspot.com"), retryStrategy);
S3Connection balticConnection = new S3Connection(balticClient, RequestStyle.Path);
}}}

==[https://jets3t.dev.java.net/ jets3t/cockpit]==
Edit jets3t.properties 
{{{
s3service.https-only=false
s3service.s3-endpoint=baltic-avenue.appspot.com
s3service.disable-dns-buckets=true
}}}

==[http://code.google.com/p/boto/ boto]==
{{{
conn = S3Connection(
        aws_access_key_id='<access-key-id>',
        aws_secret_access_key='<secret-access-key>',
        host='baltic-avenue.appspot.com',is_secure=False,
        calling_format=OrdinaryCallingFormat())
}}}

==[http://s3sync.net/wiki s3sync.rb/s3cmd.rb]==
Edit s3config.yml
{{{
aws_access_key_id: <access-key-id>
aws_secret_access_key: <secret-access-key>
ssl_cert_dir: /home/user/s3sync/certs
aws_s3_host: baltic-avenue.appspot.com
}}}


FrequentlyAskedQuestions.wiki
=============================

#summary Frequently Asked Questions
#labels Featured

==How do I host my own instance?==
 * Download the application source
 * Create custom user accounts (see [http://code.google.com/p/baltic-avenue/source/browse/trunk/project-baltic-avenue/src/baltic-avenue/principals_public.py principals_public.py])
 * Launch using SDK dev server
 * Browse to /admin, sign in as admin, and run "update principals"
 * Modify [http://code.google.com/p/baltic-avenue/source/browse/trunk/project-baltic-avenue/src/baltic-avenue/app.yaml app.yaml]
 * Upload to GAE production using appcfg.py 

==How can I use my existing S3 client or application to connect to a clone instance?==
 * See ClientSpecificConfiguration

==Why can't I upload objects larger than one meg?==
 * This is a limitation of the current pre-release google appengine platform.  It's likely that this restriction will be lifted once the service is pay-as-you-go.

==Why can't I store more than 500 megs?==
 * This is a limitation of the current pre-release google appengine platform.  It's likely that this restriction will be lifted once the service is pay-as-you-go.

==Uh, why "baltic-avenue"?==
 * A callback of sorts to [http://code.whytheluckystiff.net/parkplace Park Place], a ruby Amazon S3 clone.
