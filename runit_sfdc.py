import json
import httplib2
import time
import urllib3
import requests
import xml.dom.minidom
import collections
import time
import os
import zipfile
import base64
import beatbox
from runit_sfdc_ui import *
from random import choice
from string import ascii_lowercase
from config_sfdc import *
from simple_salesforce import Salesforce

#Unit tests
sf = Salesforce(username=ADMIN1_USERNAME, password=ADMIN1_PASSWORD, security_token=ADMIN1_TOKEN)

def main():
    #-----Admin 1--Getting global Administrator Session ID.
    AdminSid = getUserSid(ADMIN1_USERNAME, ADMIN1_PTK)
    #Admin 1--Making sure we will be able to manipulate without any identification
    setIPRange(SysAdminProfileName, AdminSid)
    #-----Super-Admin-----
    #-----Admin 1--Because of weak lockout policy, it triggers Security Control: Lockout effective period -super-admin
    changeLockoutPeriod(AdminSid)
    #-----Admin 1--Disable clickjack protection for customer Visualforce pages with standard headers
    disableClickJackWithStdHeaders(AdminSid)
    #-----Admin 1--Creating 4 users - due to license limitations, the other 2 will be Force.com Free users.
    createUser(LSL_USER1_USERNAME, LSL_USER1_ALIAS, LSL_USER1_USERNAME, LSL_USER1_USERNAME, 'Standard Platform User')
    createUser(LSL_USER2_USERNAME, LSL_USER2_ALIAS, LSL_USER2_USERNAME, LSL_USER2_USERNAME, 'Force.com - Free User')
    createUser(LSL_USER3_USERNAME, LSL_USER3_ALIAS, LSL_USER3_USERNAME, LSL_USER3_USERNAME, 'Force.com - Free User')
    createUser(LSL_USER4_USERNAME, LSL_USER4_ALIAS, LSL_USER4_USERNAME, LSL_USER4_USERNAME, 'Force.com - App Subscription User')
    #-----Admin 1--set IP range (for admin profile) - making sure we will be able to manipulate without any identification
    setIPRange(SysAdminProfileName, AdminSid)


    #Path#1: Account compromise --User1
    #-----User 1--brute force login, Attacker brute forced account successfully, triggers Threat: Failed login(e.g. 5 average, 2x) 
    switchUserProfileOrRole(LSL_USER1_USERNAME, 'System Administrator')
    # failUserLogins(SFDC_TEST_USER1, "X", num_failed_attempts)
    #-----User 1--Login from remote triggers UBA Risk User: High, activity from unseen browser, device, OS, unseen location(including unseen IPs v2) (score approx: 45-50)
    # failUserLogins(SFDC_TEST_USER1, SFDC_TEST_USER1_PASSWORD, num_failed_attempts, tor_proxy_ip, tor_proxy_port, "Mozilla/1.0 (Windows CE 0.1; Win63; x63; rv:1.1) GeckoX/20100101 Firebug/0.1")
    #-----User 1-----UBA Risk User: 10x High, Data export --- Instead of this, Attacker set Trusted IP Range to enable backdoor access, triggers Policy alert.
    # To verify, in the UI this is at "Network Access"
    setTrustedIPRange(howManyTrustedIPRangeSets, 'lsl-TrustRange-'+randStrGen(4),'192.168.0.11','192.168.0.200', LSL_USER1_USERNAME, DefUserPass)
    switchUserProfileOrRole(LSL_USER1_USERNAME, 'Standard Platform User')

    #Path 2: Data Exfiltration--User2
    #-----User 2--Grant Admin permissions
    switchUserProfileOrRole(LSL_USER2_USERNAME, 'System Administrator')
    #-----User 2--60+(configurable) Mass Transfer to another account, triggers UBA Risk User: Medium, Mass Transfer+After-hr.
    #Creating given numbers of mockup account data to have something to transfer.
    LSL_USER2_FULLNAME = getUserFullName(LSL_USER2_USERNAME)
    Admin1FullName = getUserFullName(ADMIN1_USERNAME)
    createMockupAccount(howManyMockupAccounts, ADMIN1_USERNAME)
    mass_transfer(LSL_USER2_USERNAME, DefUserPass, Admin1FullName, LSL_USER2_FULLNAME, howManyMassTransfers)
    switchUserProfileOrRole(LSL_USER2_USERNAME, 'Force.com - Free User')

    #Path#3: Insider Threat--User3
    ##-----User 3--Admin grant excessive permissions to insider user, triggers Policy alert: Profile/Change user permissions
    switchUserProfileOrRole(LSL_USER3_USERNAME, 'System Administrator')
    #-----User 3--We deploy new Sharing Rules as an insider threat.
    #We have some static XML content and if we want to add multiple rules, don't want to add the header all the time.
    #create some mockup sharing rules.
    createZipObjects()
    addLeadSharingRule(howManySharingRules, "Read")
    closeRules()
    deployZipFile(LSL_USER3_USERNAME, DefUserPass)
    #-----User 3--3-Insider user is corrupted by a vendor, he helped vendor to extend contract term, triggers Policy alert: Contract Create+Update
    response = createMockupContract(LSL_USER3_USERNAME, "lsl-Account-firstMockup", "3", "2016-03-01")
    updateContract(response['id'])
    #-----User 3--4-Before termination, insider user also Mass deleting data, triggers UBA Risk User: High, Mass Delete
    for x in range(0, howManyMassDelete):
        createMockupAccount(howManyMockupAccounts, LSL_USER3_USERNAME)
        mass_delete(LSL_USER3_USERNAME, DefUserPass)
        print("Mass Delete iteration nr.: "+str(x))
    #-----User 3--Policy alert: Change user profile
    switchUserProfileOrRole(LSL_USER3_USERNAME, 'Force.com - Free User')

    #Path 4: Insider Threat--User4
    #-----User 4--UBA Risk User: 20x Medium, Reports export, Report Run
    #2-The 3rd party has the permission to access sensitive data and function, he run and export the reports, sale to competitor, triggers UBA Risk User: Medium, Reports exported, Report Run
    #3-The 3rd party also export data, triggers UBA Risk User: High, Data Export
    #4-For all report activities by the 3rd party, stand out in KSI: Top customer report run and Top customer report exported
    switchUserProfileOrRole(LSL_USER4_USERNAME, 'System Administrator')
    reportName = create_Report(howManyReportsCreate, LSL_USER4_USERNAME, DefUserPass, "Accounts")
    exportReport(howManyExportReports, reportName, LSL_USER4_USERNAME, DefUserPass)
    switchUserProfileOrRole(LSL_USER4_USERNAME, 'Force.com - App Subscription User')
 
