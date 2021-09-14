# Prisma SDWAN Configure LQM Extensions 
This utility is used to configure LQM Thresholds for media, a single app or all applications.

#### Synopsis
This script can be used to configure LQM thresholds for applications. It accepts threshold values either via CLI or in the form of a CSV file for multiple site configurations.

Users can use the *lqmtype* attribute to determine the type of LQM extension.

**media**: Configure the given threshold for all VPN paths at the given site & element
**app**: Configure thresholds for the application specified at the given site & element
**all_apps**: Configure thresholds for all applications at the given site & element

For bulk configurations, a CSV file with site & device specific thresholds can be provided. The CSV file should have the following headers:

**media**: site,latency,jitter,packetloss

**app**: site,element,app,latency,jitter,packetloss

**all_apps**: site,element,latency,jitter,packetloss

#### Requirements
* Active Prisma SDWAN Account
* Python >=3.6
* Python modules:
    * Prisma SDWAN (CloudGenix) Python SDK >= 5.5.3b1 - <https://github.com/CloudGenix/sdk-python>

#### License
MIT

#### Installation:
 - **Github:** Download files to a local directory, manually run `configlqmthresholds.py`. 

### Examples of usage:
Create LQM Threshold for media app for all VPN at the given site
```
./configlqmthresholds.py -SN sitename -LT media -L latency -J jitter -PL packetloss
```

Create LQM Threshold for a single app
```
./configlqmthresholds.py -SN sitename -EN elementname -AN appname -LT app -L latency -J jitter -PL packetloss
```

Create LQM Threshold for ALL apps
```
./configlqmthresholds.py -SN sitename -EN elementname -LT all_apps -L latency -J jitter -PL packetloss
```

Create LQM Threshold for media app for all VPN at the given site using a CSV file
```
./configlqmthresholds.py -LT media -F csvfile
```

Create LQM Threshold for a single app using a CSV file
```
./configlqmthresholds.py -LT app -F csvfile
```

Create LQM Threshold for ALL apps using a CSV file
```
./configlqmthresholds.py -LT all_apps -F csvfile
```


#### Help Text:
```angular2
TanushreeKamath:configlqmthresholds tkamath$ ./configlqmthresholds.py -h
usage: configlqmthresholds.py [-h] [--controller CONTROLLER] [--email EMAIL] [--pass PASS] [--sitename SITENAME] [--elemname ELEMNAME] [--lqmtype LQMTYPE] [--appname APPNAME] [--latency LATENCY] [--jitter JITTER] [--packetloss PACKETLOSS]
                              [--filename FILENAME]

CloudGenix: Config SSH.

optional arguments:
  -h, --help            show this help message and exit

API:
  These options change how this program connects to the API.

  --controller CONTROLLER, -C CONTROLLER
                        Controller URI, ex. C-Prod: https://api.elcapitan.cloudgenix.com

Login:
  These options allow skipping of interactive login

  --email EMAIL, -E EMAIL
                        Use this email as User Name instead of prompting
  --pass PASS, -P PASS  Use this Password instead of prompting

LQM Config Specific information:
  Provide value for Latency, Jitter and Packet Loss

  --sitename SITENAME, -SN SITENAME
                        Name of the Site
  --elemname ELEMNAME, -EN ELEMNAME
                        Name of the Element
  --lqmtype LQMTYPE, -LT LQMTYPE
                        Type of LQM config. Allowed values: media, all_apps, app
  --appname APPNAME, -AN APPNAME
                        Name of the Element
  --latency LATENCY, -L LATENCY
                        Max value for latency
  --jitter JITTER, -J JITTER
                        Max value for jitter
  --packetloss PACKETLOSS, -PL PACKETLOSS
                        Max value for packetloss
  --filename FILENAME, -f FILENAME
                        CSV file containing configuration information. CSV header should match: site,element,app,latency,jitter,packetloss
TanushreeKamath:configlqmthresholds tkamath$ 
```

#### Version
| Version | Build | Changes |
| ------- | ----- | ------- |
| **1.0.0** | **b1** | Initial Release. |


#### For more info
 * Get help and additional Prisma SDWAN Documentation at <https://docs.paloaltonetworks.com/prisma/prisma-sd-wan.html>
