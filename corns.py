################################################################################
################################################################################
#
#    CoRNS.py version 1.0.1
#
#    Copyright (C) 2016  Jenna Dorey and Nelson R. Salinas
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
################################################################################

import argparse
import datetime
import os

today = datetime.datetime.now()
outfileRootDefault = today.strftime("corns_result_%Y-%m-%d_%H:%M:%S")

parser = argparse.ArgumentParser(description = "CoRNS.py: a Python utility for Complimentary Reserve Selection. The script will run a simple greedy richness algorithm to determine the most diverse site and will then complimentarily add sites based on the diversity composition. Input is a comma delimited site-by-species matrix. The script returns an ordered list of sites to reserve including a running total of the number of species and the percent of the total diversity that are conserved. Optionally provide a site-by-species matrix for a second organismal group to determine what percent of diversity is conserved based on selections for the first group.")

parser.add_argument("-i", required = True, dest = "infile", action = "store", help = "Input file of the site by species matrix in CSV format with species as the row headers and sites as the column headers.")

parser.add_argument("-m", dest = "infile2", action = "store", help = "Site by species matrix for a second organismal group based on reserve selection for first organismal group.")

parser.add_argument("-o", dest = "outfile_root", default = outfileRootDefault, action = "store", help = "Root name of output files. If you do not provide a root file name the default is `result`.")

parser.add_argument("-v", action = "version", version = "corns v. 1.0.1")

args = parser.parse_args()

files = os.listdir(os.getcwd())
outfile_name = "{0}.csv".format(args.outfile_root)
if outfile_name in files:
	print "`{0}` already exists. Outfile name changed to `{1}.csv`".format(outfile_name, outfileRootDefault)
	outfile_name = "{0}.csv".format(outfileRootDefault)

out_matrix = [] # order, site_name, cumulative_spp_first_set, cumulative_percent_first_site
preserved_spp = []
preserved_spp2 = []

def check_file(infile):

	row_count = 0
	prev_col_count = 0
	current_col_count = 0
	species_tmp = {}
	sites_tmp = {}
	sites_names_tmp = []
	sites_diversity_tmp = []

	with open(infile, "r") as fhandle:
		for row in fhandle:
			row = row.rstrip()
			row = row.replace('\'','')
			row = row.replace('\"','')
			if len(row) < 1:
				raise ValueError("Input files cannot contain empty lines (line {0}, file `{1}`).".format(row_count + 1, infile))
			bits = row.split(',')
			current_col_count = len(bits)
			if row_count == 0: # first row
				for ind,bi in enumerate(bits):
					if ind > 0:
						if bi == '':
							raise ValueError("Site name at column {0} is empty (file `{1}`).".format((ind + 1), infile))
						if bi in sites_tmp:
							sites_tmp[bi] += 1  #{bi: 0}
						else:
							sites_tmp[bi] = 1
						sites_names_tmp.append(bi)

			else: # second or greater row
				if prev_col_count != current_col_count:
					raise ValueError("Rows {0} and {1} have differrent number of columns (file `{2}`).".format((row_count),(row_count + 1), infile))

				if row_count == 1: #only in the second row
					# Checking if sites are unique
					for si in sites_tmp:
						if sites_tmp[si] > 1:
							raise ValueError("Site `{0}` is repeated in file `{1}`!!!!".format(si, infile))
						sites_diversity_tmp.append(0)
					# reformatting sites as main data structure -> {site:[list of spp present]}
					sites_tmp = {si : [] for si in sites_names_tmp}

				presences = 0
				for ind,bi in enumerate(bits):
					if ind == 0: # first column
						if bi == '':
							raise ValueError("Species names cannot be empty (line {0}, file `{1}`).".format((row_count + 1), infile))
						if bi in species_tmp:
							species_tmp[bi] += 1  #{bi: 0}
						else:
							species_tmp[bi] = 1
					else: # second column or greater
						if bi != '0' and bi != '1':
							raise ValueError("Species {0} (row {1}) at column {2} (file `{3}`) does not contain a legal value (should be `0` or `1`)".format(bits[0],(row_count + 1),(ind + 1), infile))
						presences += int(bi)
						if bi == '1':
							sites_diversity_tmp[(ind - 1)] += 1
							sites_tmp[sites_names_tmp[(ind - 1)]].append(bits[0])
				# Checking species are present in at least one site
				if presences == 0:
					raise ValueError("{0} is not present in any site (file {1})!!!!".format(bits[0], infile))

			prev_col_count = current_col_count
			row_count += 1

	# Checking is species are not repeated
	for sp in species_tmp:
		if species_tmp[sp] > 1:
			raise ValueError("Species `{0}` is repeated in the file `{1}`!!!".format(sp, infile))

	# Checking is species are not repeated
	for ind,sit in enumerate(sites_diversity_tmp):
		if sit == 0:
			raise ValueError("Site {0} has no species in the file `{1}`!!!".format(sites_names_tmp[ind], infile))

	return (species_tmp, sites_tmp, sites_names_tmp, sites_diversity_tmp)

