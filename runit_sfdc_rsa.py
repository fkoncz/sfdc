import xml.dom.minidom
from Config.config_sfdc_rsa import *
from runit_sfdc import *
from simple_salesforce import Salesforce
sf = Salesforce(username=ADMIN1_USERNAME, password=ADMIN1_PASSWORD, security_token=ADMIN1_TOKEN)


def main():
    # brute force login
    # failUserLogins(SFDC_TEST_USER1, "X", num_failed_attempts)
    # login from unseen browser, device, OS, unseen location(including unseen IPs v2)
    # failUserLogins(SFDC_TEST_USER1, SFDC_TEST_USER1_PASSWORD, num_failed_attempts, tor_proxy_ip,
    # tor_proxy_port, "Mozilla/1.0 (Windows CE 0.1; Win63; x63; rv:1.1) GeckoX/20100101 Firebug/0.1")

    # Create given number of users and deactivate them.
    admin1_sid = get_user_sid(ADMIN1_USERNAME, ADMIN1_PTK)
    chatter_free_profile_id = get_profile_id('Chatter Free User')
    create_and_deactivate_users(NumUsers, LSL_DEMO_USERNAME, LSL_DEMO_ALIAS, LSL_DEMO_EMAIL, LSL_DEMO_LASTNAME,
                                chatter_free_profile_id)

    # Creating some mockup account data to have something to transfer.
    create_mockup_account(ADMIN1_USERNAME, "LSL-TestAccount2Data")
    create_mockup_account(ADMIN1_USERNAME, "LSL-TestAccount123Data")
    create_mockup_account(ADMIN1_USERNAME, "LSL-TestAccount1jri43Data")
    create_mockup_account(ADMIN1_USERNAME, "LSL-TestAccountData")
    create_mockup_account(ADMIN1_USERNAME, "LSL-TestAccount4523452345Data")
    admin1_full_name = get_user_full_name(ADMIN1_USERNAME)
    # Create 2nd administrator user, if it is possible. If not, raise exception.
    # createAdmin2(ADMIN2_USERNAME)
    admin2_full_name = get_user_full_name(ADMIN2_USERNAME)
    set_ip_range(sysadmin_profile_name, admin1_sid)
    mass_transfer(ADMIN1_USERNAME, ADMIN1_PASSWORD, admin1_full_name, admin2_full_name, NumTransfers)
    deactivate_user(ADMIN2_USERNAME)
    print("\n\nDone with tasks.\n\n")


# This is useful in general to manipulate any user's details
def get_user_id(username):
    """
    :param username:
    :return:
    """
    userinfo = sf.query("SELECT Id FROM User WHERE username = '" + username + "'")
    # Userinfo is an ordereddict that contains a list that contains another OrderedDict so we need to dig in a bit:
    dict = collections.OrderedDict(userinfo)
    dictitems = list(dict.values())[2]
    itemlist = (dictitems.pop())
    dict2 = collections.OrderedDict(itemlist)
    uid = list(dict2.values())[1]
    return uid


def get_user_full_name(username):
    """
    :param username:
    :return:
    """
    userinfo = sf.query("SELECT FirstName, LastName FROM User WHERE username = '" + username + "'")
    dict = collections.OrderedDict(userinfo)
    dictitems = list(dict.values())[2]
    itemlist = (dictitems.pop())
    dict2 = collections.OrderedDict(itemlist)
    firstname = list(dict2.values())[1]
    lastname = list(dict2.values())[2]
    if firstname is None:
        fullname = lastname
    else:
        fullname = firstname + " " + lastname
    return fullname


# Creating a user
def create_and_deactivate_users(how_many, username, alias, email, lastname, profile_id):
    """
    :param how_many:
    :param username:
    :param alias:
    :param email:
    :param lastname:
    :param profile_id:
    :return:
    """
    try:
        while how_many > 0:
            actual_username = username + str(how_many) + "@hotmail.com"
            actual_email = email + str(how_many) + "@hotmail.com"
            actual_alias = alias + str(how_many)
            actual_lastname = lastname + str(how_many) + "Joe"
            sf.User.create({'userName': actual_username,
                            'Alias': actual_alias,
                            'Email': actual_email,
                            'lastName': actual_lastname,
                            'EmailEncodingKey': 'UTF-8',
                            'TimeZoneSidKey': 'America/New_York',
                            'LocaleSidKey': 'en_US',
                            'ProfileId': profile_id,
                            'LanguageLocaleKey': 'en_US'})
            print("User created. Now deactivating if not already deactivated.")
            deactivate_user(actual_username)
            how_many -= 1
    except Exception as e:
        print("Users created and deactivated, {}".format(e))
        pass


