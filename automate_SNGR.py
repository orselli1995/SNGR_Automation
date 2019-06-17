# automate_SNGR.py collection of functions for automating SNGR parametric 
# studies. Calls should go python automate_SNGR path2BaseRepository 
# path2Inputfile caseNameRoot1 caseNameRoot2 ...
# If no caseNameRoots are specified the program assumes all cases

import numpy, re, os, shutil, argparse

parser = argparse.ArgumentParser(
    description = '''My description of how this script works.''',
    epilog = '''For more help/questions email joe.orselli@fft.be''')
#parser.add_argument('PATH', help='Path to the repository of base cases') 
parser.add_argument('FILE', help='Path to the input file containing the SNGR parameters')
#parser.add_argument('--path', '-p', help='Path to the repository of base cases', required = True)
#parser.add_argument('-f', '--file', help='Path to the input file containing the SNGR parameters', required=True)
parser.add_argument('--path', '-p', help='Path to the repository of base cases', required = True)
parser.add_argument('--cases', '-c', nargs='*', default = [], help = '''List of names of the cases from 
the base case repository to be studied. If not specified, use all cases defined in input data file''') 
args = parser.parse_args()

# TODO: perform some checks to ensure that the repository exists, the input parameter file exists, etc.

# Go from relative paths to absolute paths
args.path = os.path.abspath(args.path)
args.FILE = os.path.abspath(args.FILE)

# Retrieve cases from input file if cases list is empty 

if args.cases == []:
    caseNameRegex = re.compile(r'(Case Name: )(\w*)')
    inputFile = open(args.FILE)
    inputLines = inputFile.readlines()
    inputFile.close()
    for line in inputLines:
        if caseNameRegex.search(line) and line != 'Case Name: baseCase_template\n':
            args.cases.append(caseNameRegex.search(line).group(2))

print(args.path)
'''
print(args.path)
print(args.FILE)
print(args.cases)
'''

# For loop through every arguement 2->end and append it to BaseCaseName dictionary. If no argument 
# cases search path2Base for all .edat w/out ICFD and make call that collection BaseCaseName list.

baseCaseName = {}
params = {'freq': None, 'filt': None, 'samp': None, 'thld': None, 'turb': None}

for caseName in args.cases:
    baseCaseName[caseName] = params.copy()

def main():
    ''' Main function for flow control '''

    # Read Input File, extract relevant info using regexes and fill in parameter values in dictionaries
    baseCaseName = extractParams()

    # Build Filetree with dictionary parameters EXCEPT frequency. Populate with base edat files
    #buildTree(baseCaseName)

    # TODO: Edit the pathnames and parameters of the ICFD and Actran analysis accordingly
    editParams(baseCaseName)

    # TODO: Launch each ICFD case. Launch each Actran Analysis

    # TODO: Walk through BaseCase_Parametric filetrees, use session files for post-processing


def extractParams():
    ''' Function for taking SNGR and frequency parameters for each case from the specified file '''

    inputFile = open(args.FILE)
    inputContents = inputFile.readlines()
    freqRegex = re.compile(r'(Frequency: )(.+)(\s)')
    filtRegex = re.compile(r'(Filter: )(.+)(\s)')
    sampRegex = re.compile(r'(# Samples: )(.+)(\s)')
    thldRegex = re.compile(r'(Threshold: )(.+)(\s)')
    turbRegex = re.compile(r'(# Turbulent Modes: )(.+)(\s)')


    for keys in baseCaseName.keys():
        caseRegex = re.compile(r'Case Name: ' + keys)
        for lines in inputContents:
            if caseRegex.search(lines):
                chunk = inputContents[inputContents.index(lines):inputContents.index(lines)+6]
                baseCaseName[keys]['freq'] = freqRegex.search(''.join(chunk)).group(2)
                baseCaseName[keys]['filt'] = filtRegex.search(''.join(chunk)).group(2)
                baseCaseName[keys]['samp'] = sampRegex.search(''.join(chunk)).group(2)
                baseCaseName[keys]['thld'] = thldRegex.search(''.join(chunk)).group(2)
                baseCaseName[keys]['turb'] = turbRegex.search(''.join(chunk)).group(2)
    return baseCaseName

def myRange(spaceDelimStr):
    ''' Similar to np.arange, but working how I think it should work. The ending of a range is
    always included. Also check for user errors in ranges in the input file. '''
    
    range = []
    ranList = spaceDelimStr.split(' ')
    if len(ranList) != 3:
        return [float(spaceDelimStr)]
    start = float(ranList[0])
    step = float(ranList[1])
    end = float(ranList[2])
    
    # TODO: Check that none of the ranges are choosen poorly. If there is a negative value, end < start, 
    # start + step > end, or non-ints for samps and turb modes, stop execution and throw a warning.

    range.append(start)
    while range[-1] < end-step:
        range.append(range[-1] + step)
    range.append(end)
    return range

def buildTree(baseCaseName):
    ''' Make a filetree for the ranges of parameters given, and copy-paste the base case edat files. '''

    for keys in baseCaseName.keys():
        param_list = []
        os.mkdir(keys)
        os.chdir(keys)
        for param_keys in baseCaseName[keys]:
            if param_keys == 'freq':
                continue
            else:
                param_list.append(myRange(baseCaseName[keys][param_keys]))
       
        fold_names = list('filt%.2f_samp%d_thld%.2f_turb%d' % (w, x, y, z) for w in param_list[0]\
                for x in param_list[1] for y in param_list[2] for z in param_list[3])
        for sub_case in fold_names:
            os.mkdir(sub_case)
            shutil.copy(args.path + '\\' + keys + '.edat', sub_case)
            shutil.copy(args.path + '\\' + keys + '_ICFD.edat', sub_case)
        os.chdir('..')

def editParams(baseCaseName)
    ''' Walk over the filetree and make the necessary edits to the edat files using regExes to find
    where to replace necessary parameters'''
    




main()