species, sites, sites_names, sites_diversity = check_file(args.infile)

if args.infile2:
	species2, sites2, sites_names2, sites_diversity2 = check_file(args.infile2)
	if sorted(sites_names) != sorted(sites_names2):
		raise ValueError("Site names in the provided matrices do not match!!!")

first_site = sites_names[sites_diversity.index(max(sites_diversity))]
spp_first_site = len(sites[first_site])
percent_spp_first_site = (float(spp_first_site) / len(species)) * 100
out_matrix = [[1, first_site, spp_first_site, percent_spp_first_site]]
preserved_spp = sites.pop(first_site)
if args.infile2:
	spp_first_site2 = len(sites2[first_site])
	percent_spp_first_site2 = (float(spp_first_site2) / len(species2)) * 100
	preserved_spp2 = sites2.pop(first_site)
	out_matrix = [[1, first_site, spp_first_site, percent_spp_first_site, spp_first_site2, percent_spp_first_site2]]
counter = 1

while sites:
	counter += 1
	selected_site = ""
	selected_gain = 0
	spp_cumulative2 = 0
	percent_spp_cumulative2 = 0.0
	for sit in sites:
		new_spp = filter(lambda x: x not in preserved_spp, sites[sit])
		spp_gain = len(new_spp)
		if selected_gain < spp_gain:
			selected_gain = spp_gain
			selected_site = sit
	if selected_gain == 0: # if no remaining site adds diversity
		selected_site = sites.keys()[0]
	preserved_spp = preserved_spp + filter(lambda x: x not in preserved_spp, sites[selected_site])
	sites.pop(selected_site)
	spp_cumulative = len(preserved_spp)
	percent_spp_cumulative = (float(spp_cumulative) / len(species)) * 100
	if args.infile2:
		preserved_spp2 = preserved_spp2 + filter(lambda x: x not in preserved_spp2, sites2[selected_site])
		sites2.pop(selected_site)
		spp_cumulative2 = len(preserved_spp2)
		percent_spp_cumulative2 = (float(spp_cumulative2) / len(species2)) * 100
		out_matrix.append([counter, selected_site, spp_cumulative, percent_spp_cumulative, spp_cumulative2, percent_spp_cumulative2])
	else:
		out_matrix.append([counter, selected_site, spp_cumulative, percent_spp_cumulative])

bufferito = "Order,Site_name,{0}_species_count,{0}_percent_diversity".format(args.infile)
if args.infile2:
	bufferito += ",{0}_species_count,{0}_percent_diversity".format(args.infile2)
bufferito += "\n"

for line in out_matrix:
	bufferito += "{0},{1},{2},{3:.2f}".format(line[0],line[1],line[2],line[3])
	if args.infile2:
		bufferito += ",{0},{1:.2f}".format(line[4],line[5])
	bufferito += "\n"

with open(outfile_name, "w") as outhandle:
	outhandle.write(bufferito)

exit()
