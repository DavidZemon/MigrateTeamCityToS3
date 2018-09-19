#!/usr/bin/python3

import argparse
import json
import os
import subprocess
import itertools
import gzip
import configparser
from typing import List

import common


def run() -> None:
    args = parse_args()

    local_artifact_root = args.local_artifact_root
    aws_bucket_uri = args.aws_bucket_uri
    dry_mode = args.dry
    teamcity_feature = args.teamcity_feature
    ignore_missing = args.ignore_missing
    skip_old = args.skip_old
    
    for project in sorted(os.listdir(local_artifact_root)):
        if project.startswith('_'):
            continue

        local_project_dir = os.path.join(local_artifact_root, project)
        for build_config in sorted(os.listdir(local_project_dir)):
            local_build_config_dir = os.path.join(local_project_dir, build_config)

            for build_result in sorted(os.listdir(local_build_config_dir),key=int):
                build_result_dir = os.path.join(local_build_config_dir,build_result)

                print("Working in {}".format(build_result_dir))
                
                if skip_old and os.path.isfile(os.path.join(build_result_dir, '.teamcity', 'artifacts.json')):
                    print("  Found previous artifacts.json file, skipping")
                    continue
                    
                # On canceled builds this may not exists but artifacts also are not a concern then
                properties_file = os.path.join(build_result_dir, '.teamcity/properties/build.start.properties.gz')
                if not os.path.isfile(properties_file):
                   print(" Could not find '.teamcity/properties/build.start.properties.gz', this is assumed to be "
                         "caused by a canceled build")
                   continue
                remote_dir = get_remote_path(properties_file)
                remote_uri = aws_bucket_uri + '/' + remote_dir
                aws_command = ['aws', 's3', 'sync', '--exclude', '.teamcity/*', build_result_dir, remote_uri]

                if dry_mode:
                    print("  Not running '{}'".format(aws_command))
                else:
                    artifact_list = list(filter(lambda x: not x.startswith('.teamcity'), os.listdir(build_result_dir)))
                    if len(artifact_list) == 0:
                        print("  No artifacts found'".format(build_result_dir))
                    else:
                        print('  > ' + ' '.join(aws_command))
                        subprocess.run(aws_command)
                        write_json_file(artifact_list, build_result_dir, remote_dir, teamcity_feature, ignore_missing, dry_mode)


def get_remote_path(properties_file: str) -> str:

    with gzip.open(properties_file, mode='rt', encoding="utf8") as fh:
        config = configparser.ConfigParser()
        config.read_file(f=itertools.chain(['[global]'], fh))
        build_number = config['global']['teamcity.build.id']
        build_id = config['global']['system.teamcity.buildtype.id']
        project_id = config['global']['teamcity.project.id']

    return '{project_id}/{build_id}/{build_number}/'.format(project_id=project_id, build_id=build_id, build_number=build_number)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    common.add_local_artifact_root_argument(parser)
    common.add_aws_bucket_uri_argument(parser)
    common.add_dry_mode_argument(parser)
    common.add_teamcity_feature_argument(parser)
    common.add_ignore_missing_argument(parser)
    common.add_skip_old_argument(parser)

    return parser.parse_args()


def write_json_file(artifacts: List[str], build_result_dir: str, remote_dir: str, teamcity_feature: str, ignore_missing:str, dry_run: bool) -> None:
    artifact_objects = []
    missing_file_found=False
    for artifact in artifacts:
        if os.path.isfile(artifact):
            artifact_objects.append({
                "path": os.path.basename(artifact),
                "size": os.stat(artifact).st_size,
                "properties": {}
            })
        else:
            missing_file_found=True
            error_message = 'Expected "{0}" to be a file but was not'.format(artifact)
            if ignore_missing:
                print("  " + error_message)
            else:
                raise Exception(error_message)
        
    # Don't write artifact manifest if we found a irregularity
    if missing_file_found:
        print("  Skipping writing artifacts.json due to missing file")
        return
    
    if artifacts:
        the_json = {
            "version": "2017.1",
            # FIXME: This is probably specific to Linux... someone might want to add flexibility someday for Windows
            #        support if this is wrong
            "storage_settings_id": teamcity_feature,
            "properties": {
                "s3_path_prefix": remote_dir
            },
            "artifacts": artifact_objects
        }
        artifacts_json_file_path = os.path.join(build_result_dir, '.teamcity', 'artifacts.json')
        print('  Writing .teamcity/artifacts.json')
        json_string = json.dumps(the_json, indent=2)
        if dry_run:
            print(json_string)
        else:
            with open(artifacts_json_file_path, 'w') as f:
                f.write(json_string)


if '__main__' == __name__:
    run()
