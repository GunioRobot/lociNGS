#!/usr/bin/python
#convertingLociNGS.py
#S.Hird; 11 july 2011

import re
import pymongo
import json
import sys
import os
from Bio import SeqIO
from Bio.Alphabet import generic_protein, generic_dna, generic_nucleotide
from pymongo import Connection
import datetime 
from constructionMDB import getPopDict
#MongoDB connection
connection = Connection()
db = connection.test_database
loci = db.loci
demographic = db.demographic
now = datetime.datetime.now()


def toNexus (listOfFiles):
	for file in listOfFiles:
		output_handle = file.replace(".fasta", ".nex")
		SeqIO.convert(file, "fasta", output_handle, "nexus", generic_dna)

def toIMa2 (listOfFiles):
	popDict = getPopDict()
	numberPops = len(popDict)
	numberLoci = len(listOfFiles)
	#put names of populations in tuple and string
	namesPops = ""
	print numberPops, numberLoci
	print "popsToUse", popDict
	namesPops = " ".join(sorted(popDict))
	popsToUseTuple = tuple(sorted(popDict))	
	#get the IMa2 parameters from the IMa2InputFile.txt and put in listInput list
	listInput = []
	inputFile = open('IMa2InputFile.txt', 'r')
	rows = [ line.strip().split(': ') for line in inputFile ]
	for row in rows:
		listInput.append(row[1])
	#this prints the header for the IMa2 file - write seems inefficient but it works
	outputFile = open('IMa2_formatted.txt', 'w')
	outputFile.write(listInput[0])
	outputFile.write("\r\n")
	outputFile.write("# file generated by lociNGS on ")
	outputFile.write(now.strftime("%B %d, %Y at %H:%M"))
	outputFile.write("\r\n")
	outputFile.write(str(numberPops))
	outputFile.write("\r\n")
	outputFile.write(namesPops)
	outputFile.write("\r\n")
	outputFile.write(listInput[1])
	outputFile.write("\r\n")
	outputFile.write(str(numberLoci))
	outputFile.write("\r\n")
	for pops, inds in popDict.iteritems():
		popDict[pops].insert(0, -1)    #[0] = -1

	for n in listOfFiles:    #from each input file, n, in the list, pathsToGet...
		dataList = []
		#create dictionary of population keys and save -1 as first value in value list
		for pops, inds in popDict.iteritems():
			popDict[pops][0] = -1
		currentLocusName = ""  #create and text edit locus name
		currentLocusName = re.sub('/.+/', '', n)
		currentLocusName = currentLocusName.replace(".fasta", "")  #also turn header into string, then print once
		print currentLocusName, "current locus name"
		print popDict, "popdict"
		for seq_record in SeqIO.parse(n, "fasta"): #open fasta files, read in indivdiual sequence records
			length = 0
			length = len(seq_record.seq)
			print seq_record.id
			modSeqId = seq_record.id[:-3]
			print modSeqId
			for pop, inds in popDict.iteritems():  #for everything in the popDict dictionary
				if modSeqId in inds:			#if an individual is found in one of the population individual lists
					print "modseqid in inds", modSeqId, inds
					popDict[pop][0] = popDict[pop][0] + 1       #increase counter by 1
					digitLength = 8 - len(pop)     #to ensure seq ID is exactly 10 characters, count prefix, set counter to fill with zeros until 10
					stringID = pop + "_" + str(popDict[pop][0]).zfill(digitLength) + " " + str(seq_record.seq) + "\r\n" #concatenate all the parts, including sequence
					dataList.append(stringID) 			
		locusHeader = ""     	#creating locus headers for output
		locusHeader = currentLocusName + " " 
		for each in popsToUseTuple:
			locusHeader = locusHeader + str(popDict[each][0] + 1) + " "
		mutRateFinal = 0.0000	
		mutRateFinal = float(listInput[4]) / length
		locusHeader = locusHeader + str(length) + " " + listInput[3] + " " + str(mutRateFinal) + "\r\n"
		dataList = sorted(dataList) #make sure in correct order
		outputFile.write(locusHeader)
		for x in dataList:
			outputFile.write(x)	
	forMigrate = outputFile.name
	return forMigrate
			
