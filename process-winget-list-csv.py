#!/bin/env python3
#import pdb; pdb.set_trace()
import argparse
from argparse import ArgumentParser
import csv
from datetime import datetime
import operator
import os
import platform
import typing
import subprocess
import sys

class AppInfo:
    """All the app info from a winget list output line"""
    def __init__(self, name, appId, version, availableVersion, source ):
        self.name = name
        self.appId = appId
        self.version = version
        self.availableVersion = availableVersion
        self.source = source

    def __repr__(self):
        return f"name:{self.name},appId:{self.appId},version:{self.version},"+\
            "availableVersion:{self.availableVersion},source:{self.source}"

    def __str__(self):
        return f"{self.name},{self.appId},{self.version},{self.availableVersion},{self.source}"
    

CONFIGURATION_VERSION="0.2.0"

SYSTEM_NAME_WINDOWS='Windows'
SYSTEM_NAME_LINUX='Linux'
WINDOWS_WSL_TAG='WSL2'
WINGET_LIST_FILE_SFX='winget_list.txt'
WINGET_LIST_POWERSHELL_SCRIPT_SFX='winget_list.ps1'


NAME_COL=0
ID_COL=1
VERSION_COL=2
AVAILABLE_COL=3
SOURCE_COL=4
WINGET_LIST_POWERSHELL_SCRIPT='# powershell' + os.linesep +\
    '$Width = $host.UI.RawUI.MaxPhysicalWindowSize.Width'+ os.linesep +\
    '$host.UI.RawUI.BufferSize = New-Object System.Management.Automation.Host.size($Width,2000)'+ os.linesep +\
    'winget list' + os.linesep 


node_name=platform.node().lower()
system=platform.system()
release=platform.release()
dt=datetime.now()
default_basename=node_name + '_apps_' + dt.strftime('%Y%m%d-%H%M%S')
default_output_file='.' + os.sep + default_basename + '_DSC.yaml'
pid=os.getpid()

if (system == SYSTEM_NAME_LINUX ):
    default_intermediate_file_dir='/mnt/c/Windows/Temp/'+str(pid)
elif (system == SYSTEM_NAME_WINDOWS ):
    default_intermediate_file_dir='C:\Windows\Temp\\'+str(pid)
else:
    print( 'This script does not support',system,'. Exiting.', file=sys.stderr )
    os.exit(-1)


    
arg_parser: ArgumentParser = ArgumentParser( # includes an unnecessary type hint
    prog=sys.argv[0],
    description='Extract installed apps using Windows winget list and then convert it to a '+
                'Windows DSC yaml installation file',
    epilog='-')

arg_parser.add_argument( '-b', '--basename', 
                         help='The base name of the generated files output files in yaml format',
                         default=default_basename )
arg_parser.add_argument( '--overwrite',
                         action=argparse.BooleanOptionalAction,
                         help='Overwite intermediate files and output file.  Default is --no-overwrite' )
arg_parser.set_defaults(overwrite=-False) # set the default for the BooleanOptionalAction add_argument above
arg_parser.add_argument( '-o', '--output-file',
                         help='The name and path (optional) of the Windows DSC yaml file to be generated.',
                         metavar='<output-file>',
                         default=default_output_file )
arg_parser.add_argument( '--intermediate-file-dir',
                         help='The directory where the intermediate files will be saved.'+
                         'This must be a Windows directory permitted to run Powershell scripts',
                         metavar='<intermediate-dir>',
                         default=default_intermediate_file_dir )
arg_parser.add_argument( '--use-winget-list-file',
                         help='Do not run winget list, use this txt file of winget list output instead',
                         metavar='<winget-list-txt-file>' )


args = arg_parser.parse_args()

intermediate_file_dir=getattr(args, 'intermediate_file_dir')
output_file=getattr(args, 'output_file' )
overwrite=getattr(args, 'overwrite')
basename=getattr(args, 'basename')
use_winget_list_file=getattr(args, 'use_winget_list_file')
winget_list_powershell_script=basename + '_' + WINGET_LIST_POWERSHELL_SCRIPT_SFX
winget_list_powershell_script_path=os.path.join( intermediate_file_dir,
                                                 winget_list_powershell_script)
winget_list_output_file=os.path.join( intermediate_file_dir,
                                      basename + '_' +
                                      WINGET_LIST_FILE_SFX )

print('winget_list_powershell_script:', winget_list_powershell_script )
print('winget_list_output_file',winget_list_output_file )

print(args)


# run winget command

