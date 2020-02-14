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
from Config.config_sfdc import *
from simple_salesforce import Salesforce

sf = Salesforce(username=ADMIN1_USERNAME, password=ADMIN1_PASSWORD, security_token=ADMIN1_TOKEN)


def main():
    # -----Admin 1--Getting global Administrator Session ID.
    admin_sid = get_user_sid(ADMIN1_USERNAME, ADMIN1_PTK)

    # Admin 1--Making sure we will be able to manipulate without any identification
    set_ip_range(sysadmin_profile_name, admin_sid)

    # -----Super-Admin-----
    # -----Admin 1--Because of weak lockout policy, it triggers
    # Security Control: Lockout effective period -super-admin
    change_lockout_period(admin_sid)

    # -----Admin 1--Disable clickjack protection for customer Visualforce pages with standard headers
    disable_clickjack_with_standard_headers(admin_sid)

    # -----Admin 1--Creating 4 users - due to license limitations,
    # the other 2 will be Force.com Free users.
    create_user(LSL_USER1_USERNAME, LSL_USER1_ALIAS, LSL_USER1_USERNAME, LSL_USER1_USERNAME, 'Standard Platform User')
    create_user(LSL_USER2_USERNAME, LSL_USER2_ALIAS, LSL_USER2_USERNAME, LSL_USER2_USERNAME, 'Force.com - Free User')
    create_user(LSL_USER3_USERNAME, LSL_USER3_ALIAS, LSL_USER3_USERNAME, LSL_USER3_USERNAME, 'Force.com - Free User')
    create_user(LSL_USER4_USERNAME, LSL_USER4_ALIAS, LSL_USER4_USERNAME, LSL_USER4_USERNAME, 'Force.com - App'
                                                                                             'Subscription User')

    # -----Admin 1--set IP range (for admin profile) - making sure we
    # will be able to manipulate without any identification
    set_ip_range(sysadmin_profile_name, admin_sid)

    # Path 1: Account compromise -- User1
    # -----User 1--brute force login, Attacker brute forced account successfully,
    # triggers Threat: Failed login(e.g. 5 average, 2x)
    switch_user_profile_or_role(LSL_USER1_USERNAME, 'System Administrator')

    # failUserLogins(SFDC_TEST_USER1, "X", num_failed_attempts)
    # -----User 1--Login from remote triggers UBA Risk User: High, activity from unseen browser,
    # device, OS, unseen location(including unseen IPs v2) (score approx: 45-50)
    # failUserLogins(SFDC_TEST_USER1, SFDC_TEST_USER1_PASSWORD, num_failed_attempts, tor_proxy_ip,
    # tor_proxy_port, "Mozilla/1.0 (Windows CE 0.1; Win63; x63; rv:1.1) GeckoX/20100101 Firebug/0.1")
    # -----User 1-----UBA Risk User: 10x High, Data export --- Instead of this,
    # Attacker set Trusted IP Range to enable backdoor access, triggers Policy alert.
    # To verify, in the UI this is at "Network Access"
    set_trusted_ip_range(howmany_trusted_ip_range_sets, 'lsl-TrustRange-' + random_string_generator(4), '192.168.0.11',
                         '192.168.0.200', LSL_USER1_USERNAME, default_user_password)
    switch_user_profile_or_role(LSL_USER1_USERNAME, 'Standard Platform User')

    # Path 2: Data exfiltration -- User2
    # -----User 2--Grant Admin permissions
    switch_user_profile_or_role(LSL_USER2_USERNAME, 'System Administrator')
    # -----User 2--60+(configurable) Mass Transfer to another account,
    # triggers UBA Risk User: Medium, Mass Transfer+After-hr.
    # Creating given numbers of mockup account data to have something to transfer.
    LSL_USER2_FULLNAME = get_user_full_name(LSL_USER2_USERNAME)
    admin1_full_name = get_user_full_name(ADMIN1_USERNAME)
    create_mockup_account(howManyMockupAccounts, ADMIN1_USERNAME)
    mass_transfer(LSL_USER2_USERNAME, default_user_password, admin1_full_name, LSL_USER2_FULLNAME,
                  how_many_mass_transfers)
    switch_user_profile_or_role(LSL_USER2_USERNAME, 'Force.com - Free User')

    # Path#3: Insider Threat--User3
    # -----User 3--Admin grant excessive permissions to insider user, triggers Policy alert:
    # Profile/Change user permissions
    switch_user_profile_or_role(LSL_USER3_USERNAME, 'System Administrator')

    # -----User 3--We deploy new Sharing Rules as an insider threat.
    # We have some static XML content and if we want to add multiple rules,
    # don't want to add the header all the time.
    # create some mockup sharing rules.
    create_zip_objects()
    add_lead_sharing_rule(how_many_sharing_rules, "Read")
    close_rules()
    deploy_zipfile(LSL_USER3_USERNAME, default_user_password)

    # -----User 3--3-Insider user is corrupted by a vendor, he helped vendor to extend
    # contract term, triggers Policy alert: Contract Create+Update
    response = create_mockup_contract(LSL_USER3_USERNAME, "lsl-Account-firstMockup", "3", "2016-03-01")
    update_contract(response['id'])

    # -----User 3--4-Before termination, insider user also Mass deleting data,
    # triggers UBA Risk User: High, Mass Delete
    for x in range(0, howManyMassDelete):
        create_mockup_account(howManyMockupAccounts, LSL_USER3_USERNAME)
        mass_delete(LSL_USER3_USERNAME, default_user_password)
        print("Mass Delete iteration nr.: " + str(x))

    # -----User 3--Policy alert: Change user profile
    switch_user_profile_or_role(LSL_USER3_USERNAME, 'Force.com - Free User')

    # Path 4: Insider Threat--User4
    # -----User 4--UBA Risk User: 20x Medium, Reports export, Report Run
    # 2 - The 3rd party has the permission to access sensitive data and function,
    #     he run and export the reports, sale to competitor, triggers UBA Risk User: Medium,
    #     Reports exported, Report Run
    # 3 - The 3rd party also export data, triggers UBA Risk User: High, Data Export
    # 4 - For all report activities by the 3rd party, stand out in KSI:
    # Top customer report run and Top customer report exported
    switch_user_profile_or_role(LSL_USER4_USERNAME, 'System Administrator')
    report_name = create_report(howManyReportsCreate, LSL_USER4_USERNAME, default_user_password, "Accounts")
    export_report(how_many_export_reports, report_name, LSL_USER4_USERNAME, default_user_password)
    switch_user_profile_or_role(LSL_USER4_USERNAME, 'Force.com - App Subscription User')


