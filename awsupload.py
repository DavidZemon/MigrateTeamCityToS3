#!/usr/bin/python3

import argparse
import json
import os
import subprocess

# Set a default local artifact root so that you don't have to type it on the command-line all the time
DEFAULT_LOCAL_ARTIFACT_ROOT = None
# Set a default AWS bucket URI so that you don't have to type it on the command-line all the time
DEFAULT_AWS_BUCKET_URI = None


def run() -> None:
    args = parse_args()

    local_artifact_root = args.local_artifact_root
    aws_bucket_uri = args.aws_bucket_uri
    dry_mode = args.dry

    directory_mapping = {}
    for project in os.listdir(local_artifact_root):
        if not project.startswith('_'):
            local_project_dir = os.path.join(local_artifact_root, project)
            for build_config in os.listdir(local_project_dir):
                local_build_config_dir = os.path.join(local_project_dir, build_config)
                directory_mapping[local_build_config_dir] = '{0}/{0}_{1}'.format(project, build_config)

    for local_dir, remote_dir in directory_mapping.items():
        remote_uri = aws_bucket_uri + '/' + remote_dir
        print('{0} -> {1}'.format(local_dir, remote_uri))
        aws_command = ['aws', 's3', 'sync', '--exclude', '*.teamcity/*', local_dir, remote_uri]
        print('> ' + ' '.join(aws_command))
        if not dry_mode:
            subprocess.run(aws_command)

        write_json_files(local_dir, remote_dir, dry_mode)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument('-l', '--local-artifact-root', default=DEFAULT_LOCAL_ARTIFACT_ROOT,
                        help='Local artifact root to be uploaded. For example, '
                             '`/home/teamcity/.BuildServer/system/artifacts`')
    parser.add_argument('-u', '--aws-bucket-uri', default=DEFAULT_AWS_BUCKET_URI,
                        help='AWS bucket URI where artifacts will be uploaded. Takes the form `s3://<BUCKET_NAME>`, '
                             'such as `s3://my-cool-bucket`')
    parser.add_argument('-d', '--dry', action='store_true',
                        help='Run in "dry" mode where no actions are actually performed, only log statements written '
                             'to the console')

    return parser.parse_args()


def write_json_files(local_dir: str, remote_dir: str, dry: bool) -> None:
    for build_number in os.listdir(local_dir):
        write_json_file(local_dir, remote_dir, build_number, dry)


def write_json_file(local_dir: str, remote_dir: str, build_number: str, dry: bool) -> None:
    local_build_dir = os.path.join(local_dir, build_number)
    artifacts = [os.path.join(local_build_dir, entry) for entry in os.listdir(local_build_dir)
                 if entry != '.teamcity']

    artifact_objects = []
    for artifact in artifacts:
        assert os.path.isfile(artifact), 'Expected {0} to be a file but was not'.format(artifact)
        artifact_objects.append({
            "path": os.path.basename(artifact),
            "size": os.stat(artifact).st_size,
            "properties": {}
        })

    if artifacts:
        the_json = {
            "version": "2017.1",
            # FIXME: This is probably specific to Linux... someone might want to add flexibility someday for Windows
            #        support if this is wrong
            "storage_settings_id": "PROJECT_EXT_4",
            "properties": {
                "s3_path_prefix": "{0}/{1}/".format(remote_dir, build_number)
            },
            "artifacts": artifact_objects
        }
        artifacts_json_file_path = os.path.join(local_build_dir, '.teamcity', 'artifacts.json')
        print('Writing ' + artifacts_json_file_path)
        json_string = json.dumps(the_json, indent=2)
        if dry:
            print(json_string)
        else:
            with open(artifacts_json_file_path, 'w') as f:
                f.write(json_string)


if '__main__' == __name__:
    run()
