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

DEBUG=False

logfile = None
def get_timestamped_msg( *args ) -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "  " + \
        " ".join([str(i) for i in args])

def log( *args, to_stderr=False ):
    msg = get_timestamped_msg(*args)
    if (not logfile ):
        print( msg, file=sys.stderr )
    else:        
        print( msg, file=logfile )        
        if (to_stderr):
            print( msg, file=sys.stderr ) 

            
def slices(s, *args):
    """Slice a string into a list of fixed-width fields
    eg:
    code:    list(slices('abdefgh', 1,2,3)) 
    returns: ['a', 'bc', 'def']

    or
    
    code:
    msg='abcdefgh'
    fieldWidths(1,2,3)
    list(slices(msg,*fieldWidths))
    """
    position = 0
    for length in args:
        yield s[position:position + length]
        position += length


def run_winget_list():
     #
     # create powershell script that runs winget
     #
     # remember newline has to be Windows because whether in Windows or WSL,
     # the winget runs in Windows and therefore the powershell script runs in Windows
     #
     with open(winget_list_powershell_script_path, encoding='utf-8', newline='\r\n', mode='w+') as f:
         f.write(WINGET_LIST_POWERSHELL_SCRIPT);

     log( 'Created powershell "winget list" script:',winget_list_powershell_script)


     #
     # run the powershell script with winget list
     #
     if (system == SYSTEM_NAME_LINUX):
         if (not release.endswith(WINDOWS_WSL_TAG)):
             log( 'Expected to be running on WSL2 (Linux for Windows) in order to run winget.\n', to_stderr=True)
             log( 'Found platform.release() that does not end in WSL2:', "'"+release+"'", to_stderr=True )
             sys.exit(-1)

         with open(winget_list_output_file, encoding='utf-8', newline=os.linesep, mode='wt') as f:
             os.chdir(intermediate_file_dir)
             completed_process = subprocess.run(['cmd.exe', '/c', 'pwsh.exe', '-File',
                                                 winget_list_powershell_script],
                                                stdout=f, capture_output=False, encoding='utf-8', check=True)
             log('"winget list" script completed, output in,',winget_list_output_file)
     elif (system == SYSTEM_NAME_WINDOWS):
         with open(winget_list_output_file, encoding='utf-8', newline=os.linesep, mode='wt') as f:
             os.chdir(intermediate_file_dir)
             completed_process = subprocess.run([winget_list_powershell_script],
                                                stdout=f, capture_output=False, encoding='utf-8', check=True)
             log('"winget list" script completed, output in,',winget_list_output_file)
     else:
         log( 'This script does not support',system,'. Exiting.', to_stderr=True )
         os.exit(-1)

        
class AppInfo:
    """All the app info from a winget list output line"""
    def __init__(self, appId, name, version, availableVersion, source ):
        self.appId = appId
        self.name = name
        self.version = version
        self.availableVersion = availableVersion
        self.source = source

    def __repr__(self):
        return f"appId:{self.appId},name:{self.name},version:{self.version},"+\
            "availableVersion:{self.availableVersion},source:{self.source}"

    def __str__(self):
        return f"{self.appId},{self.name},{self.version},{self.availableVersion},{self.source}"
    
script_dir=sys.path[0]
app_dir=os.path.realpath(script_dir + "/.." )

CONFIGURATION_VERSION="0.2.0"

SYSTEM_NAME_WINDOWS='Windows'
WINDOWS_LINESEP='\r\n'
SYSTEM_NAME_LINUX='Linux'
LINUX_LINESEP='\n'
WINDOWS_WSL_TAG='WSL2'
WINGET_LIST_FILE_SFX='winget_list.txt'
WINGET_LIST_POWERSHELL_SCRIPT_SFX='winget_list.ps1'
TEMP_DIR_PREFIX='winget_to_dsc.'


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
default_exclude_apps_cfg_path=os.path.join( app_dir, 'cfg', 'exclude.cfg' )
pid=os.getpid()

if (system == SYSTEM_NAME_LINUX ):
    default_intermediate_file_dir='/mnt/c/Windows/Temp/'+TEMP_DIR_PREFIX+str(pid)
elif (system == SYSTEM_NAME_WINDOWS ):
    default_intermediate_file_dir='C:\Windows\Temp\\'+TEMP_DIR_PREFIX+str(pid)
else:
    print( 'This script does not support',system,'. Exiting.', file=sys.stderr )
    os.exit(-1)

log("'" + sys.argv[0] + "'" + ' started.')
#
# setup arg parser
#
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
arg_parser.add_argument( '--exclude-apps-cfg-path',
                         help='Path to the list of apps (as app ids) to exclude when' +
                         'generating the DSC.',
                         metavar='<exclude-apps-cfg-path>',
                         default=default_exclude_apps_cfg_path )