# Creating a user
def create_user(username, alias, email, last_name, profile_name):
    """
    :param username:
    :param alias:
    :param email:
    :param last_name:
    :param profile_name:
    :return:
    """
    profile_id = get_profile_id(profile_name)
    try:
        sf.User.create({'userName': username,
                        'Alias': alias,
                        'Email': email,
                        'lastName': last_name,
                        'EmailEncodingKey': 'UTF-8',
                        'TimeZoneSidKey': 'America/New_York',
                        'LocaleSidKey': 'en_US',
                        'profile_id': profile_id,
                        'LanguageLocaleKey': 'en_US'})
        set_password(username, default_user_password)
    except Exception as e:
        try:
            activate_user(username)
            set_password(username, default_user_password)
        except Exception as e:
            set_password(username, default_user_password)


def get_user_full_name(username):
    """
    :param username:
    :return:
    """
    userinfo = sf.query("SELECT FirstName, LastName FROM User WHERE username = '" + username + "'")
    dict = collections.OrderedDict(userinfo)
    dictitems = list(dict.values())[2]
    firstname = list(collections.OrderedDict(dictitems.pop()).values())[1]
    lastname = list(collections.OrderedDict(dictitems.pop()).values())[2]
    if firstname is None:
        fullname = lastname
    else:
        fullname = firstname + " " + lastname
    return fullname


# Resetting a user's password
def set_password(username, default_user_password):
    """
    :param username:
    :param default_user_password:
    :return:
    """
    uid = get_user_id(username)
    print("\nDefaulting Password for user with UID: " + uid + "\n")
    sf2 = beatbox.PythonClient()
    sf2.login(ADMIN1_USERNAME, ADMIN1_PASSWORD)
    try:
        sf2.setPassword(uid, default_user_password)
    except Exception as e:
        pass


