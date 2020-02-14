from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec


class AwsUIActions:
    def __init__(self, user_name=None,
                 password=None,
                 proxy=0,
                 proxy_ip=None,
                 proxy_port=None,
                 user_agent=None,
                 download_dir="c:\\tmp"):
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
        count = number_of_failed_attempts
        while count > 0:
            driver.get("https://login.salesforce.com/")
            elem = wait.until(ec.presence_of_element_located((By.ID, "username")))
            elem.send_keys(self.user_name)
            elem = wait.until(ec.presence_of_element_located((By.ID, "password")))
            elem.send_keys(self.password)
            elem.send_keys(Keys.RETURN)
            print("trying..."+str(count))
            count -= 1

    def teardown(self):
        self.driver.close()

    def mass_transfer(self, as_user_login, as_user_password, transfer_from, transfer_to, number_of_transfers):
        """
        :param as_user_login:
        :param as_user_password:
        :param transfer_from:
        :param transfer_to:
        :param number_of_transfers:
        :return:
        """
        driver = self.driver
        wait = WebDriverWait(driver, 20)
        self.login_attempt(as_user_login, as_user_password, 1)
        try:
            # Either we get a mandatory password changing window
            wait.until(ec.presence_of_element_located((By.ID, "cancel-button")))
            pass
        except Exception as e:
            try:
                # Or we get a register our cell phone window
                wait.until(driver.find_element_by_id((By.NAME,"save")))
                pass
            except Exception as e:
                # Or we get a home site which is good but we have to make sure.
                wait.until(ec.presence_of_element_located((By.ID, "setupLink")))
                pass
        driver.get("https://na24.salesforce.com/p/own/BulkTransfer?ent=Account")
        count = number_of_transfers
        while count > 0:
            elem = wait.until(ec.presence_of_element_located((By.ID, "newOwn")))
            elem.click()
            elem.send_keys(Keys.CONTROL+"a")
            elem.send_keys(Keys.DELETE)
            elem.send_keys(transfer_to)
            elem = driver.find_element_by_name("find")
            elem.click()
            elem = wait.until(ec.presence_of_element_located((By.ID, "allBox")))
            elem.click()
            elem = driver.find_element_by_name("save")
            elem.click()
            print("Mass Transfer from " + transfer_from + " to " + transfer_to + " is done.\nMass transfer nr.: " +
                  str(count) + "\n")
            count -= 1
            elem = wait.until(ec.presence_of_element_located((By.ID, "newOwn")))
            elem.click()
            elem.send_keys(Keys.CONTROL + "a")
            elem.send_keys(Keys.DELETE)
            elem.send_keys(transfer_from)
            elem = driver.find_element_by_name("find")
            elem.click()
            elem = wait.until(ec.presence_of_element_located((By.ID, "allBox")))
            elem.click()
            elem = driver.find_element_by_name("save")
            elem.click()
            print("Mass Transfer from " + transfer_to + " to " + transfer_from + " is done.\nMass transfer nr.: " +
                  str(count) + "\n")
            count -= 1
        print("Done with the mass transfers.")


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
            # Same login test via Singapore proxy
            print("Start failed login via Proxy...")
            a_acct = AwsUIActions(username, proxy=1, proxy_ip=proxy_ip, proxy_port=proxy_port, user_agent=user_agent)
            a_acct.login_attempt(password=password, number_of_failed_attempts=number_of_failed_attempts)
        finally:
            if a_acct:
                a_acct.teardown()

# failed_user_logins("xyx@yahoo.ca", "pass123", 1)


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
