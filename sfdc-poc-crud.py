import requests
import sys
import xml.dom.minidom

login_url = 'https://login.salesforce.com/services/Soap/c/35.0'
metadata_url = 'https://na24.salesforce.com/services/Soap/m/35.0'

# Valid values could be: FifteenMinutes, ThirtyMinutes, SixtyMinutes, TwoHours, FourHours, EightHours, TwelveHours
new_lockout_interval = 'ThirtyMinutes'
new_session_timeout = 'FifteenMinutes'

# Check for python version - the script currently is in 3.4
req_version = (3, 4)
cur_version = sys.version_info
if cur_version >= req_version:
    print("\n\nPython version min. 3.4 requirement: PASS\n\n")
else:
    print("\n\nPlease use Python v3 or run using python3\n\n")
    exit()

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

try:
    dom = xml.dom.minidom.parseString(login_result.text)
    sidresult = dom.getElementsByTagName('sessionId')
    sid = sidresult[0].firstChild.nodeValue
except IndexError:
    dom = xml.dom.minidom.parseString(login_result.text)
    sidresult = dom.getElementsByTagName('faultstring')
    sid = sidresult[0].firstChild.nodeValue
    print("\nI wasn't successful. Error was:\n")
    print(sid + '\n')

update_headers = {
    'content-type': 'text/xml',
    'charset': 'UTF-8',
    'SOAPAction': 'updateMetadata'
}

update_body = """
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
                  <lockoutInterval>""" + new_lockout_interval + """</lockoutInterval>
               </passwordPolicies>
               <sessionSettings>
                  <sessionTimeout>""" + new_session_timeout + """</sessionTimeout>
               </sessionSettings>
            </metadata>
        </updateMetadata>
    </env:Body>
</env:Envelope>
"""
update_result = requests.post(metadata_url, update_body, headers=update_headers)

try:
    result_value = xml.dom.minidom.parseString(update_result.text).getElementsByTagName('success')[0].firstChild.nodeValue
    print("I successfully updated the elements requested for the update.")
except IndexError:
    result_value = xml.dom.minidom.parseString(update_result.text).getElementsByTagName('faultstring')[0].firstChild.nodeValue
    print("\n\nI wasn't successful. Error was:\n\n")
    print('\n' + result_value + '\n')
