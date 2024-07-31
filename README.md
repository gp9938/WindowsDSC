# WindowsDSC
To apply a DSC file run winget configure <my-dsc-yaml-file>.yaml --accept-configuration-agreements

For the OS DSC note that you can find out which resources are controllable using PowerShell command:
 Find-DscResource -Module Microsoft.Windows.Developer -Repository PSGallery -AllowPrerelease
 
