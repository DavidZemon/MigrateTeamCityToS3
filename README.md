Migrate TeamCity to Amazon's S3
===============================

TeamCity natively supports storing build artifacts in Amazon's S3 cloud storage. This is a great way to speed up 
artifact downloads and never worry about running out of disk space. Unfortunately, JetBrains does not (currently) 
provide any scripts to help with the migration of an existing server to S3 storage. These scripts are one person's 
attempt to do so.

Instructions
------------

RECOMMENDED: Modify the constants at the top of `common.py` so that you don't have to provide any command line arguments

### Before you begin

* You MUST configure TeamCity to start using Amazon's S3 cloud storage for your **root project/\<root\>**. 
  These scripts are only useful for migrating ALL artifacts, so it only makes sense to have TeamCity
  start using S3 for all future artifacts as well. 
* This code is only tested on Linux with Python 3.
* You need `awscli` installed on your TeamCity server: `pip3 install awscli`
* You need to initialize the default AWS CLI profile with credentials that can upload to the artifact bucket:
  `aws configure`
* Make your life easier by providing user-specific configuration parameters in at the top of `common.py`. Skipping 
  this step means that you will have to provide the same information on the command-line each time you invoke 
  `awsupload.py`:
  * Absolute path to local artifacts: This is the absolute path to the root of your local TeamCity artifacts. It is 
    named `artifacts` by default. On my machine I found where to look from the value of `teamcity.data.path` in the
    file at `<install_dir>/conf/teamcity-startup.properties`.
  * The feature ID for the AWS storage feature in TeamCity: this will be used in a new settings file for each 
    build of each project, which describes where TeamCity can find that build's artifacts. This string can be found 
    in the `<Root project>`'s Kotlin settings:
    1. Go the `Administration` page in TeamCity
    2. Dive into the `<Root project>` project
    3. Find the `Actions` dropdown in the top right of the page and select `Download settings in Kotlin format`
    4. Extract the contents and open `_Self/Project.kt` for viewing
    5. Find a block of text that looks similar to the following (hint: search for `storage_settings`):
       ```
       feature {
           id = "PROJECT_EXT_9"
           type = "storage_settings"
           param("secure:aws.secret.access.key", "xxxx")
           param("aws.external.id", "xxxx")
           param("storage.name", "S3 Artifacts")
           param("storage.s3.bucket.name", "david-zemon-teamcity-artifacts")
           param("storage.type", "S3_storage")
           param("aws.access.key.id", "xxxx")
           param("aws.credentials.type", "aws.access.keys")
           param("aws.region.name", "xxxx")
           param("storage.s3.upload.presignedUrl.enabled", "true")
       }
       ```
       The value you're looking for is the `id` property. In my case, it was `PROJECT_EXT_9`.
  * S3 bucket URL: This is the name of your S3 bucket with the prefix `s3://`, such as 
    `s3://david-zemon-teamcity-artifacts`
  * AWS key and AWS secret: These are the credentials that will be used to connect to AWS and synchronize your 
    artifacts. They can be found in the above-mentioned Kotlin file, `~/.aws/credentials` or new ones can be created in 
    the IAM console

### The migration process

1. Shutdown TeamCity to prevent any concurrency issues.
2. Invoke the `awsupload.py` script to get all artifacts into S3.
3. Move the old (local) artifacts out of the way by invoking `artifactmover.py`. This allows you to be confident that
   TeamCity is no longer serving artifacts from the local filesystem (and, whenever you're ready, allows you to free 
   up disk space).
   NOTE: You can not just move your entire `artifacts` directory to another location. TeamCity will continue to store
   metadata in this directory and, if it is lost, TeamCity will have no way to know where your artifacts are in S3.
4. Start your TeamCity server and verify functionality.
5. Delete the backup artifact directory that was created in step 3.

### Hints for reducing downtime.

Before starting the steps above you you can use `awsupload.py` to perform syncs on 
live servers. The results may be dirty/incomplete but it will allow you to perform the bulk of 
your data upload while still online. 

If you need to run `awsupload.py` multiple times you can use `--skip-old` to speed up the build.