#Creating a user
def createUser(userName, Alias, Email, lastName, ProfileName):
    ProfileId = getProfileId(ProfileName)
    try:
        account = sf.User.create({'userName':userName,
                              'Alias':Alias,
                              'Email':Email,
                              'lastName':lastName,
                              'EmailEncodingKey':'UTF-8',
                              'TimeZoneSidKey':'America/New_York',
                              'LocaleSidKey':'en_US',
                              'ProfileId':ProfileId,
                              'LanguageLocaleKey':'en_US'})
        setPass(userName, DefUserPass)
    except:
        try:
            activateUser(userName)
            setPass(userName, DefUserPass)
        except:
            setPass(userName, DefUserPass)

def getUserFullName(userName):
    userinfo = sf.query("SELECT FirstName, LastName FROM User WHERE username = '"+userName+"'")
    dict = collections.OrderedDict(userinfo)
    dictitems = list(dict.values())[2]
    itemlist = (dictitems.pop())
    dict2 = collections.OrderedDict(itemlist)
    Firstname = list(dict2.values())[1]
    Lastname = list(dict2.values())[2]
    if Firstname is None:
        Fullname = Lastname
    else:
        Fullname = Firstname+" "+Lastname
    return Fullname

#Resetting a user's password
def setPass(userName, NewPassword):
    uid = getUserId(userName)
    print("\nDefaulting Password for user with UID: "+uid+"\n")
    sf2 = beatbox.PythonClient()
    sf2.login(ADMIN1_USERNAME, ADMIN1_PASSWORD)
    try:
        sf2.setPassword(uid, DefUserPass)
    except:
        pass

