from random import choice
from string import ascii_lowercase
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec


class AwsUIActions:
    def __init__(self,
                 user_name=None,
                 password=None,
                 proxy=0,
                 proxy_ip=None,
                 proxy_port=None,
                 user_agent=None,
                 download_dir="C:\\tmp"):
        firefox_profile = webdriver.FirefoxProfile()
        firefox_profile.set_preference('services.sync.prefs.sync.privacy.clearOnShutdown.cookies', False)
        firefox_profile.set_preference('browser.download.useDownloadDir', True)
        firefox_profile.set_preference('browser.download.folderList', 2)
        firefox_profile.set_preference('browser.download.dir', download_dir)
        firefox_profile.set_preference('browser.download.manager.showWhenStarting', False)
        firefox_profile.set_preference('browser.helperApps.neverAsk.saveToDisk', "application/csv, text/csv")
        firefox_profile.set_preference('browser.helperApps.neverAsk.openFile', "application/csv, text/csv")
        if proxy == 1:
            firefox_profile.set_preference('network.proxy.type', proxy)
            firefox_profile.set_preference('network.proxy.http', proxy_ip)
            firefox_profile.set_preference('network.proxy.http_port', proxy_port)
            firefox_profile.set_preference('network.proxy.ssl', proxy_ip)
            firefox_profile.set_preference('network.proxy.ssl_port', proxy_port)
        if user_agent:
            firefox_profile.set_preference("general.useragent.override", user_agent)

        self.driver = webdriver.Firefox(firefox_profile)
        self.user_name = user_name
        self.password = password

    def login_attempt(self, user_name=None, password=None, number_of_failed_attempts=0):
        """
        :param user_name:
        :param password:
        :param number_of_failed_attempts:
        :return:
        """
        self.user_name = user_name if user_name is not None else self.user_name
        self.password = password if password is not None else self.password
        driver = self.driver
        wait = WebDriverWait(driver, 60)
        driver.get("https://login.salesforce.com/")
        count = number_of_failed_attempts
        while count > 0:
            (wait.until(ec.presence_of_element_located((By.ID, "username")))).send_keys(self.user_name)
            elem = wait.until(ec.presence_of_element_located((By.ID, "password")))
            elem.send_keys(self.password)
            elem.send_keys(Keys.RETURN)
            print("Trying login nr.: " + str(count))
            count -= 1

    def teardown(self):
        """
        :return:
        """
        self.driver.close()

    # Mass Delete is achievable via Selenium
    def mass_delete(self, as_user_login, as_user_password):
        """
        :param as_user_login:
        :param as_user_password:
        :return:
        """
        driver = self.driver
        wait = WebDriverWait(driver, 30)
        self.login_attempt(as_user_login, as_user_password, 1)
        try:
            wait.until(ec.presence_of_element_located((By.ID, "cancel-button")))
            pass
        except Exception as e:
            try:
                wait.until(driver.find_element_by_id((By.NAME, "save")))
                pass
            except Exception as e:
                wait.until(ec.presence_of_element_located((By.ID, "setupLink")))
                pass
        driver.get("https://na24.salesforce.com/setup/own/massdelete.jsp?ftype=a&retURL=%2Fui%2Fsetup" +
                   "%2Fown%2FMassDeleteSelectPage%3Fsetupid%3DDataManagementDelete%26retURL%3D%252Fui%252F" +
                   "setup%252FSetup%253Fsetupid%253DDataManagement")
        (wait.until(ec.presence_of_element_located((By.NAME, "find")))).click()
        (wait.until(ec.presence_of_element_located((By.ID, "closed_opp")))).click()
        (driver.find_element_by_id("owner_opp")).click()
        (wait.until(ec.presence_of_element_located((By.ID, "allBox")))).click()
        (wait.until(ec.presence_of_element_located((By.NAME, "save")))).click()

    def mass_transfer(self, as_user_login, as_user_pass, transfer_from, transfer_to, number_of_transfers):
        """
        :param as_user_login:
        :param as_user_pass:
        :param transfer_from:
        :param transfer_to:
        :param number_of_transfers:
        :return:
        """
        driver = self.driver
        wait = WebDriverWait(driver, 15)
        self.login_attempt(as_user_login, as_user_pass, 1)
        # If we have to change password, the first screen that appears only contains the "Cancel" button.
        try:
            wait.until(ec.presence_of_element_located((By.ID, "cancel-button")))
            pass
        except Exception as e:
            # If we already changed our password, the screen that appears wants to add a cell phone number for
            # password recovery.
            try:
                wait.until(driver.find_element_by_id((By.NAME, "save")))
                pass
            # Otherwise, we can see the SETUP link.
            except Exception as e:
                wait.until(ec.presence_of_element_located((By.ID, "setupLink")))
                pass
        driver.get("https://na24.salesforce.com/p/own/BulkTransfer?ent=Account")
        count = number_of_transfers
        while count > 0:
            elem = wait.until(ec.presence_of_element_located((By.ID, "newOwn")))
            elem.send_keys(Keys.CONTROL + "a")
            elem.send_keys(Keys.DELETE)
            elem.send_keys(transfer_to)
            (driver.find_element_by_name("find")).click()
            (wait.until(ec.presence_of_element_located((By.ID, "allBox")))).click()
            (driver.find_element_by_name("save")).click()
            print("Done with mass transfer from " + transfer_from + " to " + transfer_to + ".\nMass transfer nr.: " + str(count) +
                  "\n")
            count -= 1
            elem = wait.until(ec.presence_of_element_located((By.ID, "newOwn")))
            elem.send_keys(Keys.CONTROL + "a")
            elem.send_keys(Keys.DELETE)
            elem.send_keys(transfer_from)
            (driver.find_element_by_name("find")).click()
            (wait.until(ec.presence_of_element_located((By.ID, "allBox")))).click()
            (driver.find_element_by_name("save")).click()
            print("Mass Transfer from " + transfer_to + " to " + transfer_from + " is done.\nMass transfer nr.: " + str(count) +
                  "\n")
            count -= 1
        print("Done with mass transfer " + str(number_of_transfers) + " times.")
    
    def create_report(self, how_many, username, password, which_object):
        """
        :param how_many:
        :param username:
        :param password:
        :param which_object:
        :return:
        """
        driver = self.driver
        wait = WebDriverWait(driver, 15)
        self.login_attempt(username, password, 1)
        # If we have to change password, the first screen that appears only contains the "Cancel" button.
        try:
            wait.until(ec.presence_of_element_located((By.ID, "cancel-button")))
            pass
        except Exception as e:
            # If we already changed our password, the screen that appears wants to add a cell phone number for
            # password recovery.
            try:
                wait.until(driver.find_element_by_id((By.NAME, "save")))
                pass
            # Otherwise, we can see the SETUP link.
            except Exception as e:
                wait.until(ec.presence_of_element_located((By.ID, "setupLink")))
                pass
        count = how_many
        report_name = ""
        while count > 0:
            if (count == how_many):
                first_run = True
            else:
                first_run = False
            driver.get("https://na24.salesforce.com/reportbuilder/reportType.apexp")
            elem = wait.until(ec.presence_of_element_located((By.ID, "quickFindInput")))
            elem.send_keys(which_object)
            elem.send_keys(Keys.ENTER)
            (driver.find_element_by_id("thePage:rtForm:createButton")).click()
            (wait.until(ec.presence_of_element_located((By.ID, "ext-gen63")))).click()
            (wait.until(ec.presence_of_element_located((By.NAME, "memorizenew")))).click()

            if first_run is True:
                report_name = "lsl-Report-"+(''.join(choice(ascii_lowercase) for i in range(5)))
                # We generate a random name after the common "lsl-Report-" prefix but we store the first one's name.
                # The dashes for the Report unique name will be automatically replaced with an underscore by Salesforce.
                (wait.until(ec.presence_of_element_located((By.ID, "report_name")))).send_keys(report_name)
                (driver.find_element_by_id("devName")).click()
                (driver.find_element_by_name("saveas")).click()
                count -= 1
            else:
                (wait.until(ec.presence_of_element_located((By.ID, "report_name")))).\
                    send_keys("lsl-Report-" + (''.join(choice(ascii_lowercase) for i in range(5))))
                (driver.find_element_by_name("saveas")).click()
                count -= 1
        print("Done with creating " + str(how_many) + " reports.")
        return report_name