if (not os.path.exists(intermediate_file_dir)):
    os.mkdir(intermediate_file_dir)

if (os.path.exists(intermediate_file_dir)):
    print('Directory',intermediate_file_dir,'exists')
else:
    print('Directory',intermediate_file_dir,'does not exist')


# create powershell script
# remember newline has to be Windows because whether in Windows or WSL, the winget runs in Windows
# and therefore the powershell script runs in Windows
with open(winget_list_powershell_script_path, encoding='utf-8', newline='\r\n', mode='w+') as f:
    f.write(WINGET_LIST_POWERSHELL_SCRIPT);

print( 'Created script',winget_list_powershell_script,'\n')
    


if (system == SYSTEM_NAME_LINUX):
    if (not release.endswith(WINDOWS_WSL_TAG)):
        print( 'Expected to be running on WSL2 (Linux for Windows) in order to run winget.\n', file=sys.stderr)
        print( 'Found platform.release() that does not end in WSL2:', "'"+release+"'" )
        sys.exit(-1)
        
    with open(winget_list_output_file, encoding='utf-8', newline=os.linesep, mode='wt') as f:
        os.chdir(intermediate_file_dir)
        completed_process = subprocess.run(['cmd.exe', '/c', 'pwsh.exe', '-File',
                                            winget_list_powershell_script],
                                           stdout=f, capture_output=False, encoding='utf-8', check=True)
        print('Process completed, output in,',winget_list_output_file)
elif (system == SYSTEM_NAME_WINDOWS):
    with open(winget_list_output_file, encoding='utf-8', newline=os.linesep, mode='wt') as f:
        os.chdir(intermediate_file_dir)
        completed_process = subprocess.run([winget_list_powershell_script],
                                           stdout=f, capture_output=False, encoding='utf-8', check=True)
        print('Process completed, output in,',winget_list_output_file)
else:
    print( 'This script does not support',system,'. Exiting.', file=sys.stderr )
    os.exit(-1)


print('before file read')
found_winget_starting_line=False

appCount=0
with open(winget_list_output_file, encoding='utf-8', newline='\r\n', mode='rt') as winget_file:
    appList = []
    while True:
        line=winget_file.readline()
        if (not line): break
        if (found_winget_starting_line):
            appName=line[0:42].rstrip()
            appId=line[42:85].rstrip()
            appVersion=line[85:102].rstrip()
            appAvailableVersion=line[102:112].rstrip()
            appSource=line[112:len(line)-1].rstrip()
            appList.append( AppInfo(appName, appId, appVersion, appAvailableVersion, appSource))
            appCount += 1
        else:
            if (line.startswith('-----')):
                found_winget_starting_line=True

print("\nprocessed winget list output file\n\n" )
        
for appInfo in appList:
    print(appInfo)
sys.exit(0)
            


readlineprint("# yaml-language-server: $schema=https://aka.ms/configuration" +
      "-dsc-schema/0.2");
print("properties:")

#gawk -v FIELDWIDTHS="1 10 4 2 2" -v OFS=, '{print $1,$2,$3,$4,$5}' file





with open('/mnt/c/Users/petra/installed-packages02.csv',encoding='utf-8',newline='\r\n', mode='rt') as csvfile:
    csvReader = csv.reader(csvfile, delimiter=',', quotechar='|')
#    print("----csvReader type",type(csvReader));
    sortedInstalled = sorted(csvReader, key=operator.itemgetter(ID_COL) )
    for row in sortedInstalled:
#        print('row length is:', len(row))
#       print(row)
#        if(len(row)>4): print("col0:",row[0],"col4:",row[4])
#        if(len(row)>5): print("col0:",row[0],"col5:",row[5])
#        print(row)
#        print('\n')
        if ( len(row) >SOURCE_COL and
            (row[SOURCE_COL] == 'winget' or row[SOURCE_COL] == 'msstore' )):
            print('    - resource: Microsoft.WinGet.DSC/WinGetPackage' )
            print('      id:',row[ID_COL])
            print('        directives:')
            print('          description: Install', row[NAME_COL] )
            print('          allowPrerelease: true')
            print('      settings:')
            print('        id:',row[ID_COL])
            print('        source: ',row[SOURCE_COL] )
            
#        print( row[1],row[2],row[3],row[4] )
#        print( type(row),':  ',row )
#        print(', '.row['Column1'],'\t',row['Column2'],'\t',row['Column3'] )

print("  configurationVersion:",CONFIGURATION_VERSION);