arg_parser.add_argument( '--use-winget-list-file',
                         help='Do not run winget list, use this txt file of winget list output instead',
                         metavar='<winget-list-txt-file>' )

#
# parse command line args
#
args = arg_parser.parse_args()
log('Received args:', args )
#
# extract command line args
#
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
exclude_apps_cfg_path=getattr(args,'exclude_apps_cfg_path')
if (len(exclude_apps_cfg_path)==0 or
    exclude_apps_cfg_path.lower() == 'none'):
    exclude_apps_cfg_path = None

log( 'Extracted startup argument, intermediate_file_dir:', intermediate_file_dir )
log( 'Extracted startup argument, output_file:', output_file )
log( 'Extracted startup argument, overwrite:', overwrite )
log( 'Extracted startup argument, basename:', basename )
log( 'Extracted startup argument, use_winget_list_file:', use_winget_list_file  )
log( 'Extracted startup argument, winget_list_powershell_script:', winget_list_powershell_script )
log( 'Extracted startup argument, winget_list_powershell_script_path:', winget_list_powershell_script_path )
log( 'Extracted startup argument, exclude_apps_cfg_path:',  exclude_apps_cfg_path )


    
    
if (overwrite==False and os.path.exists(output_file)):
    log("Flag overwrite is false and output_file,",
        output_file,"exists.  Exiting...", to_stderr=True)
    sys.exit(-1)
    
#
# Load exclude file
#
log('Loading excluded app ids file from',exclude_apps_cfg_path )
excluded_apps_ids=set([])
if (exclude_apps_cfg_path):
    with open( exclude_apps_cfg_path, encoding='utf-8', newline=os.linesep, mode='rt' ) as f:
        lines = []
        while True:
            line=f.readline()
            if (not line): break
            lines.append(line.strip())
        excluded_app_ids=sorted(set(lines))
        log( 'excluded_app_ids:', excluded_app_ids )



#
# create intermediate file directory
#
log('Will create intermediate file directory:',)
if (not os.path.exists(intermediate_file_dir)):
    os.mkdir(intermediate_file_dir)

# check temp directory
if (os.path.exists(intermediate_file_dir)):
    log('Intermediate file directory',intermediate_file_dir,'okay')
else:
    log('Intermediate file directory',intermediate_file_dir,'not found. Exiting')
    sys.exit(-1)

if (use_winget_list_file == None):
    run_winget_list()
    


found_winget_starting_line=False
with open(winget_list_output_file, encoding='utf-8', newline='\r\n', mode='rt') as winget_file:
    appList = []
    while True:
        line=winget_file.readline()
        if (not line): break
        if (found_winget_starting_line):
            appName=line[0:41].strip()
            appId=line[42:83].strip()
            appVersion=line[84:100].strip()
            appAvailableVersion=line[101:111].strip()
            appSource=line[112:len(line)-1].strip()
            appList.append( AppInfo(appId=appId,
                                    name=appName,
                                    version=appVersion,
                                    availableVersion=appAvailableVersion,
                                    source=appSource ))
        else:
            if (line.startswith('-----')):
                found_winget_starting_line=True




appList.sort( key=lambda x: x.appId )    

if (DEBUG):
    log( 'Extracted and sorted appInfo from winget list')
    for appInfo in appList:
        print(appInfo)


appList = [x for x in appList if x.appId not in excluded_app_ids ]
log( 'Excluded app ids removed from app list')
if (DEBUG):
    log( 'App list with excluded app ids removed' )
    for appInfo in appList:
        print(appInfo)

#
# write DSC yaml file.
# Windows newlines required
#
log('Will create DSC yaml file:', output_file )
with open(output_file, encoding='utf-8', newline=WINDOWS_LINESEP, mode='+w') as dsc_yaml:
    print("# yaml-language-server: $schema=https://aka.ms/configuration-dsc-schema/0.2",
          file=dsc_yaml )
    print("properties:",
          file=dsc_yaml)
    print("  configurationVersion:",CONFIGURATION_VERSION,
          file=dsc_yaml);
    print("  resources:",
          file=dsc_yaml);
    for app in appList:
        if (app.source == 'winget' or app.source=='msstore'):
            print('    - resource: Microsoft.WinGet.DSC/WinGetPackage',
                  file=dsc_yaml)
            print('      id:',app.appId,
                  file=dsc_yaml )
            print('      directives:',
                  file=dsc_yaml )
            print('        description: Install', app.name,
                  file=dsc_yaml)
            print('        allowPrerelease: true',
                  file=dsc_yaml)
            print('      settings:',
                  file=dsc_yaml)
            print('        id:', app.appId,
                  file=dsc_yaml)
            print('        source: ',app.source,
                  file=dsc_yaml )

log('Ouput file', output_file, 'write complete.')

sys.exit(0)