# Login for all users, keep session Ids
def get_user_sid(username, password):
    """
    :param username:
    :param password:
    :return:
    """
    login_headers = {
        'content-type': 'text/xml',
        'charset': 'UTF-8',
        'SOAPAction': 'login'
        }
    login_envelope = """
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:urn="urn:enterprise.soap.sforce.com">
            <soapenv:Header>
            </soapenv:Header>
        <soapenv:Body>
            <urn:login>
                <urn:username>""" + '' + username + '' + """</urn:username>
                <urn:password>""" + '' + password + '' + """</urn:password>
            </urn:login>
        </soapenv:Body>
        </soapenv:Envelope>
    """
    login_response = requests.post(partnerURL, login_envelope, headers=login_headers)
    dom = xml.dom.minidom.parseString(login_response.text)
    user_sid_result = dom.getElementsByTagName('sessionId')
    if user_sid_result[0].firstChild.nodeValue is None:
        print("\nI wasn't successful. Error was:\n")
        print(login_response.text + '\n')
    else:
        user_sid = user_sid_result[0].firstChild.nodeValue
        return user_sid


# This is useful in general to manipulate any user's details
def get_user_id(username):
    """
    :param username:
    :return:
    """
    # Userinfo is an OrderedDict that contains a list that contains another OrderedDict so we need to dig in a bit.
    userinfo = sf.query("SELECT Id FROM User WHERE username = '" + username + "'")
    dict = collections.OrderedDict(userinfo)
    dictitems = list(dict.values())[2]
    itemlist = (dictitems.pop())
    dict2 = collections.OrderedDict(itemlist)
    uid = list(dict2.values())[1]
    return uid


def get_user_profile_id(which_user):
    """
    :param which_user:
    :return:
    """
    query = sf.query("SELECT ProfileId FROM User where username = '" + which_user + "'")
    dictitems = list(collections.OrderedDict(query).values())[2]
    if len(dictitems) == 0:
        print("Could not get System Administrator Profile Id. Continuing...\n")
        return None
    else:
        prof_id = list(collections.OrderedDict(dictitems.pop()).values())[1]
        return prof_id


def get_profile_id(profile_name):
    """
    :param profile_name:
    :return:
    """
    query = sf.query("SELECT Id FROM Profile WHERE name = '" + profile_name + "'")
    dictitems = list(collections.OrderedDict(query).values())[2]
    if len(dictitems) == 0:
        print("Could not get System Administrator Profile Id. Continuing...\n")
        return None
    else:
        prof_id = list(collections.OrderedDict(dictitems.pop()).values())[1]
        return prof_id


def switch_user_profile_or_role(user1, user1_profile, user2_profile=None, how_many_times=None):
    """
    :param user1:
    :param user1_profile:
    :param user2_profile:
    :param how_many_times:
    :return:
    """
    if how_many_times is None:
        user_id = get_user_id(user1)
        switch_to_profile_id = get_profile_id(user1_profile)
        sf.User.update(user_id, {'ProfileId': '' + switch_to_profile_id + ''})
    else:
        while how_many_times > 0:
            user_id = get_user_id(user1)
            get_user_profile_id(user1)
            switch_between1 = get_profile_id(user1_profile)
            switch_between2 = get_profile_id(user2_profile)
            sf.User.update(user_id, {'ProfileId': '' + switch_between2 + ''})
            print("The " + user1 + "'s profile switched from " + switch_between1 + " to " + switch_between2 +
                  " Profile Id.")
            get_user_profile_id(user1)
            sf.User.update(user_id, {'ProfileId': '' + switch_between1 + ''})
            print("The " + user1 + "'s profile switched from " + switch_between2 + " to " + switch_between1 +
                  " Profile Id.")
            print("UserProfile switches left: " + str(how_many_times - 1))
            how_many_times -= 1


# Reactivate a user if existing
def activate_user(username):
    """
    :param username:
    :return:
    """
    userinfo = sf.query("SELECT IsActive FROM User WHERE username = '" + username + "'")
    itemlist = (userinfo.values())[2]
    dictitems = list(collections.OrderedDict(userinfo).values())[2]
    is_active = list(collections.OrderedDict(dictitems.pop()).values())[1]
    if not is_active:
        print("User exists, but is not active. Activating.")
        sf.User.update(get_user_id(username), {'IsActive': 'true'})
    else:
        print("User is active, no need to re-enable.")


