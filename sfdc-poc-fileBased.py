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

# Some globals could be in a settings file
login_url = 'https://login.salesforce.com/services/Soap/c/35.0'
metadata_url = 'https://na24.salesforce.com/services/Soap/m/35.0'

# Valid values could be: FifteenMinutes, ThirtyMinutes, SixtyMinutes, TwoHours, FourHours, EightHours, TwelveHours
new_session_timeout = 'ThirtyMinutes'
new_lockout_interval = 'SixtyMinutes'

# Check for python version - we need 3.4
req_version = (3,4)
cur_version = sys.version_info

if cur_version >= req_version:
    print("\n\nPython version min. 3.4 requirement: PASS\n\n")
else:
    print("\n\nPlease use Python v3 or run using python3\n\n")
    exit()

# just for the cleanup at the end
os.makedirs('./temp', exist_ok=True)

# Don't want to log in again and again and again so this part is for re-using SID from one login so uncomment for debugging and comment out the login part where mentioned.
# filename = "sid.txt"
# mysid = []
# with open(filename) as f:
#     for line in f:
#         mysid.append([str(n) for n in line.strip().split('^^^')])
# for pair in mysid:
#     try:
#         crap, sid = pair[0], pair[1]
#         print(crap, sid)
#     except IndexError:
#         print("A line in the file doesn't have enough entries.")


login_headers = {
    'content-type': 'text/xml',
    'charset': 'UTF-8',
    'SOAPAction': 'login'
}
login_body = """
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
login_result = requests.post(login_url, login_body, headers=login_headers)
f = open("./temp/login.xml", 'w')
f.write(login_result.text)
f.close()
dom = parse("./temp/login.xml")
sid_result = dom.getElementsByTagName('sessionId')

# Comment out the line below if using the SID from a backup file.
sid = sid_result[0].firstChild.nodeValue

# + sid for debugging, we could add checks if sid is successful, etc.
print("\nGot session ID.\n\n")

retrieve_headers = {
    'content-type': 'text/xml',
    'charset': 'UTF-8',
    'SOAPAction': 'retrieve'
    }
get_zipfile = """
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
retrieve_status_xml = requests.post(metadata_url, get_zipfile, headers=retrieve_headers)
f = open("./temp/getzipresult.xml", 'w')
f.write(retrieve_status_xml.text)
f.close()
dom = parse("./temp/getzipresult.xml")
retr_status_element = dom.getElementsByTagName('id')
retr_id = retr_status_element[0].firstChild.nodeValue


check_retrieve_headers = {
    'content-type': 'text/xml',
    'charset': 'UTF-8',
    'SOAPAction': 'checkRetrieveStatus'
    }
check_retrieve = """
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:met="http://soap.sforce.com/2006/04/metadata">
   <soapenv:Header>
      <met:SessionHeader>
            <sessionId>""" + sid + """</sessionId>
      </met:SessionHeader>
   </soapenv:Header>
   <soapenv:Body>
      <met:checkRetrieveStatus>
         <met:asyncProcessId>""" + retr_id + """</met:asyncProcessId>
         <met:includeZip>true</met:includeZip>
      </met:checkRetrieveStatus>
   </soapenv:Body>
</soapenv:Envelope>
"""
time.sleep(2)
retrieve_result = requests.post(metadata_url, check_retrieve, headers=check_retrieve_headers)
f = open("./temp/getzipfile.xml", 'w')
f.write(retrieve_result.text)
f.close()
xmldoc1 = xml.dom.minidom.parse("./temp/getzipfile.xml")
xmldata1 = xmldoc1.getElementsByTagName("zipFile")[0]
try:
    encFile = xmldata1.firstChild.nodeValue
    print("\n\nGot ZipFile. ZipFile is in Base64 encoded, decoding.\n\n")
    fh = open("./temp/currentPackage.zip", "wb")
    Data = base64.b64decode(encFile)
    fh.write(Data)
    fh.close()
except Exception as e:
    print("\n\n**** ERROR: Probably too frequent queries! Stopping, try again! \n")
    print("Exception was: {}".format(e))
    exit()

zip_ref = zipfile.ZipFile('./temp/currentPackage.zip', 'r')
zip_ref.extractall()
zip_ref.close()


def change_session_timeout():
    xmldoc2 = xml.dom.minidom.parse('./unpackaged//settings/Security.settings')
    xmldata2 = xmldoc2.getElementsByTagName("sessionTimeout")[0]
    xmldata2.firstChild.nodeValue = new_session_timeout
    with_file = open('./unpackaged//settings/Security.settings', 'w')
    with_file.write(xmldoc2.toxml())
    with_file.close()
    return "sessionTimeout updated to " + new_session_timeout + " setting locally."


def change_lockout_interval():
    xmldoc = xml.dom.minidom.parse('./unpackaged//settings/Security.settings')
    xmldata = xmldoc.getElementsByTagName("lockoutInterval")[0]
    xmldata.firstChild.nodeValue = new_lockout_interval
    with_file = open('./unpackaged//settings/Security.settings', 'w')
    with_file.write(xmldoc.toxml())
    with_file.close()
    return "lockoutInterval updated to " + new_lockout_interval + " setting locally."


change_session_timeout()
change_lockout_interval()

new_zip = zipfile.ZipFile('./temp/updatedPackage.zip', "w")
for folder_name, subfolders, files in os.walk("./unpackaged"):
    new_zip.write(folder_name)
    for filename in files:
        new_zip.write(os.path.join(folder_name, filename))
        new_zip.write("./unpackaged//package.xml")
        new_zip.close()

with open("./temp/updatedPackage.zip", "rb") as f:
    data = f.read()
    encoded = base64.b64encode(data)
    converted = encoded.decode("utf-8")
print("\n\n Base64 new zip file created.\n\n") # We could print the Base64 data for debugging.

deploy_headers = {
        'content-type': 'text/xml',
        'charset': 'UTF-8',
        'SOAPAction': 'deploy'
    }
deploy_body = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:met="http://soap.sforce.com/2006/04/metadata">
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
deploy_it = requests.post(metadata_url, deploy_body, headers=deploy_headers)
f = open("./temp/deploystatus.xml", 'w')
f.write(deploy_it.text)
f.close()
deploy_xml = parse("./temp/deploystatus.xml")
result = deploy_xml.getElementsByTagName('id')
did = result[0].firstChild.nodeValue

check_deploy_headers = {
        'content-type': 'text/xml',
        'charset': 'UTF-8',
        'SOAPAction': 'checkDeployStatus'
    }
check_deploy_status = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:met="http://soap.sforce.com/2006/04/metadata">
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
check_deployment = requests.post(metadata_url, check_deploy_status, headers=check_deploy_headers)
f = open("./deployresult.xml", 'w')
f.write(check_deployment.text)
f.close()
deploy_result = parse("./deployresult.xml")
result = deploy_result.getElementsByTagName('status')
print("\n\nDeployment result: " + result[0].firstChild.nodeValue)
if result[0].firstChild.nodeValue == 'Succeeded':
    time.sleep(2)
    print("\n\n**** Update successful.\n\n")
    os.remove("./deployresult.xml")
else:
    print("\n***ERROR: See deployresult.xml for details. Printing error to stdout in 5 seconds;\n\n")
    time.sleep(5)
    print(check_deployment.text)
    print("\n")
    exit()
time.sleep(2)
ts = time.time()
st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
log_text = """
.
Action logged. Details:
Session ID: """ + sid + """

TimeStamp: """ + st + """
.
"""
f = open("./log.txt", "a")
f.write(log_text)
f.close()
shutil.rmtree('./unpackaged')
shutil.rmtree('./temp')
