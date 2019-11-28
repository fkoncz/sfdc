import requests
import sys
import os
import shutil
import base64
import zipfile
import time
import datetime
import xml.dom.minidom
from xml.dom.minidom import parse
from xml.dom import minidom

# Some globals could be in a settings file
loginURL = 'https://login.salesforce.com/services/Soap/c/35.0'
metadataURL = 'https://na24.salesforce.com/services/Soap/m/35.0'

## Valid values could be: FifteenMinutes, ThirtyMinutes, SixtyMinutes, TwoHours, FourHours, EightHours, TwelveHours
NewSessionTimeOut = 'ThirtyMinutes'
NewLockoutInterval = 'SixtyMinutes'

## Check for python version - we need 3
req_version = (3,4)
cur_version = sys.version_info

if cur_version >= req_version:
    print("\n\nPython version min. 3.4 requirement: PASS\n\n")
else:
    print("\n\nPlease use Python v3 or run using python3\n\n")
    exit()

# just for the cleanup at the end
os.makedirs('./temp', exist_ok=True)

## Don't want to log in again and again and again so this part is for re-using SID from one login so uncomment for debugging and comment out the login part where mentioned.
## filename = "sid.txt"
## mysid = []
## with open(filename) as f:
##     for line in f:
##         mysid.append([str(n) for n in line.strip().split('^^^')])
## for pair in mysid:
##     try:
##         crap,sid = pair[0],pair[1]
##         print(y)
##     except IndexError:
##         print("A line in the file doesn't have enough entries.")


loginHeaders = {
    'content-type': 'text/xml',
    'charset': 'UTF-8',
    'SOAPAction': 'login'
}
loginBody = """
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:urn="urn:enterprise.soap.sforce.com">
   <soapenv:Header>
   </soapenv:Header>
   <soapenv:Body>
      <urn:login>
         <urn:username>xyz@yahoo.ca</urn:username>
         <urn:password>po09PO)(hO1eSc4L3tIKL</urn:password>
      </urn:login>
   </soapenv:Body>
</soapenv:Envelope>
"""
loginresult = requests.post(loginURL, loginBody, headers=loginHeaders)
f = open("./temp/login.xml", 'w')
f.write(loginresult.text)
f.close()
dom = parse("./temp/login.xml")
sidresult = dom.getElementsByTagName('sessionId')
## Comment out the line below if using the SID from a backup file.
sid = sidresult[0].firstChild.nodeValue

print("\nGot session ID.\n\n") # + sid for debugging, we could add checks if sid is successful, etc.

retrieveHeaders = {
    'content-type': 'text/xml',
    'charset': 'UTF-8',
    'SOAPAction': 'retrieve'
    }
getZipFile = """
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <soap:Header>
    <SessionHeader xmlns="http://soap.sforce.com/2006/04/metadata">
            <sessionId>""" + sid + """</sessionId>
            </SessionHeader>
  </soap:Header>
  <soap:Body>
    <retrieve xmlns="http://soap.sforce.com/2006/04/metadata">
      <retrieveRequest>
        <apiVersion>35.0</apiVersion>
        <unpackaged>
    <types>
        <members>Security</members>
        <name>Settings</name>
    </types>
    <version>35.0</version>
    </unpackaged>
      </retrieveRequest>
    </retrieve>
  </soap:Body>
</soap:Envelope>
"""

time.sleep(2)
retrieveStatusXML = requests.post(metadataURL, getZipFile, headers=retrieveHeaders)
f = open("./temp/getzipresult.xml", 'w')
f.write(retrieveStatusXML.text)
f.close()
from xml.dom.minidom import parse
dom = parse("./temp/getzipresult.xml")
retrStatusElement = dom.getElementsByTagName('id')
retrId = retrStatusElement[0].firstChild.nodeValue


checkRetrieveHeaders = {
    'content-type': 'text/xml',
    'charset': 'UTF-8',
    'SOAPAction': 'checkRetrieveStatus'
    }
checkRetrieve = """
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:met="http://soap.sforce.com/2006/04/metadata">
   <soapenv:Header>
      <met:SessionHeader>
            <sessionId>""" + sid + """</sessionId>
      </met:SessionHeader>
   </soapenv:Header>
   <soapenv:Body>
      <met:checkRetrieveStatus>
         <met:asyncProcessId>""" + retrId + """</met:asyncProcessId>
         <met:includeZip>true</met:includeZip>
      </met:checkRetrieveStatus>
   </soapenv:Body>
</soapenv:Envelope>
"""
time.sleep(2)
retrieveResult = requests.post(metadataURL, checkRetrieve, headers=checkRetrieveHeaders)
f = open("./temp/getzipfile.xml", 'w')
f.write(retrieveResult.text)
f.close()
xmldoc1 = xml.dom.minidom.parse("./temp/getzipfile.xml")
xmldata1 = xmldoc1.getElementsByTagName("zipFile")[0]
try:
    encFile = xmldata1.firstChild.nodeValue
    print ("\n\nGot ZipFile. ZipFile is in Base64 encoded, decoding.\n\n") # we can add a check if this was successful.
    fh = open("./temp/currentPackage.zip", "wb")
    Data = base64.b64decode(encFile)
    fh.write(Data)
    fh.close()
