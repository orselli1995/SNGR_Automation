""" automate_SNGR.py collection of functions for automating SNGR parametric 
studies. If no sepcific case are passes as arguements the program tests all
cases defined in the mandatory SNGR parameter inputfile"""

import numpy, re, os, shutil, argparse, subprocess, sys

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

if not os.path.isfile(args.FILE):
    sys.exit('The input SHGR parameter file address is not valid')

if not os.path.isdir(args.path):
    sys.exit('The input basecase repository pathname does not point to a valid directory')

# Retrieve cases from input file if cases list is empty 

if args.cases == []:
    caseNameRegex = re.compile(r'(Case Name: )(\w*)')
    inputFile = open(args.FILE)
    inputLines = inputFile.readlines()
    inputFile.close()
    for line in inputLines:
        if caseNameRegex.search(line) and line != 'Case Name: baseCase_template\n':
            args.cases.append(caseNameRegex.search(line).group(2))

for case in args.cases:
    if case + '.edat' not in os.listdir(args.path):
        sys.exit('''One or all of the desired cases was not found in the Automation Repository.
        This could be due to:
            1) The name of the case is misspelled in the --cases arguement
            2) The name of the case is misspelled in the input parameter file
            3) The --path arguement does not point to the Automation Repository''')

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
    buildTree(baseCaseName)

    # Edit the pathnames and parameters of the ICFD and Actran analysis accordingly
    editParams(baseCaseName, args.path)

    # Launch each ICFD case. Launch each Actran Analysis
    #local_launcher('icfd')
    #local_launcher('actran')

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

def myRange(spaceDelimStr, parameter_type):
    ''' Similar to np.arange, but working how I think it should work. The ending of a range is
    always included. Also check for user errors in ranges in the input file. '''
    
    ran = []
    ranList = spaceDelimStr.split(' ')
    
    if parameter_type == 'freq' and len(ranList) != 3:
        sys.exit('''The input file is formatted poorly. Frequency must be written as a range,
        in the format START STEP STOP''')

    if len(ranList) == 1:
        if float(spaceDelimStr) < 0:
            sys.exit('''The input file is formatted poorly. Please make sure that no negative values are used
            for SNGR parameters''')
        else:
            return [float(spaceDelimStr)]

    if len(ranList) != 3:
        sys.exit('''The input file is formatted poorly. Please make sure that inputs are either single float
        numbers or 3 space seperated numbers as START STEP STOP''')

    start = float(ranList[0])
    step = float(ranList[1])
    end = float(ranList[2])
    
    # TODO: Check that none of the ranges are choosen poorly. If there is a negative value, end < start, 
    # start + step > end, or non-ints for samps and turb modes, stop execution and throw a warning.
    if start < 0 or stop < 0 or step < 0:
        sys.exit('''The input file is formatted poorly. Please make sure that no negative values are used
        for SNGR parameters''')
    
    if start > stop or start+step*25 < stop:
        sys.exit('''The input file is formatted poorly. Either the range start value > stop value, or the step is 
        too small''')




    ran.append(start)
    while ran[-1] < end-step:
        ran.append(ran[-1] + step)
    ran.append(end)
    return ran

def buildTree(baseCaseName):
    ''' Make a filetree for the ranges of parameters given, and copy-paste the base case edat files. '''

    # Perform a check that the input file is formatted correctly
    for keys in baseCaseName.keys():
        for param_keys in baseCaseName[keys]:
            myRange(baseCaseName[keys][param_keys], param_keys)


    for keys in baseCaseName.keys():
        param_list = []
        os.mkdir(keys)
        os.chdir(keys)
        for param_keys in baseCaseName[keys]:
            if param_keys == 'freq':
                continue
            else:
                param_list.append(myRange(baseCaseName[keys][param_keys], param_keys))
       
        fold_names = list('filt%.2f_samp%d_thld%.2f_turb%d' % (w, x, y, z) for w in param_list[0]\
                for x in param_list[1] for y in param_list[2] for z in param_list[3])
        for sub_case in fold_names:
            os.mkdir(sub_case)
            shutil.copy(args.path + '\\' + keys + '.edat', sub_case)
            shutil.copy(args.path + '\\' + keys + '_ICFD.edat', sub_case)
        os.chdir('..')

