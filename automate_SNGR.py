""" automate_SNGR.py collection of functions for automating SNGR parametric 
studies. If no sepcific case are passes as arguements the program tests all
cases defined in the mandatory SNGR parameter inputfile"""

import numpy, re, os, shutil, argparse, subprocess, sys, logging

parser = argparse.ArgumentParser(
    description = '''My description of how this script works.''',
    epilog = '''For more help/questions email joe.orselli@fft.be''')
parser.add_argument('FILE', help='Path to the input file containing the SNGR parameters')
parser.add_argument('--cases', '-c', nargs='*', default = [], help = '''List of names of the cases from 
the base case repository to be studied. If not specified, use all cases defined in input data file''') 
parser.add_argument('--path', '-p', help='Path to the repository of base cases', required = True)
args = parser.parse_args()

logging.basicConfig(level = logging.DEBUG, format=' %(levelname)s - %(message)s')

# Perform some checks to ensure that the repository exists, the input parameter file exists, etc.

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

baseCaseLIMITS = {}
paramsLIMITS = {'filt': None, 'samp': None, 'thld': None, 'turb': None}

baseCaseCOMPINFO = {}
paramsCOMPINFO = {'Machine': None, 'Queue': None, 'RAM Allocated': None, '# Procs': None, '# Threads': None}


for caseName in args.cases:
    baseCaseName[caseName] = params.copy()
    baseCaseLIMITS[caseName] = paramsLIMITS.copy()
    baseCaseCOMPINFO[caseName] = paramsCOMPINFO.copy()

def main():
    ''' Main function for flow control '''

    # Read Input File, extract relevant info using regexes and fill in parameter values in dictionaries
    [baseCaseName, baseCaseLIMITS] = extractParams()

    # Build Filetree with dictionary parameters EXCEPT frequency. Populate with base edat files
    #buildTree(baseCaseName, baseCaseLIMITS)

    # Edit the pathnames and parameters of the ICFD and Actran analysis accordingly
    #editParams(baseCaseName, args.path)

    # Launch each ICFD case. Launch each Actran Analysis
    #local_launcher('icfd')
    #local_launcher('actran')

    # TODO: Walk through BaseCase_Parametric filetrees, use session files for post-processing
    post_pro()


def extractParams():
    ''' Function for taking SNGR and frequency parameters for each case from the specified file '''

    inputFile = open(args.FILE)
    inputContents = inputFile.readlines()
    inputFile.close()

    defaultsFile = open(args.path + '\\case_defaults.txt')
    defaultsContents = defaultsFile.readlines()
    defaultsFile.close()

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
                baseCaseName[keys]['freq'] = freqRegex.search(''.join(chunk)).group(2).strip()
                baseCaseName[keys]['filt'] = filtRegex.search(''.join(chunk)).group(2).strip()
                baseCaseName[keys]['samp'] = sampRegex.search(''.join(chunk)).group(2).strip()
                baseCaseName[keys]['thld'] = thldRegex.search(''.join(chunk)).group(2).strip()
                baseCaseName[keys]['turb'] = turbRegex.search(''.join(chunk)).group(2).strip()

        for lines in defaultsContents:
            if caseRegex.search(lines):
                chunk = defaultsContents[defaultsContents.index(lines):defaultsContents.index(lines)+16]
                baseCaseLIMITS[keys]['freq'] = baseCaseName[keys]['freq']
                baseCaseLIMITS[keys]['filt'] = filtRegex.search(''.join(chunk)).group(2).strip()
                baseCaseLIMITS[keys]['samp'] = sampRegex.search(''.join(chunk)).group(2).strip()
                baseCaseLIMITS[keys]['thld'] = thldRegex.search(''.join(chunk)).group(2).strip()
                baseCaseLIMITS[keys]['turb'] = turbRegex.search(''.join(chunk)).group(2).strip()

    return [baseCaseName, baseCaseLIMITS]


