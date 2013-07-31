#!/usr/bin/python
#
# Copyright Makoto Sugano
#
import re
import os
import csv
import subprocess
from datetime import date, datetime

# time || contributors || density || patches || files_changed || lines_inserted || lines_deleted
# commit_obj

def increment_month(sourcedate):
    month = sourcedate.month
    year = sourcedate.year + month / 12
    month = month % 12 + 1
    day = 1

    return date(year, month, day)

def decrement_month(sourcedate):
    month = sourcedate.month - 1
    year = (sourcedate.year - 1) if month == 0 else sourcedate.year
    month = 12 if month == 0 else sourcedate.month - 1
    day = 1

    return date(year, month, day)

def gen_commit_objs(since_date_obj, before_date_obj):
    commit_objs = []

    command = 'git log --no-merges --since="' + since_date_obj.isoformat() + '" --before="' + before_date_obj.isoformat() + '"'
    p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()

    for line in output.splitlines():

        # hashtag
        m = re.match('commit ((\w){40})', line)
        if (m):
            hashtag = m.group(1)
            commit_obj = {}
            commit_obj['hashtag'] = hashtag
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
    return density

os.chdir(os.getenv("HOME") + '/src/linux')



# init_date_obj = date(2005, 05, 01) # from April 2005
# last_date_obj = date(2006, 10, 01) # until September 2006

# init_date_obj = date(2005, 07, 01) # from  June 2005
# last_date_obj = date(2013, 07, 01) # until June 2013

init_date_obj = date(2005, 06, 01) # from  June 2005
last_date_obj = date(2005, 10, 01) # until July 2013

def main():
    curr_date_obj = init_date_obj
    prev_name_list = []

    csvfile_name = os.getenv("HOME") + "/Dropbox/src/statistics/developer_retention.csv"
    with open(csvfile_name, 'w') as csvfile:
        writer = csv.writer(csvfile)

        print "month_string", "curr_contributors", "intersect(curr, prev)", "retained/current", "patches", "patches/curr_contributors"
        writer.writerow(["month_string", "curr_contributors", "intersect(curr, prev)", "retained/current", "patches", "patches/curr_contributors"])
        
        while True:
            prev_date_obj = decrement_month(curr_date_obj)
            # note that the curr_date_obj is the next_month_first_day
            year_month_string = prev_date_obj.strftime("%Y-%m")

            # commit_objs consists of commit_obj (includes social network)
            commit_objs = gen_commit_objs(prev_date_obj, curr_date_obj)
            patches = len(commit_objs)

            # name list
            curr_name_list = gen_name_list(commit_objs)
            curr_contributors = len(curr_name_list)

            retained_name_list = list(frozenset(curr_name_list).intersection(prev_name_list))
            retained_contributors = len(retained_name_list)

            print year_month_string, curr_contributors, retained_contributors, float(retained_contributors)/float(curr_contributors), patches, float(patches)/float(curr_contributors)
            writer.writerow([year_month_string, curr_contributors, retained_contributors, float(retained_contributors)/float(curr_contributors), patches, float(patches)/float(curr_contributors)])

            prev_name_list = curr_name_list

            if curr_date_obj == last_date_obj:
                break;
            else:
                curr_date_obj = increment_month(curr_date_obj)

if __name__ == '__main__':
  main()
######
