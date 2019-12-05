import requests
import collections
import xml.dom.minidom
from config_sfdc_rsa import *
from runit_sfdc_ui_rsa import *
from simple_salesforce import Salesforce


sf = Salesforce(username=ADMIN1_USERNAME, password=ADMIN1_PASSWORD, security_token=ADMIN1_TOKEN)

def main():
    #brute force login
    #failUserLogins(SFDC_TEST_USER1, "X", num_failed_attempts)
    #login from unseen browser, device, OS, unseen location(including unseen IPs v2)
    #failUserLogins(SFDC_TEST_USER1, SFDC_TEST_USER1_PASSWORD, num_failed_attempts, tor_proxy_ip, tor_proxy_port, "Mozilla/1.0 (Windows CE 0.1; Win63; x63; rv:1.1) GeckoX/20100101 Firebug/0.1")

    #Create given number of users and deactivate them.
    ChatterFreeProfileId = getProfileId('Chatter Free User')
    createAndDeactUsers(NumUsers, LSL_DEMO_USERNAME, LSL_DEMO_ALIAS, LSL_DEMO_EMAIL, LSL_DEMO_LASTNAME, ChatterFreeProfileId)

    # Creating some mockup account data to have something to transfer.
    createMockupAccount(ADMIN1_USERNAME, "LSL-TestAccount2Data")
    createMockupAccount(ADMIN1_USERNAME, "LSL-TestAccount123Data")
    createMockupAccount(ADMIN1_USERNAME, "LSL-TestAccount1jri43Data")
    createMockupAccount(ADMIN1_USERNAME, "LSL-TestAccountData")
    createMockupAccount(ADMIN1_USERNAME, "LSL-TestAccount4523452345Data")
    Admin1FullName = getUserFullName(ADMIN1_USERNAME)
    #Create 2nd administrator user, if it is possible. If not, raise exception.
    #createAdmin2(ADMIN2_USERNAME)
    Admin2FullName = getUserFullName(ADMIN2_USERNAME)
    setIPRange(SysAdminProfileName)
    mass_transfer(ADMIN1_USERNAME, ADMIN1_PASSWORD, Admin1FullName, Admin2FullName, NumTransfers)
    deactivateUser(ADMIN2_USERNAME)
    print("\n\nDone with tasks.\n\n")







#This is useful in general to manipulate any user's details
def getUserId(userName):
    '''
    :param userName:
    :return:
    '''
    userinfo = sf.query("SELECT Id FROM User WHERE username = '"+userName+"'")
    # Userinfo is an ordereddict that contains a list that contains another ordereddict so we need to dig in a bit:
    dict = collections.OrderedDict(userinfo)
    dictitems = list(dict.values())[2]
    itemlist = (dictitems.pop())
    dict2 = collections.OrderedDict(itemlist)
    uid = list(dict2.values())[1]
    return uid

def getUserFullName(userName):
    '''
    :param userName:
    :return:
    '''
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


#Creating a user
def createAndDeactUsers(howMany, userName, Alias, Email, lastName, ProfileId):
    '''
    :param howMany:
    :param userName:
    :param Alias:
    :param Email:
    :param lastName:
    :param ProfileId:
    :return:
    '''
    try:
        while howMany>0:
            actualUsername = userName+str(howMany)+"@hotmail.com"
            actualEmail = Email+str(howMany)+"@hotmail.com"
            actualAlias = Alias+str(howMany)
            actualLastname = lastName+str(howMany)+"Joe"
            sf.User.create({'userName': actualUsername,
                            'Alias': actualAlias,
                            'Email': actualEmail,
                            'lastName': actualLastname,
                            'EmailEncodingKey': 'UTF-8',
                            'TimeZoneSidKey': 'America/New_York',
                            'LocaleSidKey': 'en_US',
                            'ProfileId': ProfileId,
                            'LanguageLocaleKey': 'en_US'})
            print("User created. Now deactivating if not already deactivated.")
            deactivateUser(actualUsername)
            howMany -= 1
    except:
        print("Users created and deactivated.")
        pass

# Check if second Admin exists, if not create one, otherwise report license limitation