#login for all users, keep session Ids
def getUserSid(User, Pass):
    loginHeaders = {
        'content-type': 'text/xml',
        'charset': 'UTF-8',
        'SOAPAction': 'login'
        }
    loginEnvelope = """
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:urn="urn:enterprise.soap.sforce.com">
            <soapenv:Header>
            </soapenv:Header>
        <soapenv:Body>
            <urn:login>
                <urn:username>""" + ''+User+'' + """</urn:username>
                <urn:password>""" + ''+Pass+'' + """</urn:password>
            </urn:login>
        </soapenv:Body>
        </soapenv:Envelope>
    """
    loginResponse = requests.post(partnerURL, loginEnvelope, headers=loginHeaders)
    dom = xml.dom.minidom.parseString(loginResponse.text)
    userSidResult = dom.getElementsByTagName('sessionId')
    if userSidResult[0].firstChild.nodeValue is None:
        print("\nI wasn't successful. Error was:\n")
        print(loginResponse.text + '\n')
    else:
        userSid = userSidResult[0].firstChild.nodeValue
        return(userSid)


#This is useful in general to manipulate any user's details
def getUserId(userName):
    userinfo = sf.query("SELECT Id FROM User WHERE username = '"+userName+"'")
    # Userinfo is an ordereddict that contains a list that contains another ordereddict so we need to dig in a bit:
    dict = collections.OrderedDict(userinfo)
    dictitems = list(dict.values())[2]
    itemlist = (dictitems.pop())
    dict2 = collections.OrderedDict(itemlist)
    uid = list(dict2.values())[1]
    return uid

def getUserProfileId(whichUser):
    query = sf.query("SELECT ProfileId FROM User where username = '"+whichUser+"'")
    dict = collections.OrderedDict(query)
    dictitems = list(dict.values())[2]
    if len(dictitems) == 0:
        print("Could not get System Administrator Profile Id. Continuing...\n")
        return None
    else:
        itemlist = (dictitems.pop())
        dict2 = collections.OrderedDict(itemlist)
        profId = list(dict2.values())[1]
        return profId

def getProfileId(ProfileName):
    query = sf.query("SELECT Id FROM Profile WHERE name = '"+ProfileName+"'")
    dict = collections.OrderedDict(query)
    dictitems = list(dict.values())[2]
    if len(dictitems) == 0:
        print("Could not get System Administrator Profile Id. Continuing...\n")
        return None
    else:
        itemlist = (dictitems.pop())
        dict2 = collections.OrderedDict(itemlist)
        profId = list(dict2.values())[1]
        return profId

def switchUserProfileOrRole(user1, user1_profile, user2_profile=None, howManyTimes=None):
    if howManyTimes is None:
        userid = getUserId(user1)
        switchToProfileId = getProfileId(user1_profile)
        sf.User.update(userid,{'ProfileId': ''+switchToProfileId+''})
    else:
        while howManyTimes>0:
            userid = getUserId(user1)
            origProfileId = getUserProfileId(user1)
            switchbetween1 = getProfileId(user1_profile)
            switchbetween2 = getProfileId(user2_profile)
            sf.User.update(userid,{'ProfileId': ''+switchbetween2+''})
            print("The "+user1+"'s profile switched from "+switchbetween1+" to "+switchbetween2+" Profile Id.")
            newProfileId = getUserProfileId(user1)
            sf.User.update(userid,{'ProfileId': ''+switchbetween1+''})
            print("The "+user1+"'s profile switched from "+switchbetween2+" to "+switchbetween1+" Profile Id.")
            print("UserProfile switches left: "+str(howManyTimes-1))
            howManyTimes -= 1

# Reactivate a user if existing
def activateUser(userName):
    userinfo = sf.query("SELECT IsActive FROM User WHERE username = '"+userName+"'")
    itemlist = ((userinfo.values())[2])
    dict = collections.OrderedDict(userinfo)
    dictitems = list(dict.values())[2]
    itemlist = (dictitems.pop())
    dict2 = collections.OrderedDict(itemlist)
    isActive = list(dict2.values())[1]
    if not isActive:
        print("User exists, but is not active. Activating.")
        uid = getUserId(userName)
        sf.User.update(uid,{'IsActive' : 'true'})
    else:
        print("User is active, no need to re-enable.")

def createMockupAccount(howMany, Owner):
    OwnerId = getUserId(Owner)
    data1 = sf.Account.create({'type': 'Account',
                               'Name': 'lsl-Account-firstMockup',
                               'Website': 'http://www.IamJustAtestWebSite.com',
                               'OwnerId': ''+OwnerId+''})
    list = ['lsl-Account-firstMockup']
    howMany -= 1
    while howMany > 0:
        testData = "lsl-Account-"+randStrGen(8)
        OwnerId = getUserId(Owner)
        data1 = sf.Account.create({'type': 'Account',
                                   'Name': ''+testData+'',
                                   'Website': 'http://www.IamJustAtestWebSite.com',
                                   'OwnerId': ''+OwnerId+''})
        print("Some mockup Account "+testData+" for user: "+Owner+" created.")
        list.append(testData)
        howMany -= 1
    print("Following mockup Accounts have been created: "+ str(list))
    return list