def editParams(baseCaseName, repo_path):
    ''' Walk over the filetree and make the necessary edits to the edat files using regExes to find
    where to replace necessary parameters'''

    freqRegex = re.compile(r'(BEGIN FREQUENCY_DOMAIN\s)(.*)\s')
    filtRegex = re.compile(r'(FILTER_AMPLITUDE)\s(.*)')
    sampRegex = re.compile(r'(NUMBER_SAMPLES)\s(.*)')
    thldRegex = re.compile(r'(TURBULENCE_THRESHOLD RELATIVE)\s(.*)')
    turbRegex = re.compile(r'(TURBULENT_MODES)\s(.*)')
    meshRegex = re.compile(r'(NFF\s*FILE)\s(\w*.nff)')
    cfdRegex = re.compile(r'INPUT_FILE (\w*) "(.*)"')
    dirName_filtRegex = re.compile(r'(filt)(.*?)_')
    dirName_sampRegex = re.compile(r'(samp)(.*?)_')
    dirName_thldRegex = re.compile(r'(thld)(.*?)_')
    dirName_turbRegex = re.compile(r'(turb)(.*)')

    for keys in baseCaseName.keys():
        for baseDir, subDir, files in os.walk('.\\' + keys):
            if files == []:
                continue
            
            # Get parameters from directory name
            filt = dirName_filtRegex.search(os.path.basename(baseDir)).group(2)
            samp = dirName_sampRegex.search(os.path.basename(baseDir)).group(2)
            samp = dirName_sampRegex.search(os.path.basename(baseDir)).group(2)
            thld = dirName_thldRegex.search(os.path.basename(baseDir)).group(2)
            turb = dirName_turbRegex.search(os.path.basename(baseDir)).group(2)

            # Read actran analysis into memory, make substitutions to freq, filt, and mesh path, write new file
            actranFile = open(baseDir + '\\' + keys + '.edat')
            actranContent = actranFile.read()
            actranFile.close()
            new_actranContent = freqRegex.sub('\\1 ' + baseCaseName[keys]['freq'] + '\\n', actranContent)
            mesh_path = '..\\..\\' + os.path.relpath(repo_path) + '\\' + keys + '.nff'
            new_actranContent = new_actranContent.replace(meshRegex.search(new_actranContent).group(2), mesh_path)
            new_actranContent = filtRegex.sub('\\1 ' + filt, new_actranContent)
            actranFile = open(baseDir + '\\' + keys + '.edat', 'w')
            actranFile.write(new_actranContent)
            actranFile.close()
            
            # Read ICFD analysis into memory, make substitutions to samp, thld, turb, write new file
            ICFDFile = open(baseDir + '\\' + keys + '_ICFD.edat')
            ICFDContent = ICFDFile.read()
            ICFDFile.close()
            new_ICFDContent = freqRegex.sub('\\1 ' + '\t  ' + baseCaseName[keys]['freq'] \
                + '\\n', ICFDContent)
            cfd_path = '..\\\\..\\\\' + os.path.relpath(repo_path).replace('\\', '\\\\') \
                + '\\\\' + cfdRegex.search(new_ICFDContent).group(2) 
            new_ICFDContent = new_ICFDContent.replace(cfdRegex.search(new_ICFDContent).group(2), cfd_path)
            new_ICFDContent = sampRegex.sub('\\1 ' + samp, new_ICFDContent)
            new_ICFDContent = thldRegex.sub('\\1 ' + thld, new_ICFDContent)
            new_ICFDContent = turbRegex.sub('\\1 ' + turb, new_ICFDContent)
            ICFDFile = open(baseDir + '\\' + keys + '_ICFD.edat', 'w')
            ICFDFile.write(new_ICFDContent)
            ICFDFile.close()

def local_launcher(analysis):
    '''Walk over each case filetree and launch the ICFD cases, then the actran analysis.'''
   

    actranpy_path = os.environ['ACTRAN_PATH'] + '\\Actran_19.0\\bin\\actranpy.bat'
    start_dir = os.getcwd()
    
    for keys in baseCaseName.keys():
        for baseDir, subDir, files in os.walk('.\\' + keys):
            if files == []:
                continue
            os.chdir(os.path.abspath(baseDir))
            files = os.listdir()
            if analysis == 'icfd':
                icfd_file = keys + '_ICFD.edat' 
                inputfile = "--inputfile=" + icfd_file
                subprocess.call([actranpy_path, "-uICFD", inputfile, "--report=report_ICFD"]) 
            if analysis == 'actran':
                #edat_file = [edat for edat in files if (keys in edat and 'ICFD' not in edat)][0]
                edat_file = keys + '.edat'
                inputfile = "--inputfile=" + edat_file
                subprocess.call([actranpy_path, inputfile, "--report=report_Actran"]) 

            os.chdir(start_dir)

main()

