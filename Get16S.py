#!/usr/bin/env python 
# Created by: Lee Bergstrand 
# Descript: A simple program that takes a list of nucleotide genbank accession numbers and 
# downloads the 16S ribosomal RNA contained within the sequences linked to those
# accessions. Its then stores these 16S genes within a multi-sequence fasta file. The
# script also creates a CSV file containing the genomes for which no 16S annotation was found.
#
# Requirements: - This script requires the Biopython module: http://biopython.org/wiki/Download
#               - This script requires the SeqExtract module (included in the Genbank-Downloaders repository)
#               - All accessions must link to regular nucleotide genbank records (genome),
#                 however if a genome is shotgun sequenced you must provide the accession to its Whole
#                 Genome Shotgun Sequence Project record.
#               - Before using this script to access the NCBI's online resources please read the NCBI's 
#                 Entrez User Requirements. If the NCBI finds you are abusing their systems, they can 
#                 and will ban your access! Use the optional email parameter so the NCBI can contact 
#                 you if there is a problem.
#
# Notes: - This script only extracts the first 16S gene found not all the 16S genes.
#  
# Usage: Get16S.py <sequences.txt> [email@mail.com]
# Example: Get16S.py mySeqs.txt JBro@YOLO.com
# ----------------------------------------------------------------------------------------
# ===========================================================================================================
# Imports:

import sys
import csv
from SeqExtract import entrezEmail
from SeqExtract import getSeqRecords
from SeqExtract import isSSProject
from SeqExtract import extractContigs
# ===========================================================================================================
# Functions:


# 1: Checks if in proper number of arguments are passed gives instructions on proper use.
def argsCheck(numArgs):
	if len(sys.argv) < numArgs or len(sys.argv) > numArgs:
		print "Coding Sequence Downloader"
		print "By Lee Bergstrand\n"
		print "Usage: " + sys.argv[0] + " <sequences.txt> [email@mail.com]"
		print "Examples: " + sys.argv[0] + " mySeqs.txt JBro@YOLO.com\n"
		print "Please Note:"
		print "Before using this script to access the NCBI's online resources please read the NCBI's"
		print "Entrez User Requirements. If the NCBI finds you are abusing their systems, they can"
		print "and will ban your access! Use the optional email parameter so the NCBI can contact"
		print "you if there is a problem."
		sys.exit(1)  # Aborts program. (exit(1) indicates that an error occurred)


# ---------------------------------------------------------------------------------------------------------
# 2: Gets reverse complement of DNA string.
def reverseCompliment(sequence):
	sequence.upper()

	basecomplement = {'A': 'T', 'C': 'G', 'G': 'C', 'T': 'A'}
	letters = list(sequence)
	letters = [basecomplement[base] for base in letters]
	sequence = "".join(letters)

	sequence = sequence[::-1]  # Reverses sequence using pythons string slice syntax.
	return sequence


# ---------------------------------------------------------------------------------------------------------
# 3: Gets 16S DNA as a fasta.
def extract16sFasta(organismID, feature, record):
	start = feature.location.nofuzzy_start
	end = feature.location.nofuzzy_end
	strand = feature.location.strand
	sequence = str(record.seq[start:end])  # Extracts subsequence from the genome according to location of the feature.

	if strand == -1:  # Converts subsequence to reverse complement if on negative strand.
		sequence = reverseCompliment(sequence)

	fasta = ">%s\n%s" % (organismID, sequence)
	return fasta


# ---------------------------------------------------------------------------------------------------------
# 4: Gets a list of 16s FASTAs from a genome.
def get16sFasta(sequenceID, record):
	FASTAS = []
	organismID = sequenceID
	features = record.features
	for feature in features:
		if feature.type == "rRNA":
			if "16S" in feature.qualifiers["product"][0]:
				fasta = extract16sFasta(organismID, feature, record)
				if 1000 < len(fasta) < 2000:  # Removes partial sequences and really large sequence do to genbank.
					FASTAS.append(fasta)
	return FASTAS

# ===========================================================================================================
# Main program code:

# House keeping...
argsCheck(3)  # Checks if the number of arguments are correct.
entrezEmail(sys.argv[2])  # Sets up arguments email require for genbank file extraction.

# Stores file one for input checking.
print
">> Opening sequence list..."
inFile = sys.argv[1]

# File extension check
if not inFile.endswith(".txt"):
	print "[Warning] " + inFile + " may not be a txt file!"

# Reads sequence file list and stores it as a string object. Safely closes file.try:
try:
	with open(inFile, "r") as newFile:
		sequences = newFile.read()
		newFile.close()
except IOError:
	print "Failed to open " + inFile
	sys.exit(1)

seqList = sequences.splitlines()  # Splits string into a list. Each element is a single line from the string.

print
"You have listed", len(seqList), "sequences. They are:"
print sequences + "\n"

seqRecords = getSeqRecords(
	seqList)  # Acquires list of sequence record objects from NCBI using the sequence list as reference.

No16sGenomes = []
SixTeens = []
for sequence in seqRecords:
	sequenceID = sequence.id
	No16s = True
	if "plasmid" in sequence.description.lower():  # If sequence is from a plasmid skip the iteration.
		continue
	if isSSProject(sequence):  # If accession is a WGSS project...
		contigList = extractContigs(sequence.id)  # Extract all contig accessions.
		contigRecords = getSeqRecords(contigList)  # Extract sequence record object for each contig.
		for contig in contigRecords:
			fasta = get16sFasta(sequenceID, contig)  # Builds list fasta files.
			if fasta:  # If 16S is found.
				No16s = False
				SixTeens.append(fasta[0])
				break  # If 16S is found in one contig break out and skip all the other contigs
	else:  # If accession is a regular genome...
		fasta = get16sFasta(sequenceID, sequence)  # Builds list fasta files.
		if fasta:
			No16s = False
			SixTeens.append(fasta[0])
	if No16s:  # If not 16S is found add genome to the no 16s found list.
		No16sGenomeInfo = [sequenceID, sequence.annotations["organism"]]
		No16sGenomes.append(No16sGenomeInfo)
OutSixTeens = "\n".join(SixTeens)

try:
	# Attempted to create to output files.
	outFile = "SixTeenSSFromGenbank.fna"
	outCSVFile = "NoSixTeenGenomes.csv"

	print "Writing " + outFile + " to file..."
	writeFile = open(outFile, "w")
	writeFile.write(OutSixTeens)
	writeFile.close()

	if No16sGenomes:
		print "Writing " + outCSVFile + " to file..."
		csvFile = open(outCSVFile, "w")
		CSVWriter = csv.writer(csvFile)
		for genome in No16sGenomes:
			CSVWriter.writerow(genome)
		csvFile.close()
except IOError:
	print "Failed to create " + outFile
	sys.exit(1)

print "Done!"