def failed_user_logins(username, password, number_of_failed_attempts, proxy_ip=None, proxy_port=None, user_agent=None):
    """
    :param username:
    :param password:
    :param number_of_failed_attempts:
    :param proxy_ip:
    :param proxy_port:
    :param user_agent:
    :return:
    """
    a_acct = None
    if not proxy_ip:
        try:
            print("Start failed login...")
            a_acct = AwsUIActions(username)
            a_acct.login_attempt(password=password, number_of_failed_attempts=number_of_failed_attempts)
        finally:
            if a_acct:
                a_acct.teardown()
    else:
        try:
            # same login test via Singapore proxy
            print("Start failed login via Proxy...")
            a_acct = AwsUIActions(username, proxy=1, proxy_ip=proxy_ip, proxy_port=proxy_port, user_agent=user_agent)
            a_acct.login_attempt(password=password, number_of_failed_attempts=number_of_failed_attempts)
        finally:
            if a_acct:
                a_acct.teardown()


def mass_delete(username, password):
    """
    :param username:
    :param password:
    :return:
    """
    c = AwsUIActions()
    c.mass_delete(username, password)
    c.teardown()


def mass_transfer(username, password, transfer_from, transfer_to, number_of_transfers):
    """
    :param username:
    :param password:
    :param transfer_from:
    :param transfer_to:
    :param number_of_transfers:
    :return:
    """
    c = AwsUIActions()
    c.mass_transfer(username, password, transfer_from, transfer_to, number_of_transfers)
    c.teardown()


def create_report(how_many, username, password, which_object):
    """
    :param how_many:
    :param username:
    :param password:
    :param which_object:
    :return:
    """
    c = AwsUIActions()
    report_name = c.create_report(how_many, username, password, which_object)
    c.teardown()
    return report_name