except:
    print("\n\n**** ERROR: Probably too frequent queries! Stopping, try again! \n")
    exit()

zip_ref = zipfile.ZipFile('./temp/currentPackage.zip', 'r')
zip_ref.extractall()
zip_ref.close()

def change_session_timeout():
    xmldoc2 = xml.dom.minidom.parse('./unpackaged//settings/Security.settings')
    xmldata2 = xmldoc2.getElementsByTagName("sessionTimeout")[0]
    xmldata2.firstChild.nodeValue = NewSessionTimeOut
    f = open('./unpackaged//settings/Security.settings', 'w')
    f.write(xmldoc2.toxml())
    f.close()
    print ("sessionTimeout updated to " + NewSessionTimeOut + " setting locally.")

def change_lockoutInterval():
    xmldoc = xml.dom.minidom.parse('./unpackaged//settings/Security.settings')
    xmldata = xmldoc.getElementsByTagName("lockoutInterval")[0]
    xmldata.firstChild.nodeValue = NewLockoutInterval
    f = open('./unpackaged//settings/Security.settings', 'w')
    f.write(xmldoc.toxml())
    f.close()
    print ("lockoutInterval updated to " + NewLockoutInterval + " setting locally.")

change_session_timeout()
change_lockoutInterval()

newzip = zipfile.ZipFile('./temp/updatedPackage.zip', "w")
for dirname, subdirs, files in os.walk("./unpackaged"):
    newzip.write(dirname)
for filename in files:
    newzip.write(os.path.join(dirname, filename))
    newzip.write("./unpackaged//package.xml")
    newzip.close()

with open("./temp/updatedPackage.zip", "rb") as f:
    bytes = f.read()
    encoded = base64.b64encode(bytes)
    converted = encoded.decode("utf-8")
print("\n\n Base64 new zip file created.\n\n") # We could print the Base64 data for debugging.

deployHeaders = {
        'content-type': 'text/xml',
        'charset': 'UTF-8',
        'SOAPAction': 'deploy'
    }
deployBody = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:met="http://soap.sforce.com/2006/04/metadata">
    <soapenv:Header>
      <met:SessionHeader>
            <sessionId> """ + sid + """</sessionId>
      </met:SessionHeader>
   </soapenv:Header>
   <soapenv:Body>
    <deploy xmlns="http://soap.sforce.com/2006/04/metadata">
      <ZipFile> """ + converted + """</ZipFile>
      <DeployOptions>
        <allowMissingFiles>false</allowMissingFiles>
        <autoUpdatePackage>true</autoUpdatePackage>
        <checkOnly>false</checkOnly>
        <ignoreWarnings>false</ignoreWarnings>
        <performRetrieve>false</performRetrieve>
        <rollbackOnError>true</rollbackOnError>
        <runAllTests>false</runAllTests>
        <singlePackage>false</singlePackage>
      </DeployOptions>
    </deploy>
   </soapenv:Body>
    </soapenv:Envelope>"""


time.sleep(2)
deployIt = requests.post(metadataURL, deployBody, headers=deployHeaders)
f = open("./temp/deploystatus.xml", 'w')
f.write(deployIt.text)
f.close()
DeployXML = parse("./temp/deploystatus.xml")
result = DeployXML.getElementsByTagName('id')
did = result[0].firstChild.nodeValue

CheckDeployHeaders = {
        'content-type': 'text/xml',
        'charset': 'UTF-8',
        'SOAPAction': 'checkDeployStatus'
    }
CheckDeployStatus = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:met="http://soap.sforce.com/2006/04/metadata">
   <soapenv:Header>
      <met:SessionHeader>
            <sessionId> """ + sid + """</sessionId>
      </met:SessionHeader>
   </soapenv:Header>
   <soapenv:Body>
      <met:checkDeployStatus>
         <met:asyncProcessId>""" + did + """</met:asyncProcessId>
         <met:includeDetails>true</met:includeDetails>
      </met:checkDeployStatus>
   </soapenv:Body>
</soapenv:Envelope>"""

time.sleep(2)
checkDeployment = requests.post(metadataURL, CheckDeployStatus, headers=CheckDeployHeaders)
f = open("./deployresult.xml", 'w')
f.write(checkDeployment.text)
f.close()
DResult = parse("./deployresult.xml")
result = DResult.getElementsByTagName('status')
goodornot = result[0].firstChild.nodeValue
print("\n\nDeployment result: " + goodornot)
if goodornot == 'Succeeded':
    time.sleep (2)
    print ("\n\n**** Update successful.\n\n")
    os.remove("./deployresult.xml")
else:
    print("\n\***ERROR: See deployresult.xml for details. Printing error to stdout in 5 seconds;\n\n")
    time.sleep(5)
    print(checkDeployment.text)
    print("\n")
    exit()


#Cleanup a bit.
time.sleep(2)
ts = time.time()
st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
logtext = """
.
Action logged. Details:
Session ID: """ + sid + """

TimeStamp: """ + st + """
.
"""
f = open("./log.txt", "a")
f.write(logtext)
f.close()
shutil.rmtree('./unpackaged')
shutil.rmtree('./temp')

