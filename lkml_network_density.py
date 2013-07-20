#!/usr/bin/python
#
# Copyright Makoto Sugano
#
import os
import csv
import subprocess
from datetime import date, datetime
from bs4 import BeautifulSoup

def increment_month(sourcedate):
    month = sourcedate.month
    year = sourcedate.year + month / 12
    month = month % 12 + 1
    day = 1

    return date(year, month, day)

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
    if li_tag.em == None:
        name = "Unidentified"
    else:
        name = li_tag.em.string.strip().encode('utf-8')
        if name == 'Message not available':
            name = "Unidentified"
            
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
    num_mails = 0

# === From and To ===
    for cnt in range(4):
        command = 'wget "http://lkml.indiana.edu/hypermail/linux/kernel/' + year_string + month_string + '.' + str(cnt) + '/index.html' + '" -O -'

        print '=====' + command + '====='
        p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
        (output, err) = p.communicate()

        soup = BeautifulSoup(output)

        for li_tag in soup.find_all("li"):
            from_name = extract_nickname(li_tag)

            # count the mails where the from_name is valid
            if from_name != 'Unidentified':
                num_mails += 1

            # check the level of the thread (0, 1, 2, 3) and the parent (to_name)
            (level, to_name) = report_level_and_to_name(li_tag)

            # Update the Matrix
            if to_name != None:
                if not from_name in network_matrix:
                    network_matrix[from_name] = {}
                
                if not to_name in network_matrix[from_name]:
                    network_matrix[from_name][to_name] = 1
                else:
                    network_matrix[from_name][to_name] += 1

#                print level, from_name, to_name

    return num_mails, network_matrix


def calc_density(network_matrix, name_list):
    lines_cnt = 0 # network lines

    for from_name in name_list:
        for to_name in name_list:
            if to_name in network_matrix[from_name]:
                lines_cnt += 1

    len_name_list = len(name_list)
    density = float(lines_cnt) / float((len_name_list) * (len_name_list - 1))

    return density


#init_date_obj = date(2005, 06, 01) # from  June 2007
#last_date_obj = date(2008, 06, 01) # until June 2013

init_date_obj = date(2008, 07, 01) # from  June 2007
#init_date_obj = date(2008, 11, 01) # from  June 2007
last_date_obj = date(2010, 06, 01) # until June 2013

init_date_obj = date(2010, 07, 01) # from  June 2007
last_date_obj = date(2013, 06, 01) # until June 2013

# http://lkml.indiana.edu/hypermail/linux/kernel/0506.0/index.html

def main():
    curr_date_obj = init_date_obj

    csvfile_name = os.getenv("HOME") + "/Dropbox/src/statistics/lkml_density_over_time-3.csv"
    with open(csvfile_name, 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["month_string", "num_mails", "contributors", "density"])

        while True:
            year_string = curr_date_obj.strftime("%y")
            month_string = curr_date_obj.strftime("%m")
            year_month_string = curr_date_obj.strftime("%Y-%m")

            # wget the file
            # 1. record the network connection
            # 2. generate the name list
            num_mails, network_matrix = gen_network_matrix(year_string, month_string)
            name_list = gen_name_list(network_matrix)
#            print_network_matrix(network_matrix, name_list)
        
            # === Directional Density ===
            density = calc_density(network_matrix, name_list)
            print year_month_string, num_mails, len(name_list), density
            writer.writerow([year_month_string, num_mails, len(name_list), density])

            if curr_date_obj == last_date_obj:
                break;
            else:
                curr_date_obj = increment_month(curr_date_obj)

            

if __name__ == '__main__':
  main()
