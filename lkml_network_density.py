#!/usr/bin/python
#
# Copyright Makoto Sugano
#
import csv
import subprocess
from datetime import date, datetime
from bs4 import BeautifulSoup

# TODO: This should be a nested function
def report_level_and_to_name(li_tag):
    level = -1
    to_tag = li_tag
    to_name = None

    # Level 0
    to_tag = to_tag.parent.parent
    if to_tag != None and to_tag.name != "li":
        level = 0
        to_name = None
        return level, to_name

    # Level 1
    to_tag = to_tag.parent.parent
    if to_tag != None and to_tag.name != "li":
        level = 1
        to_name = extract_nickname(li_tag.parent.parent)
        return level, to_name

    # Level 2
    to_tag = to_tag.parent.parent
    if to_tag != None and to_tag.name != "li":
        level = 2
        to_name = extract_nickname(li_tag.parent.parent)
        return level, to_name

    # Level 3
    to_tag = to_tag.parent.parent
    if to_tag != None and to_tag.name != "li":
        level = 3
        if li_tag.find_previous_sibling("li") != None:
            # you have a previous sibling
            to_name = extract_nickname(li_tag.find_previous_sibling("li"))

        else:
            to_name = extract_nickname(li_tag.parent.parent)

    return level, to_name

def extract_nickname(li_tag):
    name = li_tag.em.string.strip().encode('utf-8')
    return name

def gen_name_list(network_matrix):
    name_list_orig = []
    name_list = []

    for k, v in network_matrix.iteritems():
        name_list_orig.append(k)
        
    name_list = sorted(set(name_list_orig))
    return name_list

def print_network_matrix(network_matrix, name_list):
    for from_name in name_list:
        for to_name in name_list:
            if to_name in network_matrix[from_name]:
                print network_matrix[from_name][to_name],
            else:
                print 0,

        print

##

def gen_network_matrix(year_string, month_string):
# === Initialization ===
    network_matrix = {}

# === From and To ===
    for cnt in range(4):
        command = 'wget "http://lkml.indiana.edu/hypermail/linux/kernel/' + year_string + month_string + '.' + str(cnt) + '/index.html' + '" -O -'

        print '=====' + command + '====='
        p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
        (output, err) = p.communicate()

        soup = BeautifulSoup(output)

        for li_tag in soup.find_all("li"):
            from_name = extract_nickname(li_tag)
            (level, to_name) = report_level_and_to_name(li_tag)
#            print level, from_name, to_name

            # Update the Matrix
            if to_name != None:
                if not from_name in network_matrix:
                    network_matrix[from_name] = {}
                
                if not to_name in network_matrix[from_name]:
                    network_matrix[from_name][to_name] = 1
                else:
                    network_matrix[from_name][to_name] += 1

    return network_matrix

def calc_density(network_matrix, name_list):
    lines_cnt = 0 # network lines

    for from_name in name_list:
        for to_name in name_list:
            if to_name in network_matrix[from_name]:
                lines_cnt += 1

    len_name_list = len(name_list)
    density = float(lines_cnt) / float((len_name_list) * (len_name_list - 1))

    return density


init_date_obj = date(2005, 06, 01) # from  May 2007
last_date_obj = date(2005, 08, 01) # until June 2013

# http://lkml.indiana.edu/hypermail/linux/kernel/0506.0/index.html

def main():
    curr_date_obj = init_date_obj

    while True:
        year_string = curr_date_obj.strftime("%y")
        month_string = curr_date_obj.strftime("%m")
        year_month_string = curr_date_obj.strftime("%Y-%m")

        # wget the file
        # 1. record the network connection
        # 2. generate the name list
        network_matrix = gen_network_matrix(year_string, month_string)
        name_list = gen_name_list(network_matrix)
#        print_network_matrix(network_matrix, name_list)
        
        # === Directional Density ===
        density = calc_density(network_matrix, name_list)
        print year_month_string, len(name_list), density

        if curr_date_obj == last_date_obj:
            break;
        else:
            curr_date_obj = increment_month(curr_date_obj)


if __name__ == '__main__':
  main()
