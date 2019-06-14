# automate_SNGR.py collection of functions for automating SNGR parametric 
# studies. Calls should go python automate_SNGR path2BaseRepository 
# path2Inputfile caseNameRoot1 caseNameRoot2 ...
# If no caseNameRoots are specified the program assumes all cases

import numpy, re, os, sys, argparse

parser = argparse.ArgumentParser(
    description = '''My description of how this script works.''',
    epilog = '''For more help/questions email joe.orselli@fft.be''')
parser.add_argument('--repository', help='Path to the repository of base cases')
parser.add_argument('--inputdata', help='''Path to the input file containing the SNGR parameters for 
        each case to be studied''')
parser.add_argument('--cases', nargs='*', default = [], help = '''List of names of the cases from 
the base case repository to be studied. If not specified, use all cases defined in input data file''') 
args = parser.parse_args()

# TODO: perform some checks to ensure that the repository exists, the input parameter file exists, etc.

# Go from relative paths to absolute paths
args.repository = os.path.abspath(args.repository)
args.inputdata = os.path.abspath(args.inputdata)

# Retrieve cases from input file if cases list is empty 

if args.cases == []:
    caseNameRegex = re.compile(r'(Case Name: )(\w*)')
    inputFile = open(args.inputdata)
    inputLines = inputFile.readlines()
    for line in inputLines:
        if caseNameRegex.search(line) and line != 'Case Name: baseCase_template\n':
            args.cases.append(caseNameRegex.search(line).group(2))

print(args.repository)
print(args.inputdata)
print(args.cases)

# For loop through every arguement 2->end and append it to BaseCaseName dictionary. If no arguments
# after 2, search path2Base for all .edat w/out ICFD and make call that collection BaseCaseName list.
"""
edatFiles = []
baseCaseName = {}
params = {'freq': None, 'filt': None, 'samp': None, 'thld': None, 'turb': None}

for caseName in args.cases:
    baseCaseName[caseName] = params
    else:
        edatRegex = re.compile('edat')
        ICFDRegex = re.compile('ICFD')
        for files in os.listdir(path2Base):
            if edatRegex.search(files) and (ICFDRegex.search(files) == None):
                print(files)
                baseCaseName[files[:-5]] = params
"""
# Main function for flow control 
def main():
    print('it goes')
    # TODO: Read Input File, extract relevant info using regexes and fill in parameter values in dictionaries

    # TODO: Copy-paste the BaseCase Files into each sub-directory

    # TODO: Edit the pathnames and parameters of the ICFD and Actran analysis accordingly

    # TODO: Launch each ICFD case. Launch each Actran Analysis

    # TODO: Walk through BaseCase_Parametric filetrees, use session files for post-processing

main()