def check_myRange(spaceDelimStr, case, parameter_type, limit):
    '''Similar to myRange, only for checking for user errors in ranges and value choices in the input file.'''

    ran = []
    ranList = spaceDelimStr.split(' ')
    ranList = [a for a in ranList if a != '']
    
    # Test lower or upper values in ranList against limits. If the user has specificed limits beyond
    # what is recommended in the defaults file, throw a warning
    if parameter_type == ('thld' or 'filt'):
        if ranList[-1] > limit:
            warn = '''The maximum %s limit is exceeded for the %s case. Consider changing it 
            so that the maximum value is less than %s''' % (parameter_type, case, limit)
            logging.warning(warn)

    if parameter_type == ('samp' or 'turb'):
        if ranList[0] < limit:
            warn = '''The minimum %s limit is exceeded for the %s case. Consider changing it 
            so that the minimum value is greater than %s''' % (parameter_type, case, limit)
            logging.warning(warn)

    if parameter_type == 'freq' and len(ranList) != 3:
        sys.exit('''The input file is formatted poorly. Frequency must be written as a range,
        in the format START STEP STOP''')

    if len(ranList) == 1:
        if round(float(spaceDelimStr),2) < 0:
            sys.exit('''The input file is formatted poorly. Please make sure that no negative values are used
            for SNGR parameters''')
        else:
            return [round(float(spaceDelimStr),2)]

    if len(ranList) != 3:
        sys.exit('''The input file is formatted poorly. Please make sure that inputs are either single round(float
        numbers or 3 space seperated numbers as START STEP STOP''')

    start = round(float(ranList[0]),2)
    step = round(float(ranList[1]),2)
    end = round(float(ranList[2]),2)
    
    # Check that none of the ranges are choosen poorly. If there is a negative value, end < start, 
    # start + step > end, or non-ints for samps and turb modes, stop execution and throw an error.
    if start < 0 or end < 0 or step < 0:
        sys.exit('''The input file is formatted poorly. Please make sure that no negative values are used
        for SNGR parameters''')
    
    if start > end or start+step*25 < end:
        sys.exit('''The input file is formatted poorly. Either the range start value > stop value, or the step is 
        too small''')


def myRange(spaceDelimStr):
    '''Similar to np.arange, but working how I think it should work. The ending of a range is
    always included.''' 
  
    ran = []
    ranList = spaceDelimStr.split(' ')
    ranList = [a for a in ranList if a != '']

    if len(ranList) == 1:
        return [round(float(spaceDelimStr),2)]

    start = round(float(ranList[0]),2)
    step = round(float(ranList[1]),2)
    end = round(float(ranList[2]),2)
    
    ran.append(start)
    while ran[-1] < end-step:
        ran.append(round(ran[-1] + step, 2))
    ran.append(end)
    return ran

def buildTree(baseCaseName, baseCaseLIMITS):
    ''' Make a filetree for the ranges of parameters given, and copy-paste the base case edat files. '''

    # Perform a check that the input file is formatted correctly
    for keys in baseCaseName.keys():
        for param_keys in baseCaseName[keys]:
            check_myRange(baseCaseName[keys][param_keys], keys, param_keys, baseCaseLIMITS[keys][param_keys])


    # For over each case being run
    for keys in baseCaseName.keys():
        count = 0
        os.mkdir(keys)
        os.chdir(keys)
        # For over each parameter to be varied
        for param_keys in baseCaseName[keys]:
            if param_keys == 'freq':
                continue
            else:
                subcases = myRange(baseCaseName[keys][param_keys])
                if len(subcases) == 1:
                    count += 1 
                    if count == 4:
                        os.mkdir('No_Parametric_Study')
                        os.chdir('No_Parametric_Study')
                        subdir = 'filt_%ssamp_%sthld_%sturb_%s' % (baseCaseName[keys]['filt'], \
                            baseCaseName[keys]['samp'], baseCaseName[keys]['thld'], baseCaseName[keys]['turb'])
                        os.mkdir(subdir)
                        shutil.copy(args.path + '\\' + keys + '.edat', subdir)
                        shutil.copy(args.path + '\\' + keys + '_ICFD.edat', subdir)
                        os.chdir('..')
                    continue
                else:
                    os.mkdir(param_keys)
                    # For over each value the parameter being varied may take on
                    for subcase in subcases:
                        subcase_dir = param_keys + '_' + str(subcase)
                        os.chdir(param_keys)
                        os.mkdir(subcase_dir)
                        shutil.copy(args.path + '\\' + keys + '.edat', subcase_dir)
                        shutil.copy(args.path + '\\' + keys + '_ICFD.edat', subcase_dir)
                        os.chdir('..')

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
    dirName_filtRegex = re.compile(r'(filt)_([\d,\.]*)')
    dirName_sampRegex = re.compile(r'(samp)_([\d,\.]*)')
    dirName_thldRegex = re.compile(r'(thld)_([\d,\.]*)')
    dirName_turbRegex = re.compile(r'(turb)_([\d,\.]*)')


    param_list = []

    for keys in baseCaseName.keys():
        # Get param_list for file edits
        for param_keys in baseCaseName[keys]:
            param_list.append(myRange(baseCaseName[keys][param_keys]))

        # Default parameter values
        filt = str(param_list[1][0]) 
        samp = str(param_list[2][0]) 
        thld = str(param_list[3][0])
        turb = str(param_list[4][0])

        # Walk over path, make edits appropriatley
        for baseDir, subDir, files in os.walk('.\\' + keys):
            if files == []:
                continue

            # Check what parameter directory currently in, and edit the corresponding parameter value
            if 'filt' in baseDir:
                filt = dirName_filtRegex.search(os.path.basename(baseDir)).group(2) 
            if 'samp' in baseDir:
                samp = dirName_sampRegex.search(os.path.basename(baseDir)).group(2) 
            if 'thld' in baseDir:
                thld = dirName_thldRegex.search(os.path.basename(baseDir)).group(2) 
            if 'turb' in baseDir:
                turb = dirName_turbRegex.search(os.path.basename(baseDir)).group(2) 

            # Read actran analysis into memory, make substitutions to freq, filt, and mesh path, write new file
            actranFile = open(baseDir + '\\' + keys + '.edat')
            actranContent = actranFile.read()
            actranFile.close()
            new_actranContent = freqRegex.sub('\\1 ' + baseCaseName[keys]['freq'] + '\\n', actranContent)
            mesh_path = '..\\..\\..\\' + os.path.relpath(repo_path) + '\\' + keys + '.nff'
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
            cfd_path = '..\\\\..\\\\..\\\\' + os.path.relpath(repo_path).replace('\\', '\\\\') \
                + '\\\\' + cfdRegex.search(new_ICFDContent).group(2) 
            new_ICFDContent = new_ICFDContent.replace(cfdRegex.search(new_ICFDContent).group(2), cfd_path)
            new_ICFDContent = sampRegex.sub('\\1 ' + samp, new_ICFDContent)
            new_ICFDContent = thldRegex.sub('\\1 ' + thld, new_ICFDContent)
            new_ICFDContent = turbRegex.sub('\\1 ' + turb, new_ICFDContent)
            ICFDFile = open(baseDir + '\\' + keys + '_ICFD.edat', 'w')
            ICFDFile.write(new_ICFDContent)
            ICFDFile.close()


            # Another idea using replace; the problem is that only looks to match group(2), not the whole regex
            #new_ICFDContent = new_ICFDContent.replace(sampRegex.search(new_ICFDContent).group(2), samp)
            #new_ICFDContent = new_ICFDContent.replace(thldRegex.search(new_ICFDContent).group(2), thld)
            #new_ICFDContent = new_ICFDContent.replace(turbRegex.search(new_ICFDContent).group(2), turb)