def create_mockup_account(how_many, owner):
    """
    :param how_many:
    :param owner:
    :return:
    """
    owner_id = get_user_id(owner)
    sf.Account.create({'type': 'Account',
                               'Name': 'lsl-Account-firstMockup',
                               'Website': 'http://www.IamJustAtestWebSite.com',
                               'owner_id': '' + owner_id + ''})
    acc_list = ['lsl-Account-firstMockup']
    how_many -= 1
    while how_many > 0:
        test_data = "lsl-Account-" + random_string_generator(8)
        owner_id = get_user_id(owner)
        sf.Account.create({'type': 'Account',
                           'Name': '' + test_data + '',
                           'Website': 'http://www.IamJustAtestWebSite.com',
                           'owner_id': '' + owner_id + ''})
        print("Some mockup Account " + test_data + " for user: " + owner + " created.")
        acc_list.append(test_data)
        how_many -= 1
    print("Following mockup Accounts have been created: " + str(acc_list))
    return acc_list


def get_account_id(account_name):
    """
    :param account_name:
    :return:
    """
    userinfo = sf.query("SELECT Id FROM Account WHERE Name = '" + account_name + "'")
    acc_id = list(collections.OrderedDict(list(collections.OrderedDict(userinfo).values())[2].pop()).values())[1]
    return acc_id


def create_mockup_contract(owner, account_name, contract_term, start_date):
    """
    :param owner:
    :param account_name:
    :param contract_term:
    :param start_date:
    :return:
    """
    account_id = get_account_id(account_name)
    data1 = sf.Contract.create({'AccountId': account_id,
                                'ContractTerm': contract_term,
                                'StartDate': start_date,
                                'owner_id': get_user_id(owner)})
    print("Mockup contract for Account " + account_id + " created.")
    return data1


def update_contract(user_id):
    """
    :param user_id:
    :return:
    """
    sf.Contract.update(user_id, {'ContractTerm': '75'})


def set_ip_range(profile_name, admin_sid):
    """
    :param profile_name:
    :param admin_sid:
    :return:
    """
    update_metadata_envelope = """
        <env:Envelope xmlns:env="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <env:Header>
                <urn:SessionHeader xmlns:urn="http://soap.sforce.com/2006/04/metadata">
                    <urn:sessionId>""" + admin_sid + """</urn:sessionId>
                </urn:SessionHeader>
            </env:Header>
            <env:Body>
                <updateMetadata xmlns="http://soap.sforce.com/2006/04/metadata">
                    <metadata xsi:type="Profile">
                    <fullName>""" + profile_name + """</fullName>
                       <loginIpRanges>
                          <endAddress>255.255.255.255</endAddress>
                          <startAddress>0.0.0.0</startAddress>
                       </loginIpRanges>
                    </metadata>
                </updateMetadata>
            </env:Body>
        </env:Envelope>
        """

    soap_response = requests.post(metadata_url, update_metadata_envelope, headers=updateMetadataHeader)
    dom = xml.dom.minidom.parseString(soap_response.text)
    result_element = dom.getElementsByTagName('success')
    result_value = result_element[0].firstChild.nodeValue
    if len(result_value) == 0:
        print("I've encountered an issue. Request response:\n")
        print(soap_response.text + "\n")
        return None
    else:
        if result_element[0].firstChild.nodeValue:
            print("Login IP range successfully set.")
        else:
            print("I've encountered an issue. Request response:\n")
            print(soap_response.text + "\n")
            return None


def change_lockout_period(admin_sid):
    """
    :param admin_sid:
    :return:
    """
    soap_body = """
    <env:Envelope xmlns:env="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <env:Header>
            <urn:SessionHeader xmlns:urn="http://soap.sforce.com/2006/04/metadata">
                <urn:sessionId>""" + admin_sid + """</urn:sessionId>
            </urn:SessionHeader>
        </env:Header>
        <env:Body>
            <updateMetadata xmlns="http://soap.sforce.com/2006/04/metadata">
                <metadata xsi:type="SecuritySettings">
                <fullName>*</fullName>
                <passwordPolicies>
                      <lockoutInterval>""" + lockout_interval + """</lockoutInterval>
                   </passwordPolicies>
                </metadata>
            </updateMetadata>
        </env:Body>
    </env:Envelope>
    """
    soap_result = requests.post(metadata_url, soap_body, headers=updateMetadataHeader)
    dom = xml.dom.minidom.parseString(soap_result.text)
    result_element = dom.getElementsByTagName('success')
    result_value = result_element[0].firstChild.nodeValue
    if len(result_value) == 0:
        print("I've encountered an issue. Request response:\n")
        print(soap_result.text + "\n")
        return None
    else:
        if result_element[0].firstChild.nodeValue:
            print("New Lockout time successfully set.")
        else:
            print("I've encountered an issue. Request response:\n")
            print(soap_result.text + "\n")
            return None


