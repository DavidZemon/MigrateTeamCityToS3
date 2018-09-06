Migrate TeamCity to Amazon's S3
===============================

TeamCity natively supports storing build artifacts in Amazon's S3 cloud storage. This is a great way to speed up 
artifact downloads and never worry about running out of disk space. Unfortunately, JetBrains does not (currently) 
provide any scripts to help with the migration of an existing server to S3 storage. These scripts are one person's 
attempt to do so.

Instructions
------------

1. Configure TeamCity to start using Amazon's S3 cloud storage for your **root project**. These scripts are only 
   useful for migrating ALL artifacts, so it only makes sense to have TeamCity start using S3 for all future artifacts 
   as well. 
2. Shutdown TeamCity to prevent any concurrency issues.
3. Start by invoking the `awsupload.py` script to get all artifacts into S3.
4. Unfortunately, `awsupload.py` is broken and makes a bad assumption about build configuration names based on 
   artifact paths. You'll need to fix that mistake by updating the `dict` at the top of `awspathfixer.py` and then 
   invoking that script.
5. With all artifacts uploaded and paths fixed, move the old (local) artifacts out of the way by invoking 
   `artifactmover.py`. This allows you to be confident that TeamCity is no longer serving artifacts from the local 
   filesystem (and, whenever you're ready, allows you to free up disk space).
6. Start your TeamCity server and verify functionality.
7. Delete the backup artifact directory that was created in step 5.
