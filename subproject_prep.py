#!/usr/bin/env python
###############################################################################
# This prep script does the following:
#
#   1. Looks through all all subdirectories of the script's directory. If
#      a directory contains an executable `pants` or a `pants.ini`, (2)
#
#   2. When a directory containing `pants` or `pants.ini` is found, its
#      path is kept in mind. This directory is then explored where all 
#      BUILD files are detected. For each BUILD file,
#
#       2a. Look through the modules in the BUILD file. If the module contains
#           a `dependencies` field, change all targets (not starting with :) to 
#           be relative to the directory the prep script is located in.
#
#       2b. If changes were made in step (2a), rewrite the BUILD file.
#
#  3. All changes made are recorded so that they can be easily reverted 
#     (eg with a diff)
#
# https://github.com/brandonio21/pants-subproject-prep
###############################################################################
import os
import re
import json
import difflib
import argparse

# List of tuples indicating a pants build root. First element is filename,
# second element is a list of access props that must be true
PANTS_FILES = [('pants', [os.X_OK]), ('pants.ini', [os.R_OK])]
BUILD_FILES = [('BUILD', [os.R_OK])]
DEPS_REGEX = re.compile(r'dependencies\s*=\s*\[\s*([^\[^\]]*)\s*\]', re.DOTALL)
PATCH_FILE = 'subproject_prep_changes.patch'
UNDO_PATCH_FILE = 'subproject_prep_changes_undo.patch'

TARGETS_REGEX = [DEPS_REGEX]

# Establish commandline args
parser = argparse.ArgumentParser(
    description='Replace pantsbuild subproject targets with proper paths'
)
parser.add_argument('buildroot', default=os.getcwd(), nargs='?',
                    help='The path where the pants executable is located')

args = parser.parse_args()
build_root = args.buildroot

def _is_file(path, file_list):
    if not os.path.isfile(path):
        return False

    basename = os.path.basename(path)
    for filename, access_list in file_list:
        if basename == filename:
            if all([os.access(path, perm) for perm in access_list]):
                return True

    return False

def is_pants_file(path):
    return _is_file(path, PANTS_FILES)

def is_build_file(path):
    return _is_file(path, BUILD_FILES)


pants_subproject_dirs = set()
for dirpath, dirnames, filenames in os.walk(build_root):
    if dirpath == build_root:
        continue

    for filename in filenames:
        file_path = os.path.join(dirpath, filename)
        if is_pants_file(file_path):
            pants_subproject_dirs.add(dirpath)


subproject_buildfiles = set()
for subproject_dir in pants_subproject_dirs:
    for dirpath, dirnames, filenames in os.walk(subproject_dir):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            if is_build_file(file_path):
                subproject_buildfiles.add((subproject_dir, file_path))


diff = []
undo_diff = []
for subproject_build_root, buildfile in subproject_buildfiles:
    contents = ''
    with open(buildfile, 'r') as f:
        old_contents = f.read().decode('utf-8')
        contents = str(old_contents)

    for target_regex in TARGETS_REGEX:
        matches = target_regex.findall(contents)

        for dependency_list in matches:
            new_dependency_list = []
            dependency_paths = dependency_list.split(',')
            for dependency_path in dependency_paths:
                if not re.findall(r'\w+', dependency_path):
                    continue

                dependency_path = dependency_path.replace("'", "").replace('"', '').strip()

                if dependency_path.startswith(':'):
                    new_dependency_list.append(dependency_path)
                    continue

                if dependency_path.startswith('//'):
                    dependency_path = dependency_path[2:]

                # Check to see if the change has already been made for this dependency
                subproject_buildroot_base = os.path.basename(subproject_build_root)
                if dependency_path.split('/')[0] == subproject_buildroot_base:
                    new_dependency_list.append(dependency_path)
                    continue

                full_dependency_path = os.path.join(subproject_build_root, dependency_path)
                new_dependency_path = os.path.relpath(full_dependency_path, build_root)
                new_dependency_list.append(new_dependency_path)
            
            new_dependencies = json.dumps(new_dependency_list, indent=4)
            new_dependencies = new_dependencies.replace('\\"', '"')
            contents = re.sub(dependency_list, new_dependencies[1:-1].lstrip(), contents)

        diff.extend(list(difflib.unified_diff(old_contents.splitlines(True), 
                                              contents.splitlines(True),
                                              fromfile=buildfile,
                                              tofile=buildfile)))
        undo_diff.extend(list(difflib.unified_diff(contents.splitlines(True),
                                                   old_contents.splitlines(True),
                                                   fromfile=buildfile,
                                                   tofile=buildfile)))

    with open(buildfile, 'w') as f:
        f.write(contents)


with open(PATCH_FILE, 'w+') as f:
    f.write(''.join(diff))

with open(UNDO_PATCH_FILE, 'w+') as f:
    f.write(''.join(undo_diff))