def local_launcher(analysis):
    '''Walk over each case filetree and launch the ICFD cases, then the actran analysis.'''
   

    actranpy_path = os.environ['ACTRAN_PATH'] + '\\Actran_19.1\\bin\\actranpy.bat'
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
                edat_file = keys + '.edat'
                inputfile = "--inputfile=" + edat_file
                subprocess.call([actranpy_path, inputfile, "--report=report_Actran"]) 

            os.chdir(start_dir)


def post_pro():
    '''Copy default session files from automation repository to case directory. Make the
    necessary edits and run, have all images output to 'figures' directory.'''
    
    for keys in baseCaseName.keys():
        for baseDir, subDir, files in os.walk('.\\' + keys):
            if files == [] and baseDir != '.\\' + keys:   # In the parameter subdirectory
                try:
                    os.mkdir('.\\' + baseDir + '\\PostPro')
                    shutil.copy(args.path + '\\' + keys + '_Joe.sess', '.\\' + baseDir + '\\PostPro')
                    #shutil.copy(args.path + '\\' + keys + '.sess', '.\\' + baseDir + '\\PostPro')
                except:
                    print('That directory already exists!')
            if subDir == []:        # Lowest level
                plt_file = [x for x in files if '.plt' in x]
                plt_file = plt_file[0]
                shutil.copy(os.path.abspath(baseDir) + '\\' + plt_file, baseDir + '\..\PostPro')
                shutil.move(baseDir + '\..\PostPro' + '\\' + plt_file, baseDir + '\..\PostPro\\' + os.path.basename(baseDir) + '.plt')


        # Launch Session Script for post-processing
        actran_sess = os.environ['ACTRAN_PATH'] + '\\Actran_19.1\\bin\\actranvi.bat'
        start_dir = os.getcwd()
        inputfile = keys + '_Joe.sess'
        os.chdir(keys + '\\filt\\PostPro') # TODO: Fix this line
        #subprocess.call([actran_sess, "-x" + inputfile, "--no_graphics"]) 
        subprocess.call([actran_sess, "-x" + inputfile]) 

main()