def getAccountId(accountName):
    userinfo = sf.query("SELECT Id FROM Account WHERE Name = '"+accountName+"'")
    itemlist = ((userinfo.values())[2])
    dict = collections.OrderedDict(userinfo)
    dictitems = list(dict.values())[2]
    itemlist = (dictitems.pop())
    dict2 = collections.OrderedDict(itemlist)
    accId = list(dict2.values())[1]
    return accId

def createMockupContract(Owner, accountName, contractTerm, startDate):
    OwnerId = getUserId(Owner)
    accountId = getAccountId(accountName)
    data1 = sf.Contract.create({'AccountId': accountId,
                                'ContractTerm': contractTerm,
                                'StartDate': startDate,
                                'OwnerId': OwnerId})
    print("Mockup contract for Account "+accountId+" created.")
    return data1

def updateContract(id):
    query = sf.Contract.update(id,{'ContractTerm': '75'})

def setIPRange(profileName, AdminSid):
    updateMetadataEnvelope = """
        <env:Envelope xmlns:env="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <env:Header>
                <urn:SessionHeader xmlns:urn="http://soap.sforce.com/2006/04/metadata">
                    <urn:sessionId>"""+AdminSid+"""</urn:sessionId>
                </urn:SessionHeader>
            </env:Header>
            <env:Body>
                <updateMetadata xmlns="http://soap.sforce.com/2006/04/metadata">
                    <metadata xsi:type="Profile">
                    <fullName>"""+profileName+"""</fullName>
                       <loginIpRanges>
                          <endAddress>255.255.255.255</endAddress>
                          <startAddress>0.0.0.0</startAddress>
                       </loginIpRanges>
                    </metadata>
                </updateMetadata>
            </env:Body>
        </env:Envelope>
        """

    soapResponse = requests.post(metadataURL, updateMetadataEnvelope, headers=updateMetadataHeader)
    dom = xml.dom.minidom.parseString(soapResponse.text)
    resultElement = dom.getElementsByTagName('success')
    resultValue = resultElement[0].firstChild.nodeValue
    if len(resultValue) == 0:
        print("I've encountered an issue. Request response:\n")
        print(soapResult.text+"\n")
        return None
    else:
        if resultElement[0].firstChild.nodeValue:
            print("Login IP range successfully set.")
        else:
            print("I've encountered an issue. Request response:\n")
            print(soapResult.text+"\n")
            return None

def changeLockoutPeriod(AdminSid):
    soapBody = """
    <env:Envelope xmlns:env="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <env:Header>
            <urn:SessionHeader xmlns:urn="http://soap.sforce.com/2006/04/metadata">
                <urn:sessionId>""" + AdminSid + """</urn:sessionId>
            </urn:SessionHeader>
        </env:Header>
        <env:Body>
            <updateMetadata xmlns="http://soap.sforce.com/2006/04/metadata">
                <metadata xsi:type="SecuritySettings">
                <fullName>*</fullName>
                <passwordPolicies>
                      <lockoutInterval>""" + lockoutInterval + """</lockoutInterval>
                   </passwordPolicies>
                </metadata>
            </updateMetadata>
        </env:Body>
    </env:Envelope>
    """
    soapResult = requests.post(metadataURL, soapBody, headers=updateMetadataHeader)

    dom = xml.dom.minidom.parseString(soapResult.text)
    resultElement = dom.getElementsByTagName('success')
    resultValue = resultElement[0].firstChild.nodeValue
    if len(resultValue) == 0:
        print("I've encountered an issue. Request response:\n")
        print(soapResponse.text+"\n")
        return None
    else:
        if resultElement[0].firstChild.nodeValue:
            print("New Lockout time successfully set.")
        else:
            print("I've encountered an issue. Request response:\n")
            print(soapResponse.text+"\n")
            return None

