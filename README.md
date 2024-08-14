# Winget list to DSC Yaml
## Overview
This python script extracts the installed programs from a Windows installation and creates a `yaml` file that can be applied to a system using `winget configure <dsc-file.yaml>`

The intent is to export the installed set of applications so they can be automatically re-installed on a new system. 

Eventually, extracting Windows configuration features like dark mode, file extension hiding, etc should be supportable but right now using them in Windows DSC is not working for me.

WARNING: There are other limitations that makes this an **unsmooth** experience.

## Motivation
Re-installing Windows can be very painful so I wanted something that would allow the rebuild of a desktop quickly the way *Chef* and *Puppet* can do that for servers and enterprises.  Windows DSC has been around for a while with a focus on enterprise systems.  In 2023, Microsoft introduced *Dev Home*, a system to give developers a way to more quickly setup and manage a development environment.  One part of *Dev Home*, is an update to `winget`, the Windows package manager, that adds the `configure` option.  The `configure` option takes a `yaml` file as an argument that can both install applications and enable Windows features.

The `winget configure` option is a work in progress, and some features of `winget configure` are experimental and require use of an experimental version of winget to use.  Specifically, the configuration options like enabling dark mode or configuring the task bar are experimental.  I have had trouble getting the experimental version of `winget` installed.

## Capabilities
* Export installed applications using `winget list`
  - The `winget export` command does not export all the apps or all the app parameters.  
  - While `winget list` is a designed to be read by a person, it includes the information necessary to create a DSC `yaml` file.
  - Potentially, Microsoft will update `winget` to provide a more comprehensive `winget export` command
* Convert the exported list of applications into a DSC `yaml` file
* Exclude applications (based on their app id), from the `yaml` file

## Running the script
1. Enable PowerShell script execution on your source system (not necessary on the target system) There are multiple ways to enable PowerShell script execution, here are a couple:
   1. Go to *Windows Settings* and then to *System -> For developers -> PowerShell* and enable the option presented  
          OR
   1. Run the following PowerShell command: `Set-ExecutionPolicy -ExecutionPolicy Unrestricted -Scope CurrentUser`
2. Make sure you have the latest version of Python 3.x installed on your host
   1. Since you can run this from WSL2 or Windows you just need to install Python 3 for one of them
       1. On Windows install Python like this: `winget install Python`
       2. On WSL2 run `sudo apt install ptyhon3`
3. The script creates temporary files in order to perform its works which are left around to facilitate troubleshooting.   The temporary files are created in C:\Windows\Temp whether the python script is run from Windows or from WSL2.  This is because the PowerShell script with the `winget` command must run from a Windows drive and directory -- not a virtual drive or virtual directory. 
4. Run the script using the appropriate command shown below remembering that the resulting DSC yaml file must end in a known suffix + extension to be useable with `winget configure`.  Windows supports a couple of combinations but `.dsc.yaml` works fine.
   - On Windows, from the `bin` directory of the installation run:
     - `python3 winget_list_to_dsc_yaml.py -o <my-output-directory>\<basefilename>.dsc.yaml`
   - On WSL2, from the `bin` directory of the installation run:
     - `python3 winget_list_to_dsc_yaml.py -o <my-output-directory>/<basefilename>.dsc.yaml`
    
5. Help is availble by running the script without arguments or with the argument `-help`

## Applying the the `DSC yaml` file
_**WARNING: Applying the generated DSC yaml file will result in that host getting all the software listed in the `yaml` file installed (unless already installed).   This can be a dramatic change to any host and you should be certain you want to do this.  I use a Hyper-V Windows VM to test the resulting `yaml` file.**_

From Windows use the PowerShell script `bin\apply-dsc-yaml.ps1`.
From WSL2, use the bash script `bin\apply-dsc-yaml.bash`.

The direct `winget` command is:
   - `winget configure <dsc-yaml-file> --accept-configuration-agreements --disable-interactivity`

From Windows _Dev Home_, go to left menu bar and select _Machine Configuration_, the select _Configuration file_.  This wil result in a file _Open_ dialog where you can select the `yaml` file.

## Notes & Limitations
 1. The `winget` extraction and processing is designed to work within a Windows environment with Python 3 installed or within a Windows WSL2 environment. 
 1. Google Chrome is currently in the default `cfg\exclude.cfg` file because `winget` running the Chrome installer results in Chrome launching and in `winget configure` returning an error.  The error is not fatal but *is* very confusing.   I am trying to learn how to better control the Google installer -- if that is possible.  It may not be possible as Google locks up some of the better configuration features within their paid enterprise tier.
 1. Windows configuration features like enabling dark mode require use of an experimental winget that is hard to get installed.  These features may not work anyway according to some forum posts
 1. There seem to be some dependencies on using the new version of PowerShell, PowerShell 7, but that is not completely clear.  My testing seems to work without it but some PowerShell commands to interrogate the system are only in PowerShell 7
 1. Visual Studio Code (VS Code) is explicity supported by `winget configure` but I have not tried to use this feature yet
 1. How Windows DSC for Dev Home relates to the enterprise Windows DSC that has been available for years is not clear to me and isn't clear on any of the documentation I have read.  There is a huge overlap but Windows DSC for enterprise seems to be focused on PowerShell driven solutions that use JSON configuration files.
 1. Note that you can find out which resources are DSC controllable using the below PowerShell command, but the information will be a bit cryptic.
    - `Find-DscResource -Module Microsoft.Windows.Developer -Repository PSGallery -AllowPrerelease`



