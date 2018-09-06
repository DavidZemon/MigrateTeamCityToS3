#!/usr/bin/python3
import argparse
import sys

# Set a default local artifact root so that you don't have to type it on the command-line all the time
DEFAULT_LOCAL_ARTIFACT_ROOT = None

# Set a default AWS bucket URI so that you don't have to type it on the command-line all the time
DEFAULT_AWS_BUCKET_URI = None

# Set a default local artifact backup root so that you don't have to type it on the command-line all the time
DEFAULT_ARTIFACT_BACKUP_ROOT = None


def add_local_artifact_root_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('-l', '--local-artifact-root', default=DEFAULT_LOCAL_ARTIFACT_ROOT,
                        help='Current local artifact root with TeamCity artifacts. For example, '
                             '`/home/teamcity/.BuildServer/system/artifacts`')


def add_aws_bucket_uri_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('-u', '--aws-bucket-uri', default=DEFAULT_AWS_BUCKET_URI,
                        help='AWS bucket URI where artifacts can be stored. Takes the form `s3://<BUCKET_NAME>`, such '
                             'as `s3://my-cool-bucket`')


def add_dry_mode_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('-d', '--dry', action='store_true',
                        help='Run in "dry" mode where no actions are actually performed, only log statements written '
                             'to the console')


if '__main__' == __name__:
    print('You probably did not mean to invoke this file. Try again.', file=sys.stderr)