def disableClickJackWithStdHeaders(AdminSid):
    soapBody = """
    <env:Envelope xmlns:env="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <env:Header>
            <urn:SessionHeader xmlns:urn="http://soap.sforce.com/2006/04/metadata">
                <urn:sessionId>""" + AdminSid + """</urn:sessionId>
            </urn:SessionHeader>
        </env:Header>
        <env:Body>
            <updateMetadata xmlns="http://soap.sforce.com/2006/04/metadata">
                <metadata xsi:type="SecuritySettings">
                <fullName>*</fullName>
                   <sessionSettings>
                    <enableClickjackNonsetupUser>false</enableClickjackNonsetupUser>
                   </sessionSettings>
                </metadata>
            </updateMetadata>
        </env:Body>
    </env:Envelope>
    """
    soapResult = requests.post(metadataURL, soapBody, headers=updateMetadataHeader)

    dom = xml.dom.minidom.parseString(soapResult.text)
    resultElement = dom.getElementsByTagName('success')
    resultValue = resultElement[0].firstChild.nodeValue
    if len(resultValue) == 0:
        print("I've encountered an issue. Request response:\n")
        print(soapResult.text+"\n")
        return None
    else:
        if resultElement[0].firstChild.nodeValue:
            print("Successfully disabled clickjack protection for customer Visualforce pages with standard headers.")
        else:
            print("I've encountered an issue. Request response:\n")
            print(soapResult.text+"\n")
            return None

def randStrGen(nr):
    randString = (''.join(choice(ascii_lowercase) for i in range(nr)))
    return randString

def createZipObjects():
    if not os.path.exists(os.path.dirname(ruleFile)):
        try:
            os.makedirs(os.path.dirname(ruleFile))
        except:
            pass
    with open(ruleFile, "w") as f:
        f.write("""<?xml version="1.0" encoding="UTF-8"?>
<SharingRules xmlns="http://soap.sforce.com/2006/04/metadata">"""+"\n")
    with open('./tmp/unpackaged/package.xml', "w") as f:
        f.write("""<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>*</members>
        <name>SharingRules</name>
    </types>
    <version>35.0</version>
</Package>"""+"\n")

def addLeadSharingRule(howMany, accessLevel):
    while howMany>0:
        fullName = "lsl_"+randStrGen(4)
        label = "lsl-"+randStrGen(5)
        with open(ruleFile, "a") as f:
            f.write("""     <sharingOwnerRules>
                <fullName>""" + fullName +"""</fullName>
                <accessLevel>"""+ accessLevel +"""</accessLevel>
                <label>""" + label + """</label>
                <sharedTo>
                    <allInternalUsers></allInternalUsers>
                </sharedTo>
                <sharedFrom>
                    <allInternalUsers></allInternalUsers>
                </sharedFrom>
            </sharingOwnerRules>"""+"\n")
            print("Lead sharing rule with label: "+ label +" successfully created.")
            howMany -= 1

def closeRules():
    with open(ruleFile, "ab") as f:
        f.write("""</SharingRules>"""+"\n")

def getReportId(reportName, asUser, asPass):
    userSid = getUserSid(asUser, asPass)
    sf2 = Salesforce(instance_url=instanceURL, session_id=userSid)
    query = sf2.query("SELECT Id FROM Report WHERE Name = '"+reportName+"'")
    dict = collections.OrderedDict(query)
    dictitems = list(dict.values())[2]
    itemlist = (dictitems.pop())
    dict2 = collections.OrderedDict(itemlist)
    reportId = list(dict2.values())[1]
    if len(dict2) == 0:
        print("Could not get reportId.\n")
        return None
    else:
        return(reportId,userSid)

def exportReport(howMany, reportName, asUser, asPass):
    (reportId,userSid) = getReportId(reportName, asUser, asPass)
    while howMany>0:
        response = requests.get(instanceURL+"/"+reportId+"?view=d&snip&export=1&enc=UTF-8&excel=1", headers = sf.headers, cookies = {'sid' : userSid})
        f = open("lsl-report-"+randStrGen(4)+".csv", 'w')
        f.write(response.text)
        f.close()
        howMany -= 1

