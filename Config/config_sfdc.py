"""External configuration data"""
ADMIN1_USERNAME = "xy@yahoo.ca"
ADMIN1_PASSWORD = "xyz"
ADMIN1_TOKEN = "xyzhO1eSc4L3tIKL"
ADMIN1_PTK = ADMIN1_PASSWORD+ADMIN1_TOKEN

LSL_USER1_LASTNAME = "lsl-testuser1"
LSL_USER1_USERNAME = LSL_USER1_LASTNAME+"@yahoo.com"
LSL_USER1_ALIAS = "lsl-usr1"

LSL_USER2_LASTNAME = "lsl-testuser2"
LSL_USER2_USERNAME = LSL_USER2_LASTNAME+"@yahoo.com"
LSL_USER2_ALIAS = "lsl-usr2"

LSL_USER3_LASTNAME = "lsl-testuser3"
LSL_USER3_USERNAME = LSL_USER3_LASTNAME+"@yahoo.com"
LSL_USER3_ALIAS = "lsl-usr3"

LSL_USER4_LASTNAME = "lsl-testuser4"
LSL_USER4_USERNAME = LSL_USER4_LASTNAME+"@yahoo.com"
LSL_USER4_ALIAS = "lsl-usr4"

sysadmin_profile_name = 'Admin'
default_user_password = 'W4terPwd'

loginURL = 'https://login.salesforce.com'
partnerURL = loginURL+'/services/Soap/c/35.0'
instanceURL = 'https://na24.salesforce.com'
metadata_url = instanceURL + '/services/Soap/m/35.0'

rulefile = './tmp/unpackaged/sharingRules/Lead.sharingRules'
packageZipFile = './deploy.zip'

tokyo_proxy_ip = '54.169.26.12'
tokyo_proxy_port = 8888

tor_proxy_ip = 'localhost'
tor_proxy_port = 8118

# SFDC_TEST_USER1='xy@outlook.com'
# SFDC_TEST_USER1_PASSWORD='Password123'

updateMetadataHeader = {
        'content-type': 'text/xml',
        'charset': 'UTF-8',
        'SOAPAction': 'updateMetadata'
        }

num_failed_attempts = 20
# howManyUsersToCreateAndDeactivate = 30
howmany_trusted_ip_range_sets = 30
how_many_sharing_rules = 30
howManyMassDelete = 15
howManyMockupAccounts = 30
howManyProfileSwitches = 30
howManyReportsCreate = 30
how_many_export_reports = 30
how_many_mass_transfers = 15
lockout_interval = 'ThirtyMinutes'
