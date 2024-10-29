# Manual for Fiskaly Connection in PoS  
  
The fiscal connectivity in Odoo is designed to ensure compliance with local tax regulations by integrating fiscal devices or services that manage tax data securely in accordance with legal requirements (FinanzOnline Institution).   
  
SIGN AT Protocol used --> https://developer.fiskaly.com/api/rksv/v1#section/Processes  
## Creating the Resources:   
  
 **Fiskaly API key and Fiskaly API secret** must be retrieved from the Fiskaly API (SIGN AT) provider and set in the *system parameters* in Odoo. These *system parameters* are set manually by the *Multioss Dev.* *Team* and are required throughout the whole procedure.   
  
    Settings -> Technical -> Parameters -> System parameters  
  
For Fiskaly API (SIGN AT) to function properly, the taxpayer (company) should provide necessary (legal) information in order to authenticate with FinanzOnline Institution. **This information must be added to the company instance in Odoo. *Austria* has to be selected as the company's country of operation** in order to see required fields in the sign in form for the company.  

- https://developer.fiskaly.com/api/rksv/v1#tag/FON  [1]  
    The following must be **provided** in the company information:  

    - *FON Participant ID - Teilnehmer-Identifikation (Registrierkassen-Webservice-Benutzer)*[1].  
    - *FON User ID - Benutzer-Identifikation (Registrierkassen-Webservice-Benutzer)[1]*.  
    - *FON User Pin - PIN (Registrierkassen-Webservice-Benutzer)*[1].  
    - *Legal Entity Type - Rechtsträgerkennung Typ in FinanzOnline*.  
    - *Legal Entity Number - Rechtsträgerkennung in FinanzOnline*.  
      
After this, click on *Generate SCU* button in order to create an unique *Signature Creation Unit*. A unique *SCU* will be displayed on the same page and its ID will be visible on the `dashboard.fiskaly.com` with the digital form's state being **INITIALIZED**.  
    
  - **WARNING**: If you no longer wish to have a unique *SCU* for the created company, press **DECOMMISSION *SCU*** button. Keep in mind that once the digital signature's state goes to **DECOMMISSIONED**, you **CANNOT** use it in order to create **Cash Register**, hence no **RECEIPTS** can be signed.   
   *Refer here for more detailed information*: https://developer.fiskaly.com/api/rksv/v1#section/Processes/Daily-Operations  
   If you would like to remove your company's information on our platform,  archive with the ARCHIVE button, and digital signature's **STATE** will be automatically transformed to **DECOMMISSIONED**.  
     
   After creating a unique *SCU* for your company, you can go to the *Point of Sale (Kassensystem)*. In case you don't have *Point of Sale (PoS)*, you can create one.  
    
	   Point of Sale -> Configuration -> Settings -> New Shop -> Save.  
    
After creation, you should see ***Fiskaly API*  section** where it says ***Create Cash Register in order to sign a receipt***. Click on SAVE to save Cash Register ID. Once again, information about the created *Cash Register* can be found on `dashboard.fiskaly.com`.   
  *Cash Register* state will remain **CREATED** until *PoS* session is **NOT OPENED**.   
  Only after clicking on Open Session will the digital form’s state be **INITIALIZED** and ready to sign a receipt.
    
  - **WARNING**: You should ONLY create as many *Cash Registers* as there are in the *PoS* in order to avoid complications with audit.   
  Refer here for more informations: https://developer.fiskaly.com/api/rksv/v1#section/Processes/Set-up-Resources  
  
If you no longer need a *PoS*, you can archive it, and its **STATE** will be **DECOMMISSIONED**. It will no longer be usable afterward.  
     
   - **WARNING**: If **Cash Register** is temporarily not usable, you can put it into **OUTAGE** state. In order to do so, go to PoS application and click on **OUTAGE Cash Register**. Once it is in **OUTAGE**, you won't be able to open session in PoS. It has to be done at most 48 hours after the defect has been detected. **Once it is usable again, you can put it back to INITIALIZED state**.
   If **Cash Register** is defective and no longer can be used, transition it into the state **DEFECTIVE**. You can do that by going to PoS application and click on the 3 dot menu (in the same field where you have Outage Cash Register and Initialize Cash Register).  
     
**Otherwise, you can close and open *PoS* sessions as many times as you want.** It will preserve the same unique *Cash Register* ID required to sign the receipt.  
     
     
 Finally, all that remains is to generate a receipt in the ***Point of Sale***.