#!/usr/bin/python3
import argparse
import os
import subprocess
import typing

import awsupload
import common

# This takes a mapping of two-tuples to strings, with the following form. The items in the two-tuple key are the
# project name and build configuration as display in TeamCity. The string value is the path used by TeamCity for
# storing artifacts, which follows the pattern <PROJECT_ID>/<PROJECT_ID>_<BUILD_CONFIGURATION_ID>. For example:
#
#   mapping = {
#     ('Base', 'btg25'): 'Base/Base_Btg25',
#     ('Base', 's5t'): 'Base/Base_S5t'
#   }
mapping = {
}


def run() -> None:
    args = parse_args()

    local_artifact_root = args.local_artifact_root
    aws_bucket_uri = args.aws_bucket_uri
    dry_mode = args.dry

    for old_parts, fixed_name in mapping.items():
        old = '{0}/{0}_{1}'.format(*old_parts)
        build_numbers = get_build_numbers(aws_bucket_uri, old)
        for build_number in build_numbers:
            old_s3_uri = build_path(aws_bucket_uri, old + '/' + build_number)
            sub_run(['aws', 's3', 'mv', '--recursive', old_s3_uri,
                     build_path(aws_bucket_uri, fixed_name + '/' + build_number)], dry_mode)
            sub_run(['aws', 's3', 'rm', '--recursive', old_s3_uri], dry_mode)

            local_build_dir = os.path.join(local_artifact_root, old_parts[0], old_parts[1])
            awsupload.write_json_file(local_build_dir, fixed_name, build_number, dry_mode)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    common.add_local_artifact_root_argument(parser)
    common.add_aws_bucket_uri_argument(parser)
    common.add_dry_mode_argument(parser)

    return parser.parse_args()


def write_json_files(local_dir: str, remote_dir: str, dry: bool) -> None:
    for build_number in os.listdir(local_dir):
        awsupload.write_json_file(local_dir, remote_dir, build_number, dry)


def get_build_numbers(aws_bucket_uri: str, old: str) -> typing.List[str]:
    r = subprocess.check_output(['aws', 's3', 'ls', build_path(aws_bucket_uri, old)]).decode()
    build_numbers = []
    for line in r.split('\n'):
        stripped = line.strip()
        if stripped:
            build_numbers.append(stripped.split()[1][:-1])
    return build_numbers


def build_path(aws_bucket_uri: str, p: str) -> str:
    return '{0}/{1}/'.format(aws_bucket_uri, p)


def sub_run(args, dry: bool) -> typing.Optional[subprocess.CompletedProcess]:
    print('> ' + ' '.join(args))
    if not dry:
        return subprocess.run(args)


if '__main__' == __name__:
    run()
