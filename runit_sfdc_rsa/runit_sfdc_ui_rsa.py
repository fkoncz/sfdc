from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

class AwsUIActions():

    def __init__(self, user_name=None,
                 password=None, proxy=0, proxy_ip=None, proxy_port=None,
                 useragent=None, download_dir="c:/tmp"):
        firefoxProfile = webdriver.FirefoxProfile()
        firefoxProfile.set_preference('services.sync.prefs.sync.privacy.clearOnShutdown.cookies', False)
        firefoxProfile.set_preference('browser.download.useDownloadDir', True)
        firefoxProfile.set_preference('browser.download.folderList', 2)
        firefoxProfile.set_preference('browser.download.dir', download_dir)
        firefoxProfile.set_preference('browser.download.manager.showWhenStarting', False)
        firefoxProfile.set_preference('browser.helperApps.neverAsk.saveToDisk', "application/csv, text/csv")
        firefoxProfile.set_preference('browser.helperApps.neverAsk.openFile', "application/csv, text/csv")
        if proxy == 1:
            firefoxProfile.set_preference('network.proxy.type', proxy)
            firefoxProfile.set_preference('network.proxy.http', proxy_ip)
            firefoxProfile.set_preference('network.proxy.http_port', proxy_port)
            firefoxProfile.set_preference('network.proxy.ssl', proxy_ip)
            firefoxProfile.set_preference('network.proxy.ssl_port', proxy_port)

        if useragent:
                firefoxProfile.set_preference("general.useragent.override", useragent)

        self.driver = webdriver.Firefox(firefoxProfile)
        self.user_name = user_name
        self.password = password

    def loginAttempt(self, user_name=None, password=None, numFailedAttempts=0):
        self.user_name = user_name if user_name != None else self.user_name
        self.password = password if password != None else self.password
        driver = self.driver
        wait = WebDriverWait(driver, 60)
        count = numFailedAttempts
        while count > 0:
            driver.get("https://login.salesforce.com/")
            elem = wait.until(EC.presence_of_element_located((By.ID,"username")))
            elem.send_keys(self.user_name)
            elem = wait.until(EC.presence_of_element_located((By.ID,"password")))
            elem.send_keys(self.password)
            elem.send_keys(Keys.RETURN)
            print("trying..."+str(count))
            count -= 1

    def tearDown(self):
        self.driver.close()

    def massTransfer(self, asUserLogin, asUserPass, transferFrom, transferTo, numberOfTransfers):
        driver = self.driver
        wait = WebDriverWait(driver, 20)
        self.loginAttempt(asUserLogin, asUserPass, 1)
        try:
            #Either we get a mandatory password changing window
            wait.until(EC.presence_of_element_located((By.ID,"cancel-button")))
            pass
        except:
            try:
                #Or we get a register our cell phone window
                wait.until(driver.find_element_by_id((By.NAME,"save")))
                pass
            except:
                #Or we get a home site which is good but we have to make sure.
                wait.until(EC.presence_of_element_located((By.ID,"setupLink")))
                pass
        driver.get("https://na24.salesforce.com/p/own/BulkTransfer?ent=Account")
        count = numberOfTransfers
        while count > 0:
            elem = wait.until(EC.presence_of_element_located((By.ID,"newOwn")))
            elem.click()
            elem.send_keys(Keys.CONTROL+"a")
            elem.send_keys(Keys.DELETE)
            elem.send_keys(transferTo)
            elem = driver.find_element_by_name("find")
            elem.click()
            elem = wait.until(EC.presence_of_element_located((By.ID,"allBox")))
            elem.click()
            elem = driver.find_element_by_name("save")
            elem.click()
            print("Mass Transfer from "+transferFrom+" to "+transferTo+" is done.\nMass transfer nr.: "+str(count)+"\n")
            count -= 1
            elem = wait.until(EC.presence_of_element_located((By.ID,"newOwn")))
            elem.click()
            elem.send_keys(Keys.CONTROL+"a")
            elem.send_keys(Keys.DELETE)
            elem.send_keys(transferFrom)
            elem = driver.find_element_by_name("find")
            elem.click()
            elem = wait.until(EC.presence_of_element_located((By.ID,"allBox")))
            elem.click()
            elem = driver.find_element_by_name("save")
            elem.click()
            print("Mass Transfer from "+transferTo+" to "+transferFrom+" is done.\nMass transfer nr.: "+str(count)+"\n")
            count -= 1
        print("Done with the mass transfers.")


def failUserLogins(user_name, password, numFailedAttempts, proxy_ip=None, proxy_port=None, useragent=None):
    aAcct = None
    if not proxy_ip:
            try:
                    print("Start failed login...")
                    aAcct = AwsUIActions(user_name)
                    aAcct.loginAttempt(password=password, numFailedAttempts=numFailedAttempts)
            finally:
                if aAcct:
                        aAcct.tearDown()
    else:
            try:
                    #same login test via Singapore proxy
                    print("Start failed login via Proxy...")
                    aAcct = AwsUIActions(user_name, proxy=1, proxy_ip=proxy_ip, proxy_port=proxy_port, useragent=useragent)
                    aAcct.loginAttempt(password=password, numFailedAttempts=numFailedAttempts)
            finally:
                if aAcct:
                        aAcct.tearDown()

#failUserLogins("sservice_1@yahoo.ca", "po09PO)(", 1)

def mass_transfer(username, password, transFrom, transfto, numTransfers):
    newobj = AwsUIActions()
    newobj.massTransfer(username, password, transFrom, transfto, numTransfers)
    newobj.tearDown()