def createAdmin2(username):
    '''
    :param username:
    :return:
    '''
    SysAdminProfileId = getProfileId(SysAdminProfileName)
    try:
        sf.User.create({'userName': username,
                        'Alias': 'lsladm2',
                        'Email': 'lsladmin@yahoo.com',
                        'firstName': 'Doe',
                        'lastName': 'lsl-Admin2',
                        'EmailEncodingKey': 'UTF-8',
                        'TimeZoneSidKey': 'America/New_York',
                        'LocaleSidKey': 'en_US',
                        'ProfileId': SysAdminProfileId,
                        'LanguageLocaleKey': 'en_US'})
        print("2nd Administrator user created with username: "+username+"\n")
    except:
        print("\nWas not successful creating 2nd Administrator user. Are there enough licenses or could we deactivate one for the purpose?\n\n")
        #raise

# Deactivate a user if it exists
def deactivateUser(userName):
    '''
    :param userName:
    :return:
    '''
    userinfo = sf.query("SELECT IsActive FROM User WHERE username = '"+userName+"'")
    itemlist = ((userinfo.values())[2])
    dict = collections.OrderedDict(userinfo)
    dictitems = list(dict.values())[2]
    if len(dictitems) == 0:
        print("Could not deactivate user. Maybe it does not exist? Continuing...\n")
        return None
    else:
        itemlist = (dictitems.pop())
        dict2 = collections.OrderedDict(itemlist)
        isActive = list(dict2.values())[1]
        if isActive:
            print("User "+userName+" is active, deactivating.")
            uid = getUserId(userName)
            sf.User.update(uid,{'IsActive' : 'false'})
        else:
            print("User is not active, deactivating not necessary.")
            pass

def createMockupAccount(Owner, testData):
    '''
    :param Owner:
    :param testData:
    :return:
    '''
    OwnerId = getUserId(Owner)
    data1 = sf.Account.create({'type': 'Account',
                               'Name': ''+testData+'',
                               'Website': 'http://www.IamJustAtestWebSite.com',
                               'OwnerId': ''+OwnerId+''})
    print("\nSome mockup Account "+testData+" for user: "+Owner+" created.")

def getProfileId(ProfileName):
    '''
    :param ProfileName:
    :return:
    '''
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

def getAdminSid(userName, passwordWithToken):
    '''
    :param userName:
    :param passwordWithToken:
    :return:
    '''
    loginHeader = {
        'content-type': 'text/xml',
        'charset': 'UTF-8',
        'SOAPAction': 'login'
        }
    loginEnvelope = """
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:urn="urn:enterprise.soap.sfo
rce.com">
           <soapenv:Header>
              <urn:LoginScopeHeader>
                 <urn:organizationId/>
                 <!--Optional:-->
                 <urn:portalId/>
              </urn:LoginScopeHeader>
           </soapenv:Header>
           <soapenv:Body>
              <urn:login>
                 <urn:username>"""+userName+"""</urn:username>
                 <urn:password>"""+passwordWithToken+"""</urn:password>
              </urn:login>
           </soapenv:Body>
        </soapenv:Envelope>
    """
    soapResponse = requests.post(loginURL, loginEnvelope, headers=loginHeader)
    dom = xml.dom.minidom.parseString(soapResponse.text)
    soapResult = dom.getElementsByTagName('sessionId')
    if soapResult[0].firstChild.nodeValue is None:
        print("\nI wasn't successful getting Admin Session ID. Error was:\n")
        print(soapResponse.text + '\n')
    else:
        AdminSid = soapResult[0].firstChild.nodeValue
        print("Admin successfully logged in and got "+AdminSid+" session ID.\n")
        return AdminSid

def setIPRange(profileName):
    '''
    :param profileName:
    :return:
    '''
    AdminSid = getAdminSid(ADMIN1_USERNAME, ADMIN1_PTK)
    updateMetadataHeader = {
        'content-type': 'text/xml',
        'charset': 'UTF-8',
        'SOAPAction': 'updateMetadata'
        }
    updateMetadataEnvelope = """
        <env:Envelope xmlns:env="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchem
a-instance">
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
    soapResult = dom.getElementsByTagName('success')
    if len(soapResult) == 0:
        print("I've encountered an issue. Request response:\n")
        print(soapResponse.text+"\n")
        return None
    else:
        if soapResult[0].firstChild.nodeValue:
            print("Login IP range successfully set.")
        else:
            print("I've encountered an issue. Request response:\n")
            print(soapResponse.text+"\n")
            return None
main()
