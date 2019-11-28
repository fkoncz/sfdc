from random import choice
from string import ascii_lowercase
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
        driver.get("https://login.salesforce.com/")
        count = numFailedAttempts
        while count > 0:
            (wait.until(EC.presence_of_element_located((By.ID,"username")))).send_keys(self.user_name)
            elem = wait.until(EC.presence_of_element_located((By.ID,"password")))
            elem.send_keys(self.password)
            elem.send_keys(Keys.RETURN)
            print("Trying login nr.: "+str(count))
            count -= 1

    def tearDown(self):
        self.driver.close()

    # Mass Delete is achievable via Selenium
    def massDelete(self, asUserLogin, asUserPassword):
        driver = self.driver
        wait = WebDriverWait(driver, 30)
        self.loginAttempt(asUserLogin, asUserPassword, 1)
        try:
            wait.until(EC.presence_of_element_located((By.ID,"cancel-button")))
            pass
        except:
            try:
                wait.until(driver.find_element_by_id((By.NAME,"save")))
                pass
            except:
                wait.until(EC.presence_of_element_located((By.ID,"setupLink")))
                pass
        driver.get("https://na24.salesforce.com/setup/own/massdelete.jsp?ftype=a&retURL=%2Fui%2Fsetup%2Fown%2FMassDeleteSelectPage%3Fsetupid%3DDataManagementDelete%26retURL%3D%252Fui%252Fsetup%252FSetup%253Fsetupid%253DDataManagement")
        (wait.until(EC.presence_of_element_located((By.NAME,"find")))).click()
        (wait.until(EC.presence_of_element_located((By.ID,"closed_opp")))).click()
        (driver.find_element_by_id("owner_opp")).click()
        (wait.until(EC.presence_of_element_located((By.ID,"allBox")))).click()
        (wait.until(EC.presence_of_element_located((By.NAME,"save")))).click()

    def massTransfer(self, asUserLogin, asUserPass, transferFrom, transferTo, numberOfTransfers):
        driver = self.driver
        wait = WebDriverWait(driver, 15)
        self.loginAttempt(asUserLogin, asUserPass, 1)
        # If we have to change password, the first screen that appears only contains the "Cancel" button.
        try:
            wait.until(EC.presence_of_element_located((By.ID,"cancel-button")))
            pass
        except:
            # If we already changed our password, the screen that appears wants to add a cell phone number for password recovery.
            try:
                wait.until(driver.find_element_by_id((By.NAME,"save")))
                pass
            # Otherwise, we can see the SETUP link.
            except:
                wait.until(EC.presence_of_element_located((By.ID,"setupLink")))
                pass
        driver.get("https://na24.salesforce.com/p/own/BulkTransfer?ent=Account")
        count = numberOfTransfers
        while count > 0:
            elem = wait.until(EC.presence_of_element_located((By.ID,"newOwn")))
            elem.send_keys(Keys.CONTROL+"a")
            elem.send_keys(Keys.DELETE)
            elem.send_keys(transferTo)
            (driver.find_element_by_name("find")).click()
            (wait.until(EC.presence_of_element_located((By.ID,"allBox")))).click()
            (driver.find_element_by_name("save")).click()
            print("Done with mass transfer from "+transferFrom+" to "+transferTo+".\nMass transfer nr.: "+str(count)+"\n")
            count -= 1
            elem = wait.until(EC.presence_of_element_located((By.ID,"newOwn")))
            elem.send_keys(Keys.CONTROL+"a")
            elem.send_keys(Keys.DELETE)
            elem.send_keys(transferFrom)
            (driver.find_element_by_name("find")).click()
            (wait.until(EC.presence_of_element_located((By.ID,"allBox")))).click()
            (driver.find_element_by_name("save")).click()
            print("Mass Transfer from "+transferTo+" to "+transferFrom+" is done.\nMass transfer nr.: "+str(count)+"\n")
            count -= 1
        print("Done with mass transfer "+str(numberOfTransfers)+" times.")
    
    def createReport(self, howMany, username, password, whichObject):
        driver = self.driver
        wait = WebDriverWait(driver, 15)
        self.loginAttempt(username, password, 1)
        # If we have to change password, the first screen that appears only contains the "Cancel" button.
        try:
            wait.until(EC.presence_of_element_located((By.ID,"cancel-button")))
            pass
        except:
            # If we already changed our password, the screen that appears wants to add a cell phone number for password recovery.
            try:
                wait.until(driver.find_element_by_id((By.NAME,"save")))
                pass
            # Otherwise, we can see the SETUP link.
            except:
                wait.until(EC.presence_of_element_located((By.ID,"setupLink")))
                pass
        count = howMany
        while count > 0:
            if (count == howMany):
                firstRun = True
            else:
                firstRun = False
            driver.get("https://na24.salesforce.com/reportbuilder/reportType.apexp")
            elem = wait.until(EC.presence_of_element_located((By.ID,"quickFindInput")))
            elem.send_keys(whichObject)
            elem.send_keys(Keys.ENTER)
            (driver.find_element_by_id("thePage:rtForm:createButton")).click()
            (wait.until(EC.presence_of_element_located((By.ID,"ext-gen63")))).click()
            (wait.until(EC.presence_of_element_located((By.NAME,"memorizenew")))).click()
            if firstRun is True:
                reportName = "lsl-Report-"+(''.join(choice(ascii_lowercase) for i in range(5)))
                #We generate a random name after the common "lsl-Report-" prefix but we store the first one's name. The dashes for the Report unique name will be automatically replaced with an underscore by Salesforce.
                (wait.until(EC.presence_of_element_located((By.ID,"report_name")))).send_keys(reportName)
                (driver.find_element_by_id("devName")).click()
                (driver.find_element_by_name("saveas")).click()
                count -= 1
            else:
                (wait.until(EC.presence_of_element_located((By.ID,"report_name")))).send_keys("lsl-Report-"+(''.join(choice(ascii_lowercase) for i in range(5))))
                (driver.find_element_by_name("saveas")).click()
                count -= 1
        print("Done with creating "+str(howMany)+" reports.")
        return reportName
        
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

def mass_delete(username, password):
    newobj = AwsUIActions()
    newobj.massDelete(username, password)
    newobj.tearDown()

def mass_transfer(username, password, transFrom, transfto, numTransfers):
    newobj = AwsUIActions()
    newobj.massTransfer(username, password, transFrom, transfto, numTransfers)
    newobj.tearDown()

def create_Report(howMany, username, password, whichObject):
    newobj = AwsUIActions()
    reportName = newobj.createReport(howMany, username, password, whichObject)
    newobj.tearDown()
    return reportName