def deployZipFile(asUser, AsPass):
    UserSid = getUserSid(asUser, AsPass)
    newZip = zipfile.ZipFile(packageZipFile, "w")
    dirPath = './tmp'
    lenDirPath = len(dirPath)
    for root, _ , files in os.walk(dirPath):
        for file in files:
            filePath = os.path.join(root, file)
            newZip.write(filePath, filePath[lenDirPath :] )
    newZip.close()
    with open(packageZipFile, "rb") as f:
        bytes = f.read()
        encoded = base64.b64encode(bytes)
        b64code = encoded.decode("utf-8")

    deployHeaders = {
            'content-type': 'text/xml',
            'charset': 'UTF-8',
            'SOAPAction': 'deploy'
    }
    deployBody = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:met="http://soap.sforce.com/2006/04/metadata">
        <soapenv:Header>
          <met:SessionHeader>
                <sessionId>""" + UserSid + """</sessionId>
          </met:SessionHeader>
       </soapenv:Header>
       <soapenv:Body>
        <deploy xmlns="http://soap.sforce.com/2006/04/metadata">
          <ZipFile>""" + b64code + """</ZipFile>
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

    soapResult = requests.post(metadataURL, deployBody, headers=deployHeaders)

    dom = xml.dom.minidom.parseString(soapResult.text)
    resultElement = dom.getElementsByTagName('id')
    resultValue = resultElement[0].firstChild.nodeValue
    if len(resultValue) == 0:
        print("I've encountered an issue. Request response:\n")
        print(soapResult.text+"\n")
        return None
    else:
        if resultElement[0].firstChild.nodeValue:
            print("Got deployment ID.")
            did = resultElement[0].firstChild.nodeValue
        else:
            print("I've encountered an issue. Request response:\n")
            print(soapResult.text+"\n")
            return None
    time.sleep(2)

    CheckDeployHeaders = {
            'content-type': 'text/xml',
            'charset': 'UTF-8',
            'SOAPAction': 'checkDeployStatus'
    }
    CheckDeployStatus = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:met="http://soap.sforce.com/2006/04/metadata">
       <soapenv:Header>
          <met:SessionHeader>
                <sessionId>""" + UserSid + """</sessionId>
          </met:SessionHeader>
       </soapenv:Header>
       <soapenv:Body>
          <met:checkDeployStatus>
             <met:asyncProcessId>""" + did + """</met:asyncProcessId>
             <met:includeDetails>true</met:includeDetails>
          </met:checkDeployStatus>
       </soapenv:Body>
    </soapenv:Envelope>"""

    soapResult = requests.post(metadataURL, CheckDeployStatus, headers=CheckDeployHeaders)
    dom = xml.dom.minidom.parseString(soapResult.text)
    resultElement = dom.getElementsByTagName('status')
    resultValue = resultElement[0].firstChild.nodeValue
    if len(resultValue) == 0:
        print("I've encountered an issue. Request response:\n")
        print(soapResult.text+"\n")
        return None
    else:
        if resultElement[0].firstChild.nodeValue == 'Succeeded':
            print("Deployment succeeded.")
        else:
            print("I've encountered an issue. Request response:\n")
            print(soapResult.text+"\n")
            return None

#UBA Risk User: 10x High, Set Trusted IP range.
def setTrustedIPRange(count, description, startIP, endIP, owner, passwd):
    UserSid = getUserSid(owner, passwd)
    soapBodyPart1 = """
        <env:Envelope xmlns:env="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <env:Header>
                <urn:SessionHeader xmlns:urn="http://soap.sforce.com/2006/04/metadata">
                    <urn:sessionId>""" + UserSid + """</urn:sessionId>
                    </urn:SessionHeader>
            </env:Header>
            <env:Body>
                <updateMetadata xmlns="http://soap.sforce.com/2006/04/metadata">
                <metadata xsi:type="SecuritySettings">
                <fullName>*</fullName>
			        <networkAccess>"""
    soapBodyPart2 = """
                    </networkAccess>
                </metadata>
                </updateMetadata>
            </env:Body>
        </env:Envelope>
        """
    while count > 0:
        ipRange = """
            <ipRanges>
            <description>"""+ description +"""</description>
                <start>"""+ startIP +"""</start>
                <end>"""+ endIP +"""</end>
            </ipRanges>"""
        soapResult = requests.post(metadataURL, soapBodyPart1+ipRange+soapBodyPart2, headers=updateMetadataHeader)
        print("Added trusted IP Range "+str(count)+" time(s).")
        ipRange = """ """
        soapResult = requests.post(metadataURL, soapBodyPart1+soapBodyPart2, headers=updateMetadataHeader)
        print("Deleted trusted IP Ranges "+str(count)+" times.")
        count -= 1

main()
