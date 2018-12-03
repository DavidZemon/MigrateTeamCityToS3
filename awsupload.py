#!/usr/bin/python3

import argparse
import configparser
import gzip
import itertools
import json
import os
import subprocess
from datetime import datetime
from typing import List

import common


class BadPropertiesFiles(BaseException):
    pass


case_sensitive_parser = configparser.RawConfigParser(delimiters=["="])
case_sensitive_parser.optionxform = lambda option: option


def run() -> None:
    args = parse_args()

    local_artifact_root = args.local_artifact_root
    aws_bucket_uri = args.aws_bucket_uri
    dry_mode = args.dry
    teamcity_feature = args.teamcity_feature
    skip_old = args.skip_old

    for build_result_dir in common.build_results_iter(local_artifact_root):
        print("{}: Working in {}".format(datetime.now().isoformat(' '), build_result_dir))

        artifacts_json_present = os.path.isfile(os.path.join(build_result_dir, '.teamcity', 'artifacts.json'))

        if skip_old and artifacts_json_present:
            print("  Found previous artifacts.json file, skipping sync")
            continue

        try:
            remote_dir = get_remote_path(build_result_dir)
        except BadPropertiesFiles:
            # On canceled builds this may not exists but artifacts also are not a concern then
            print(" Could not find '.teamcity/properties/build.start.properties.gz', this is assumed to be "
                  "caused by a canceled build")
            continue
        remote_uri = aws_bucket_uri + '/' + remote_dir
        aws_command = ['aws', 's3', 'sync', '--exclude', '.teamcity/*', build_result_dir, remote_uri]

        artifact_list = common.get_artifact_list(build_result_dir)

        if len(artifact_list) == 0:
            print("  No artifacts found".format(build_result_dir))
            continue
        if dry_mode:
            print("  Not running '{}'".format(aws_command))
        else:
            print('  > ' + ' '.join(aws_command))
            subprocess.run(aws_command)

        if artifacts_json_present:
            print("  Found previous artifacts.json file, I will not overwrite it!".format(build_result_dir))
            continue
        write_json_file(artifact_list, build_result_dir, remote_dir, teamcity_feature, dry_mode)


def get_remote_path(build_result_dir: str) -> str:
    # Sometimes one of the properties files is bad (empty or too short). In those cases try the other one before giving
    # up
    start_prop_file = os.path.join(build_result_dir, '.teamcity/properties/build.start.properties.gz')
    finish_prop_file = os.path.join(build_result_dir, '.teamcity/properties/build.finish.properties.gz')
    minimum_file_size_bytes = 100  # Consider files that are smaller than this invalid
    if os.path.isfile(start_prop_file) and os.path.getsize(start_prop_file) > minimum_file_size_bytes:
        properties_file = start_prop_file
    elif os.path.isfile(finish_prop_file) and os.path.getsize(finish_prop_file) > minimum_file_size_bytes:
        properties_file = finish_prop_file
    else:
        raise BadPropertiesFiles("No sane looking properties file found in {}".format(build_result_dir))

    with gzip.open(properties_file, mode='rt', encoding="utf8") as fh:
        case_sensitive_parser.read_file(f=itertools.chain(['[global]'], fh))
        all_parameters = case_sensitive_parser['global']

        build_number = all_parameters['teamcity.build.id']
        build_id = all_parameters['system.teamcity.buildType.id']
        project_id = all_parameters['teamcity.project.id']

    return '{project_id}/{build_id}/{build_number}/'.format(project_id=project_id, build_id=build_id,
                                                            build_number=build_number)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    common.add_local_artifact_root_argument(parser)
    common.add_aws_bucket_uri_argument(parser)
    common.add_dry_mode_argument(parser)
    common.add_teamcity_feature_argument(parser)

    parser.add_argument('-s', '--skip-old', action='store_true',
                        help='Skip builds if a artifacts.json is found. Used to skip builds that have already been '
                             'synced')

    return parser.parse_args()


def write_json_file(artifacts: List[str], build_result_dir: str, remote_dir: str, teamcity_feature: str,
                    dry_run: bool) -> None:
    artifact_objects = []
    for full_path in artifacts:
        relative_path = os.path.relpath(full_path, start=build_result_dir)
        artifact_objects.append({
            "path": relative_path,
            "size": os.path.getsize(full_path),
            "properties": {}
        })

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
