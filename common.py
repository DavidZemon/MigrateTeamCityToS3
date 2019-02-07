#!/usr/bin/python3
import sys

import argparse
import os
# Set a default local artifact root so that you don't have to type it on the command-line all the time
from typing import Generator, List

# Set a default path to your local artifact root so that you don't have to type it on the command-line all the time
DEFAULT_LOCAL_ARTIFACT_ROOT = None

# Set a default AWS bucket URI so that you don't have to type it on the command-line all the time
DEFAULT_AWS_BUCKET_URI = None

# Set a default feature ID so that you don't have to type it on the command-line all the time
DEFAULT_FEATURE_ID = None

# Set a default local artifact backup root so that you don't have to type it on the command-line all the time
DEFAULT_ARTIFACT_BACKUP_ROOT = None


def add_local_artifact_root_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('-l', '--local-artifact-root', default=DEFAULT_LOCAL_ARTIFACT_ROOT,
                        required=not DEFAULT_LOCAL_ARTIFACT_ROOT,
                        help='Current local artifact root with TeamCity artifacts. For example, '
                             '`/home/teamcity/.BuildServer/system/artifacts`')


def add_aws_bucket_uri_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('-u', '--aws-bucket-uri', default=DEFAULT_AWS_BUCKET_URI, required=not DEFAULT_AWS_BUCKET_URI,
                        help='AWS bucket URI where artifacts can be stored. Takes the form `s3://<BUCKET_NAME>`, such '
                             'as `s3://my-cool-bucket`')


def add_teamcity_feature_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('-t', '--teamcity-feature', default=DEFAULT_FEATURE_ID, required=not DEFAULT_FEATURE_ID,
                        help='The TeamCity feature identifier for the S3 artifact storage backend, '
                             'such as "PROJECT_EXT_9"')


def add_dry_mode_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('-d', '--dry', action='store_true',
                        help='Run in "dry" mode where no actions are actually performed, only log statements written '
                             'to the console')


def build_results_iter(local_artifact_root: str) -> Generator[str, None, None]:
    for project in sorted(os.listdir(local_artifact_root)):
        if project.startswith('_'):
            continue

        local_project_dir = os.path.join(local_artifact_root, project)
        for build_config in sorted(os.listdir(local_project_dir)):
            local_build_config_dir = os.path.join(local_project_dir, build_config)

            for build_result in sorted(os.listdir(local_build_config_dir), key=int):
                build_result_dir = os.path.join(local_build_config_dir, build_result)

                yield build_result_dir


def get_artifact_list(build_result_dir: str) -> List[str]:
    artifact_list = []
    for root, dirs, files in os.walk(build_result_dir):
        if '/.teamcity/' in root or '\\.teamcity\\' in root or root.endswith('/.teamcity') or root.endswith('\\.teamcity'):  # Skip Teamcity directory, it is not a artifact
            continue
        for file in files:
            full_path = os.path.join(root, file)
            assert os.path.isfile(full_path), \
                "  Found something that is not a file, {}".format(full_path)
            artifact_list.append(full_path)
    return artifact_list


if '__main__' == __name__:
    print('You probably did not mean to invoke this file. Try again.', file=sys.stderr)
