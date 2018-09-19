Migrate TeamCity to Amazon's S3
===============================

TeamCity natively supports storing build artifacts in Amazon's S3 cloud storage. This is a great way to speed up 
artifact downloads and never worry about running out of disk space. Unfortunately, JetBrains does not (currently) 
provide any scripts to help with the migration of an existing server to S3 storage. These scripts are one person's 
attempt to do so.

Instructions
------------

RECOMMENDED: Modify the constants at the top of `common.py` so that you don't have to provide any command line arguments

## Before you begin
* You MUST configure TeamCity to start using Amazon's S3 cloud storage for your **root project/\<root\>**. 
These scripts are only useful for migrating ALL artifacts, so it only makes sense to have TeamCity
start using S3 for all future artifacts as well. 
* This code is only tested on Linux with Python 3.
* You need to know the "feature ID" for your S3 artifact store configuration. To do this download
your `<root>` project settings in Kotlin format. Inside that Kotlin look for the file `_Self/Project.kt`.  Find a block 
that looks like the one below. The `PROJECT_EXT_91` is the feature ID of this example S3 artifact store.

```        feature {
            id = "PROJECT_EXT_91"
            type = "storage_settings"
            param("secure:aws.secret.access.key", "xxxx")
            param("aws.external.id", "xxxx")
            param("storage.name", "S3 Artifacts")
            param("storage.s3.bucket.name", "teamcity-artifacts")
            param("storage.type", "S3_storage")
            param("aws.access.key.id", "xxxx")
            param("aws.credentials.type", "aws.access.keys")
            param("aws.region.name", "xxxx")
            param("storage.s3.upload.presignedUrl.enabled", "true")
        }
```
* You need awscli installed on oyu TeamCity server. `pip install awscli`.
* You need initialize the default aws cli default profile with credentials that can upload to the
artifact bucket. `aws configure`
* You need to know the S3 bucket name. Rewrite it in url format to look something like this
`s3://bucket_name`
* You need to know the full path to the directory that holds your artifacts. It is named
`artifacts`. On my machine I found where to look from the value of `teamcity.data.path` in the
file at `<install_dir>/conf/teamcity-startup.properties`.

## The migration process

1. Shutdown TeamCity to prevent any concurrency issues.
2. Start by invoking the `awsupload.py` script to get all artifacts into S3.
3. With all artifacts uploaded and paths fixed, move the old (local) artifacts out of the way by invoking 
   `artifactmover.py`. This allows you to be confident that TeamCity is no longer serving artifacts from the local 
   filesystem (and, whenever you're ready, allows you to free up disk space).
4. Start your TeamCity server and verify functionality.
5. Delete the backup artifact directory that was created in step 5.

## Hints for reducing downtime.

Before starting the steps above you you can use the `--ignore_missing` and `--skip_old` with `awsupload.py` to 
perform syncs on live servers. The results will be dirty/inomplete but it will allow you to perform the bulk of 
your data upload while still online.
