#!/usr/bin/python
#
# Copyright Makoto Sugano
#
import subprocess
import re
import os
from datetime import date, datetime

#command = "git tag"
#p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
#(output, err) = p.communicate()
#versions = output.splitlines()

def gen_commit_objs_by_version(prev_version, version):
    commit_objs = []

    command = 'git log ' + prev_version + '..' + version
    p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()

    print "=== version: " + prev_version + "~" + version + " ==="
    for line in output.splitlines():

        # hashtag
        m = re.match('commit ((\w){40})', line)
        if (m):
            hashtag = m.group(1)
            commit_obj = {}
            commit_obj['hashtag'] = hashtag
            commit_obj['version'] = version
            commit_obj['author'] = None
            commit_obj['date'] = None
            commit_obj['network'] = []
            commit_objs.append(commit_obj)

        # author
        m = re.match('Author: ((.)+) <(.)+>', line)
        if (m):
            commit_obj['author'] = m.group(1)

        # date
        m = re.match('Date:   \w+ (\w+ \d+) \d+:\d+:\d+ (\d+) .\d+', line)
        if (m):
            date_string = m.group(1) + " " + m.group(2)
            date_obj = datetime.strptime(date_string, '%b %d %Y').date()
            commit_obj['date'] = date_obj

        # signed-off-by
        m = re.match('    Signed-off-by: ((.)+) <(.)+>', line)
        if (m):
            commit_obj['network'].append(m.group(1))

        # acked-by
        m = re.match('    Acked-by: ((.)+) <(.)+>', line)
        if (m):
            commit_obj['network'].append(m.group(1))

        # reviewed-by
        m = re.match('    Reviewed-by: ((.)+) <(.)+>', line)
        if (m):
            commit_obj['network'].append(m.group(1))

    return commit_objs

def gen_name_list(commit_objs):

    return name_list
    
def gen_network_matrix(commit_objs):
    # generating name_list
    name_list_orig = []
    name_list = []

    for commit_obj in commit_objs:
        for name in commit_obj['network']:
            # add the signed-off-by, acked-by, reviewed-by people
            name_list_orig.append(name)

    name_list = sorted(set(name_list_orig))

    # init network_matrix
    network_matrix = {}
    for from_name in name_list:
        network_matrix[from_name] = {}

        for to_name in name_list:
            network_matrix[from_name][to_name] = 0
    
    # compute network_matrix
    for commit_obj in commit_objs:
        network_size = len(commit_obj['network'])
        if (network_size > 1):
            for cnt in (range(network_size - 1)):
                from_name = commit_obj['network'][cnt]
                to_name   = commit_obj['network'][cnt + 1]
                print from_name, to_name
                network_matrix[from_name][to_name] += 1

    return network_matrix

######

os.chdir(os.getenv("HOME") + '/src/linux')

prev_version="v3.9-rc8"
versions = ["v3.9"]
commit_objs_by_version = {}
network_matrix_by_version = {}

### commit_objs_by_version is generated ###
for version in versions:
    commit_objs = gen_commit_objs_by_version(prev_version, version)
    commit_objs_by_version[version] = commit_objs
    network_matrix_by_version[version] = gen_network_matrix(commit_objs)
    print network_matrix_by_version[version]

    prev_version = version