def disable_clickjack_with_standard_headers(admin_sid):
    """
    :param admin_sid:
    :return:
    """
    soap_body = """
    <env:Envelope xmlns:env="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <env:Header>
            <urn:SessionHeader xmlns:urn="http://soap.sforce.com/2006/04/metadata">
                <urn:sessionId>""" + admin_sid + """</urn:sessionId>
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
    soap_result = requests.post(metadata_url, soap_body, headers=updateMetadataHeader)

    dom = xml.dom.minidom.parseString(soap_result.text)
    result_element = dom.getElementsByTagName('success')
    result_value = result_element[0].firstChild.nodeValue
    if len(result_value) == 0:
        print("I've encountered an issue. Request response:\n")
        print(soap_result.text + "\n")
        return None
    else:
        if result_element[0].firstChild.nodeValue:
            print("Successfully disabled clickjack protection for customer Visualforce pages with standard headers.")
        else:
            print("I've encountered an issue. Request response:\n")
            print(soap_result.text + "\n")
            return None


def random_string_generator(nr):
    """
    :param nr:
    :return:
    """
    rand_string = (''.join(choice(ascii_lowercase) for i in range(nr)))
    return rand_string


def create_zip_objects():
    """
    :return:
    """
    if not os.path.exists(os.path.dirname(rulefile)):
        try:
            os.makedirs(os.path.dirname(rulefile))
        except Exception as e:
            pass
    with open(rulefile, "w") as f:
        f.write("""<?xml version="1.0" encoding="UTF-8"?>
<SharingRules xmlns="http://soap.sforce.com/2006/04/metadata">""" + "\n")
    with open('./tmp/unpackaged/package.xml', "w") as f:
        f.write("""<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>*</members>
        <name>SharingRules</name>
    </types>
    <version>35.0</version>
