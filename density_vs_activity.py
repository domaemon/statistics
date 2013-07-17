#!/usr/bin/python
#
# Copyright Makoto Sugano
#
import re
import os
import csv
import subprocess
from datetime import date, datetime

#command = "git tag"
#p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
#(output, err) = p.communicate()
#versions = output.splitlines()

def calc_days(prev_version, version):
    command = 'git log --pretty=format:"%ad" --no-walk ' + version

    p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    m = re.match('\w+ (\w+ \d+) \d+:\d+:\d+ (\d+) .\d+', output)
    if (m):
        date_string = m.group(1) + " " + m.group(2)
        date_obj = datetime.strptime(date_string, '%b %d %Y').date()
        end_date_obj = date_obj
        end_date_string = date_string
    else:
        exit

    command = 'git log --pretty=format:"%ad" --no-walk ' + prev_version

    p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    m = re.match('\w+ (\w+ \d+) \d+:\d+:\d+ (\d+) .\d+', output)
    if (m):
        date_string = m.group(1) + " " + m.group(2)
        date_obj = datetime.strptime(date_string, '%b %d %Y').date()
        start_date_obj = date_obj
        start_date_string = date_string
    else:
        exit

    delta = (end_date_obj - start_date_obj).days

    return (start_date_string, end_date_string, delta)


def calc_changes(prev_version, version):
    command = 'git diff --shortstat ' + prev_version + '..' + version
    p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    
    m = re.match(r" (\d+) files changed, (\d+) insertions\(\+\), (\d+) deletions\(-\)", output)

    if (m):
        files_changed = m.group(1)
        lines_inserted = m.group(2)
        lines_deleted = m.group(3)
        return (files_changed, lines_inserted, lines_deleted)
    else:
        return (None, None, None)
    
def gen_commit_objs(prev_version, version):
    commit_objs = []

    command = 'git log --no-merges ' + prev_version + '..' + version
    p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()

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
    # generating name_list
    name_list_orig = []
    name_list = []

    for commit_obj in commit_objs:
        for name in commit_obj['network']:
            # add the signed-off-by, acked-by, reviewed-by people
            name_list_orig.append(name)

    name_list = sorted(set(name_list_orig))

    return name_list
    
def calc_network_matrix(commit_objs, name_list):

    # init network_matrix
    network_matrix = {}
    for from_name in name_list:
        network_matrix[from_name] = {}

        for to_name in name_list:
            network_matrix[from_name][to_name] = 0
    
    # compute network_matrix
    for commit_obj in commit_objs:
        network_size = len(commit_obj['network'])

        # the last element can *NOT* be from_name
        for from_cnt in (range(network_size - 1)):
            from_name = commit_obj['network'][from_cnt]

            # the last element can be from_name
            for to_cnt in (range(from_cnt + 1, network_size)):
                to_name = commit_obj['network'][to_cnt]
                network_matrix[from_name][to_name] += 1
        

    return network_matrix

def calc_network_density(network_matrix, name_list):
    lines_cnt = 0

    for from_name in name_list:
        for to_name in name_list:
            if network_matrix[from_name][to_name] != 0:
                lines_cnt += 1

    len_name_list = len(name_list)
    density = float(lines_cnt) / float((len_name_list) * (len_name_list - 1))
    print density
    return density



######

os.chdir(os.getenv("HOME") + '/src/linux')

prev_version="v3.1"
versions = ["v3.2", "v3.3", "v3.4", "v3.5", "v3.6", "v3.7", "v3.8", "v3.9"]

csvfile_name = "./density_vs_activity.csv"
with open(csvfile_name, 'w') as csvfile:
    writer = csv.writer(csvfile)

    writer.writerow(["version", "start_date", "end_date", "days", "density", "pathces", "files_changed", "lines_inserted", "lines_deleted"])

### commit_objs_by_version is generated ###
    for version in versions:

        (start_date_string, end_date_string, days) = calc_days(prev_version, version)
        print "=== " + prev_version + "~" + version + " " + str(days) + " days ==="

        # commit_objs consists of commit_obj (includes social network)
        commit_objs = gen_commit_objs(prev_version, version)
        patches = len(commit_objs)

        # name list
        name_list = gen_name_list(commit_objs)
        # network matrix
        network_matrix = calc_network_matrix(commit_objs, name_list)
        # network density
        density = calc_network_density(network_matrix, name_list)
        # added/removed lines
        (files_changed, lines_inserted, lines_deleted) = calc_changes(prev_version, version)
        
        writer.writerow([version, start_date_string, end_date_string, days, density, patches, files_changed, lines_inserted, lines_deleted])

        prev_version = version