# Check if second Admin exists, if not create one, otherwise report license limitation
def create_admin2(username):
    """
    :param username:
    :return:
    """
    sysadmin_profile_id = get_profile_id(sysadmin_profile_name)
    try:
        sf.User.create({'userName': username,
                        'Alias': 'lsladm2',
                        'Email': 'lsladmin@yahoo.com',
                        'firstName': 'Doe',
                        'lastName': 'lsl-Admin2',
                        'EmailEncodingKey': 'UTF-8',
                        'TimeZoneSidKey': 'America/New_York',
                        'LocaleSidKey': 'en_US',
                        'ProfileId': sysadmin_profile_id,
                        'LanguageLocaleKey': 'en_US'})
        print("2nd Administrator user created with username: " + username + "\n")
    except Exception as e:
        print("\nWas not successful creating 2nd Administrator user. Are there enough licenses or could we deactivate" +
              "one for the purpose?\n\n")
        print("Exception was: {}".format(e))


# Deactivate a user if it exists
def deactivate_user(username):
    """
    :param username:
    :return:
    """
    userinfo = sf.query("SELECT IsActive FROM User WHERE username = '" + username + "'")
    itemlist = ((userinfo.values())[2])
    dict = collections.OrderedDict(userinfo)
    dictitems = list(dict.values())[2]
    if len(dictitems) == 0:
        print("Could not deactivate user. Maybe it does not exist? Continuing...\n")
        return None
    else:
        itemlist = (dictitems.pop())
        dict2 = collections.OrderedDict(itemlist)
        is_active = list(dict2.values())[1]
        if is_active:
            print("User " + username + " is active, deactivating.")
            uid = get_user_id(username)
            sf.User.update(uid, {'IsActive': 'false'})
        else:
            print("User is not active, deactivating not necessary.")
            pass


def create_mockup_account(owner, test_data):
    """
    :param owner:
    :param test_data:
    :return:
    """
    owner_id = get_user_id(owner)
    sf.Account.create({'type': 'Account',
                       'Name': '' + test_data + '',
                       'Website': 'http://www.IamJustAtestWebSite.com',
                       'owner_id': '' + owner_id + ''})
    print("\nSome mockup Account " + test_data + " for user: " + owner + " created.")


def get_profile_id(profile_name):
    """
    :param profile_name:
    :return:
    """
    query = sf.query("SELECT Id FROM Profile WHERE name = '" + profile_name + "'")
    dict = collections.OrderedDict(query)
    dictitems = list(dict.values())[2]
    if len(dictitems) == 0:
        print("Could not get System Administrator Profile Id. Continuing...\n")
        return None
    else:
        itemlist = (dictitems.pop())
        dict2 = collections.OrderedDict(itemlist)
        prof_id = list(dict2.values())[1]
        return prof_id


def get_admin_sid(username, password_with_token):
    """
    :param username:
    :param password_with_token:
    :return:
    """
    login_header = {
        'content-type': 'text/xml',
        'charset': 'UTF-8',
        'SOAPAction': 'login'
        }
    login_envelope = """
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
                 <urn:username>""" + username + """</urn:username>
                 <urn:password>""" + password_with_token + """</urn:password>
              </urn:login>
           </soapenv:Body>
        </soapenv:Envelope>
    """
    soap_response = requests.post(loginURL, login_envelope, headers=login_header)
    dom = xml.dom.minidom.parseString(soap_response.text)
    soap_result = dom.getElementsByTagName('sessionId')
    if soap_result[0].firstChild.nodeValue is None:
        print("\nI wasn't successful getting Admin Session ID. Error was:\n")
        print(soap_response.text + '\n')
    else:
        admin_sid = soap_result[0].firstChild.nodeValue
        print("Admin successfully logged in and got " + admin_sid + " session ID.\n")
        return admin_sid


def set_ip_range(profilename):
    """
    :param profilename:
    :return:
    """
    admin_sid = get_admin_sid(ADMIN1_USERNAME, ADMIN1_PTK)
    update_metadata_header = {
        'content-type': 'text/xml',
        'charset': 'UTF-8',
        'SOAPAction': 'updateMetadata'
        }
    update_metadata_envelope = """
        <env:Envelope xmlns:env="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchem
a-instance">
            <env:Header>
                <urn:SessionHeader xmlns:urn="http://soap.sforce.com/2006/04/metadata">
                    <urn:sessionId>""" + admin_sid + """</urn:sessionId>
                </urn:SessionHeader>
            </env:Header>
            <env:Body>
                <updateMetadata xmlns="http://soap.sforce.com/2006/04/metadata">
                    <metadata xsi:type="Profile">
                    <fullName>""" + profilename + """</fullName>
                       <loginIpRanges>
                          <endAddress>255.255.255.255</endAddress>
                          <startAddress>0.0.0.0</startAddress>
                       </loginIpRanges>
                    </metadata>
                </updateMetadata>
            </env:Body>
        </env:Envelope>
        """
    soap_response = requests.post(metadata_url, update_metadata_envelope, headers=update_metadata_header)
    dom = xml.dom.minidom.parseString(soap_response.text)
    soap_result = dom.getElementsByTagName('success')
    if len(soap_result) == 0:
        print("I've encountered an issue. Request response:\n")
        print(soap_response.text + "\n")
        return None
    else:
        if soap_result[0].firstChild.nodeValue:
            print("Login IP range successfully set.")
        else:
            print("I've encountered an issue. Request response:\n")
            print(soap_response.text + "\n")
            return None


if __name__ == "__main__":
    main()