def toMigrate (IMaInputFile):
	imaList = []
	imaFile = open(IMaInputFile, 'r') #get ima2 file and turn into list of lists
	rows = [ line.strip().split(' ') for line in imaFile ]
	populations = {}
	numberPerLocus = {}
	lengthList = []
	outputFile = open('Migrate_formatted.txt', 'w') #open output and print header
	outputFile.write(str(rows[2][0]))
	outputFile.write(" ")
	outputFile.write(str(rows[5][0]))
	outputFile.write(" file generated by lociNGS on ")
	outputFile.write(now.strftime("%B %d, %Y at %H:%M"))
	outputFile.write("\n")	
	#get number of populations and make a dictionary called "populations" where the population name is the key
	for element in rows[3]:
		populations[element] = []
		numberPops = len(rows[3])		
	for i in range(numberPops+1):  #want to access populations by a number, not a name, so make new dictionary for number of individuals/pop/locus lists
		numberPerLocus[i] = []	
	for line in rows[6:]:   #for each line in the IMa2 file after the header
		if len(line) > 3 :   #if the line contains a locus header
			lengthList.append(line[numberPops+1])  #add the length of the locus to the lengthList
			for numb, numberPer in numberPerLocus.iteritems():   #for each population in the numberPerLocus list
				numberPerLocus[numb].append(line[numb])		#add the number of individuals present at each locus to the correct list
		else:    #if the line is not a locus header, add data to correct population list
			for pop in rows[3]:
				if pop in line[0]:
					populations[pop].append(line)	
	for y in lengthList: #write length data to output
		outputFile.write(y)
		outputFile.write(" ")
	outputFile.write("\n")	
	for i in range(1, numberPops+1):  #write data to output
		for x in numberPerLocus[i]:
			outputFile.write(x)
			outputFile.write(" ")
		outputFile.write(rows[3][i-1])
		outputFile.write("\n")
		for z in populations[rows[3][i-1]]:
			outputFile.write(z[0])
			outputFile.write(" ")
			outputFile.write(z[1])
			outputFile.write("\n")
	
def getRawFastaFromBAM(ind,locusFasta):
	import pysam
	print ind
	locusShort = re.sub('.fasta', '', locusFasta)
#	locusNumber = re.sub('.+_','',locusShort)
	print "locus Short :", locusShort
	file = 'readsFor_'+ind+'_'+locusShort+'.fasta'
	outputFile = open(file, 'w')
	cursor = db.loci.find({"bamPath":{'$exists':True}})
	for y in cursor:
		bamPath = y["bamPath"]
	bam_library = os.listdir(bamPath)
	for bam in bam_library:
		if bam.startswith(ind):
			if bam.endswith(".bam"):
				count = 0
				file = os.path.join(bamPath, bam)
				samfile = pysam.Samfile(file, "rb")
				for reference in samfile.references:
		#			print reference
					if reference.endswith('|'+locusShort):
						print reference, "ref 2\r"
						bamName = ()
						bamName = bam.partition(".")
						locus = reference
						for alignedread in samfile.fetch(locus):
							outputFile.write(">"+bamName[0]+"_"+locusShort+"_"+str(count))
							outputFile.write("\r")
							outputFile.write(alignedread.seq)
							outputFile.write("\r")
							count = count + 1
				samfile.close()
	currentcwd = os.getcwd()
	return currentcwd
				
def getAllRawFastaFromBAM(locusFasta):
	import pysam
	locusShort = re.sub('.fasta', '', locusFasta)
	locusNumber = re.sub('.+_','',locusShort)
	file = 'allReads_'+locusShort+'.fasta'
	outputFile = open(file, 'w') #open output and print header
	cursor = db.loci.find({"bamPath":{'$exists':True}})
	for y in cursor:
		bamPath = y["bamPath"]
	bam_library = os.listdir(bamPath)
	for bam in bam_library:
		if bam.endswith(".bam"):
			count = 0
			file = os.path.join(bamPath, bam)
			samfile = pysam.Samfile(file, "rb")
			for reference in samfile.references:
	#			print reference
				if reference.endswith('|'+locusShort):
					print reference, "ref 2\r"					
					bamName = ()
					bamName = bam.partition(".")
					locus = reference
					for alignedread in samfile.fetch(locus):
						outputFile.write(">"+bamName[0]+"_"+locusShort+"_"+str(count))
						outputFile.write("\r")
						outputFile.write(alignedread.seq)
						outputFile.write("\r")
						count = count + 1
			samfile.close()
	currentcwd = os.getcwd()
	return currentcwd