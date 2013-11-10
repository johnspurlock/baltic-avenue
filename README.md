![baltic-avenue](http://baltic.s3.amazonaws.com/baltic-avenue.png)

### Description
[baltic-avenue](https://github.com/johnspurlock/baltic-avenue) is an open source clone of the [Amazon S3](http://aws.amazon.com/s3) [REST API](http://docs.amazonwebservices.com/AmazonS3/2006-03-01/) that runs on [Google App Engine](http://code.google.com/appengine/)

### Purpose
This project allows you to host a "private instance of S3" on top of Google's infrastructure (bigtable, etc), leveraging existing client S3 libraries and applications - no need to reinvent the wheel.

### Getting Started
[Download the project](http://baltic-avenue.googlecode.com/files/baltic-avenue-r34.zip) (or get the very latest from source) and run your own instance via the SDK dev server or on production GAE (see **FrequentlyAskedQuestions**: How do I host my own instance?)

or

Try out the public sandbox instance (see **ClientSpecificConfiguration**)
 * host: [http://baltic-avenue.appspot.com]
 * access key id: `test1`
 * secret key: `password1`


### Status
Although the core S3 operations are implemented, this project is still very much in the proof-of-concept phase. i.e. ...
 * [Make It Work  ← still here](http://c2.com/cgi/wiki?MakeItWorkMakeItRightMakeItFast)
 * Make It Right
 * Make It Fast

**Currently Implemented**
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
  
**Limitations**
  * No ssl/https  [(app engine issue)](http://code.google.com/p/googleappengine/issues/detail?id=15)
  * Objects limited to 1MB  [(app engine issue)](http://code.google.com/p/googleappengine/issues/detail?id=78)
  * No bittorrent 
  * No vhost-style requests  [(app engine issue)](http://code.google.com/p/googleappengine/issues/detail?id=113)
  * Content-Encoding (and Content-Length) headers can be saved, but not returned  [(app engine issue)](http://code.google.com/p/googleappengine/issues/detail?id=198)

**Still Pending**
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

### Client Support
The following S3 client libraries/apps can be configured to use a baltic-avenue instance (see **ClientSpecificConfiguration**)
  * [CodePlex.Resourceful](http://www.codeplex.com/resourceful) (and [CodePlex.SpaceBlock](http://www.codeplex.com/spaceblock))  _.net_
  * [jets3t/cockpit](https://jets3t.dev.java.net/)  _java_
  * [boto](http://code.google.com/p/boto/)  _python_
  * [s3sync.rb](http://s3sync.net/wiki)  _ruby_

### More Info
  * There is still quite a bit of development to be done, so any and all contributions/feedback are welcome!


### Data Model
All model definitions reside in `baltic_model.py`.

![data-model](http://baltic.s3.amazonaws.com/datamodel70.png)

You will see nine entity kinds in your datastore (all of the above sans the base-class `Principal`).

### Client-Specific Configuration
In general, you need to use a client that supports:
 * a configurable service host (i.e. to something other than s3.amazonaws.com)
 * a configurable service port (if you plan on running the local sdk dev server on a port != 80)
 * the older path-style S3 request convention
 * an option to choose http over https


**[CodePlex.SpaceBlock](http://www.codeplex.com/spaceblock)**  
Specify the baltic instance host in the S3 Settings screen (Tools->Options->S3). e.g. `baltic-avenue.appspot.com`

**[CodePlex.Resourceful](http://www.codeplex.com/resourceful)**  
Use the existing !S3Connection constructor that takes an !S3Client object:
<pre>
S3Client balticClient = new S3Client("<access-key-id>", "<secret-access-key>", new Uri("http://baltic-avenue.appspot.com"), retryStrategy);
S3Connection balticConnection = new S3Connection(balticClient, RequestStyle.Path);
</pre>

**[jets3t/cockpit](https://jets3t.dev.java.net/)**  
Edit jets3t.properties 
<pre>
s3service.https-only=false
s3service.s3-endpoint=baltic-avenue.appspot.com
s3service.disable-dns-buckets=true
</pre>

**[boto](http://code.google.com/p/boto/)**  
<pre>
conn = S3Connection(
        aws_access_key_id='<access-key-id>',
        aws_secret_access_key='<secret-access-key>',
        host='baltic-avenue.appspot.com',is_secure=False,
        calling_format=OrdinaryCallingFormat())
</pre>

**[s3sync.rb/s3cmd.rb](http://s3sync.net/wiki)**  
Edit s3config.yml
<pre>
aws_access_key_id: <access-key-id>
aws_secret_access_key: <secret-access-key>
ssl_cert_dir: /home/user/s3sync/certs
aws_s3_host: baltic-avenue.appspot.com
</pre>


### Frequently Asked Questions

**How do I host my own instance?**
 * Download the application source
 * Create custom user accounts (see `principals_public.py`)
 * Launch using SDK dev server
 * Browse to /admin, sign in as admin, and run "update principals"
 * Modify `app.yaml`
 * Upload to GAE production using appcfg.py 

**How can I use my existing S3 client or application to connect to a clone instance?**
 * See ClientSpecificConfiguration

**Why can't I upload objects larger than one meg?**
 * This is a limitation of the current pre-release google appengine platform.  It's likely that this restriction will be lifted once the service is pay-as-you-go.

**Why can't I store more than 500 megs?**
 * This is a limitation of the current pre-release google appengine platform.  It's likely that this restriction will be lifted once the service is pay-as-you-go.

**Uh, why "baltic-avenue"?**
 * A callback of sorts to [Park Place](http://code.whytheluckystiff.net/parkplace), a ruby Amazon S3 clone.
