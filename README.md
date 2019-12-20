# sfdc
SalesForce python dev work - originally created with SalesForce SDK v36 which was a while ago. Still however, you might find it useful how to use the almost entire scope of the developer SDK document.


Testing triggering Salesforce.com security systems for behavioral analysis. PoC.

Attack paths:

    Weak lockout policy
    Disable clickjack protection for customer Visualforce pages with standard headers
    Creation of users
    Account compromise
    Login from remote triggers UBA Risk User: High, activity from unseen browser, device, OS, unseen location(including unseen IPs v2) (score approx: 45-50)
    UBA Risk User: 10x High, Data export --- Instead of this, Attacker set Trusted IP Range to enable backdoor access, triggers Policy alert.

Data Exfiltration:

    Grant Admin permissions
    Mass Transfer to another account, triggers UBA Risk User: Medium, Mass Transfer+After-hr.
    Creating given numbers of mockup account data to have something to transfer.

Insider user threat path:

    Admin grant excessive permissions to insider user, triggers Policy alert: Profile/Change user permissions
    Deploying new Sharing Rules as an insider threat
    Insider user is corrupted by a vendor, he helped vendor to extend contract term, triggers Policy alert: Contract Create+Update
    Before termination, insider user also Mass deleting data, triggers UBA Risk User: High, Mass Delete
    Policy alert test, change user profile

Insider user threat test #2:

    UBA Risk User: 20x Medium, Reports export, Report Run
    The 3rd party has the permission to access sensitive data and function, he run and export the reports, sale to competitor, triggers UBA Risk User: Medium, Reports exported, Report Run
    The 3rd party also export data, triggers UBA Risk User: High, Data Export
    For all report activities by the 3rd party, stand out in KSI: Top customer report run and Top customer report exported
    Login tests via Singapore proxy

    contains manipulating user's details (create, activate, deactivate)
    metadata changer python script
    the Salesforce API SDK doc version 36
    enterprise, partner and metadata wsdl

At the time created, a bug has been found telling that you cannot deploy a zipFile package until the sessionTimeout value has been changed: https://success.salesforce.com/issues_view?id=a1p30000000sXzaAAE