</Package>""" + "\n")


def add_lead_sharing_rule(how_many, access_level):
    """
    :param how_many:
    :param access_level:
    :return:
    """
    while how_many > 0:
        full_name = "lsl_" + random_string_generator(4)
        label = "lsl-" + random_string_generator(5)
        with open(rulefile, "a") as f:
            f.write("""     <sharingOwnerRules>
                <full_name>""" + full_name + """</full_name>
                <accessLevel>""" + access_level + """</accessLevel>
                <label>""" + label + """</label>
                <sharedTo>
                    <allInternalUsers></allInternalUsers>
                </sharedTo>
                <sharedFrom>
                    <allInternalUsers></allInternalUsers>
                </sharedFrom>
            </sharingOwnerRules>""" + "\n")
            print("Lead sharing rule with label: " + label + " successfully created.")
            how_many -= 1


def close_rules():
    with open(rulefile, "a+") as f:
        f.write("""</SharingRules>""" + "\n")


def get_report_id(report_name, as_user, as_password):
    """
    :param report_name:
    :param as_user:
    :param as_password:
    :return:
    """
    user_sid = get_user_sid(as_user, as_password)
    sf2 = Salesforce(instance_url=instanceURL, session_id=user_sid)
    query = sf2.query("SELECT Id FROM Report WHERE Name = '" + report_name + "'")
    dictitems = list(collections.OrderedDict(query).values())[2]
    report_id = list(collections.OrderedDict(dictitems.pop()).values())[1]
    if len(collections.OrderedDict(dictitems.pop())) == 0:
        print("Could not get report_id.\n")
        return None
    else:
        return report_id, user_sid


def export_report(how_many, report_name, as_user, as_password):
    """
    :param how_many:
    :param report_name:
    :param as_user:
    :param as_password:
    :return:
    """
    (report_id, user_sid) = get_report_id(report_name, as_user, as_password)
    while how_many > 0:
        response = requests.get(instanceURL + "/" + report_id + "?view=d&snip&export=1&enc=UTF-8&excel=1",
                                headers=sf.headers, cookies={'sid': user_sid})
        f = open("lsl-report-" + random_string_generator(4) + ".csv", 'w')
        f.write(response.text)
        f.close()
        how_many -= 1


def deploy_zipfile(as_user, as_password):
    """
    :param as_user:
    :param as_password:
    :return:
    """
    user_sid = get_user_sid(as_user, as_password)
    new_zip = zipfile.ZipFile(packageZipFile, "w")
    dir_path = './tmp'
    len_dir_path = len(dir_path)
    for root, _, files in os.walk(dir_path):
        for file in files:
            file_path = os.path.join(root, file)
            new_zip.write(file_path, file_path[len_dir_path:])
    new_zip.close()
    with open(packageZipFile, "rb") as f:
        bytes_read = f.read()
        encoded = base64.b64encode(bytes_read)
        b64code = encoded.decode("utf-8")

    deploy_headers = {
            'content-type': 'text/xml',
            'charset': 'UTF-8',
            'SOAPAction': 'deploy'
    }
    deploy_body = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:met="http://soap.sforce.com/2006/04/metadata">
        <soapenv:Header>
          <met:SessionHeader>
                <sessionId>""" + user_sid + """</sessionId>
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

    soap_result = requests.post(metadata_url, deploy_body, headers=deploy_headers)

    dom = xml.dom.minidom.parseString(soap_result.text)
    result_element = dom.getElementsByTagName('id')
    result_value = result_element[0].firstChild.nodeValue
    if len(result_value) == 0:
        print("I've encountered an issue. Request response:\n")
        print(soap_result.text + "\n")
        return None
    else:
        if result_element[0].firstChild.nodeValue:
            print("Got deployment ID.")
            did = result_element[0].firstChild.nodeValue
        else:
            print("I've encountered an issue. Request response:\n")
            print(soap_result.text + "\n")
            return None
    time.sleep(2)

    check_deploy_headers = {
            'content-type': 'text/xml',
            'charset': 'UTF-8',
            'SOAPAction': 'checkDeployStatus'
    }
    check_deploy_status = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:met="http://soap.sforce.com/2006/04/metadata">
       <soapenv:Header>
          <met:SessionHeader>
                <sessionId>""" + user_sid + """</sessionId>
          </met:SessionHeader>
       </soapenv:Header>
       <soapenv:Body>
          <met:checkDeployStatus>
             <met:asyncProcessId>""" + did + """</met:asyncProcessId>
             <met:includeDetails>true</met:includeDetails>
          </met:checkDeployStatus>
       </soapenv:Body>
    </soapenv:Envelope>"""

    soap_result = requests.post(metadata_url, check_deploy_status, headers=check_deploy_headers)
    dom = xml.dom.minidom.parseString(soap_result.text)
    result_element = dom.getElementsByTagName('status')
    result_value = result_element[0].firstChild.nodeValue
    if len(result_value) == 0:
        print("I've encountered an issue. Request response:\n")
        print(soap_result.text + "\n")
        return None
    else:
        if result_element[0].firstChild.nodeValue == 'Succeeded':
            print("Deployment succeeded.")
        else:
            print("I've encountered an issue. Request response:\n")
            print(soap_result.text + "\n")
            return None


# UBA Risk User: 10x High, Set Trusted IP range.
def set_trusted_ip_range(count, description, start_ip, end_ip, owner, password):
    """
    :param count:
    :param description:
    :param start_ip:
    :param end_ip:
    :param owner:
    :param password:
    :return:
    """
    user_sid = get_user_sid(owner, password)
    soap_body_part1 = """
        <env:Envelope xmlns:env="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <env:Header>
                <urn:SessionHeader xmlns:urn="http://soap.sforce.com/2006/04/metadata">
                    <urn:sessionId>""" + user_sid + """</urn:sessionId>
                    </urn:SessionHeader>
            </env:Header>
            <env:Body>
                <updateMetadata xmlns="http://soap.sforce.com/2006/04/metadata">
                <metadata xsi:type="SecuritySettings">
                <fullName>*</fullName>
                <networkAccess>"""
    soap_body_part2 = """
                    </networkAccess>
                </metadata>
                </updateMetadata>
            </env:Body>
        </env:Envelope>
        """
    while count > 0:
        ip_range = """
            <ipRanges>
            <description>""" + description + """</description>
                <start>""" + start_ip + """</start>
                <end>""" + end_ip + """</end>
            </ipRanges>"""
        requests.post(metadata_url, soap_body_part1 + ip_range + soap_body_part2, headers=updateMetadataHeader)
        print("Added trusted IP Range " + str(count) + " time(s).")
        requests.post(metadata_url, soap_body_part1 + soap_body_part2, headers=updateMetadataHeader)
        print("Deleted trusted IP Ranges " + str(count) + " times.")
        count -= 1


if __name__ == "__main__":
    main()
