# PowerShell for Windows
param (
    [Parameter(Mandatory, Position=0)]
    [string]$dsc_yaml_file
)
		      	 
winget configure $dsc_yaml_file --accept-configuration-agreements --disable-interactivity
