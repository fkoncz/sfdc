import requests
import sys
import xml.dom.minidom
from xml.dom.minidom import parse

loginURL = 'https://login.salesforce.com/services/Soap/c/35.0'
metadataURL = 'https://na24.salesforce.com/services/Soap/m/35.0'

# Valid values could be: FifteenMinutes, ThirtyMinutes, SixtyMinutes, TwoHours, FourHours, EightHours, TwelveHours
NewLockoutInterval = 'ThirtyMinutes'
NewSessionTimeOut = 'FifteenMinutes'

# Check for python version - the script currently is in 3.4
req_version = (3, 4)
cur_version = sys.version_info
if cur_version >= req_version:
    print("\n\nPython version min. 3.4 requirement: PASS\n\n")
else:
    print("\n\nPlease use Python v3 or run using python3\n\n")
    exit()

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
loginResult = requests.post(loginURL, loginBody, headers=loginHeaders)

try:
    dom = xml.dom.minidom.parseString(loginResult.text)
    sidresult = dom.getElementsByTagName('sessionId')
    sid = sidresult[0].firstChild.nodeValue
except IndexError:
    dom = xml.dom.minidom.parseString(loginResult.text)
    sidresult = dom.getElementsByTagName('faultstring')
    sid = sidresult[0].firstChild.nodeValue
    print("\nI wasn't successful. Error was:\n")
    print(sid + '\n')

updateHeaders = {
    'content-type': 'text/xml',
    'charset': 'UTF-8',
    'SOAPAction': 'updateMetadata'
}

updateBody = """
<env:Envelope xmlns:env="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <env:Header>
        <urn:SessionHeader xmlns:urn="http://soap.sforce.com/2006/04/metadata">
            <urn:sessionId>""" + sid + """</urn:sessionId>
        </urn:SessionHeader>
    </env:Header>
    <env:Body>
        <updateMetadata xmlns="http://soap.sforce.com/2006/04/metadata">
            <metadata xsi:type="SecuritySettings">
 	        <fullName>*</fullName>
            <passwordPolicies>
                  <lockoutInterval>""" + NewLockoutInterval + """</lockoutInterval>
               </passwordPolicies>
               <sessionSettings>
                  <sessionTimeout>""" + NewSessionTimeOut + """</sessionTimeout>
               </sessionSettings>
            </metadata>
        </updateMetadata>
    </env:Body>
</env:Envelope>
"""
updateResult = requests.post(metadataURL, updateBody, headers=updateHeaders)

try:
    dom = xml.dom.minidom.parseString(updateResult.text)
    resultElement = dom.getElementsByTagName('success')
    resultValue = resultElement[0].firstChild.nodeValue
    print("I successfully updated the elements requested for the update.")
except IndexError:
    dom = xml.dom.minidom.parseString(updateResult.text)
    resultElement = dom.getElementsByTagName('faultstring')
    resultValue = resultElement[0].firstChild.nodeValue
    print("\n\nI wasn't successful. Error was:\n\n")
    print('\n' + resultValue + '\n')
