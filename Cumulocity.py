import requests

class CumulocityUtils(object):
    def handleResponse(self,response):
        if response.status_code == 404:
            print("hmm")

    def getAuth(self,auth=None):
        from requests.auth import HTTPBasicAuth
        if auth is not None:
            return HTTPBasicAuth(auth.username, auth.password) 
        else:
            return HTTPBasicAuth(self.username, self.password)

    def getHeaders(self):
        return {
                'Content-Type': 'application/json',
                #'Content-Type': 'application/vnd.com.nsn.cumulocity.managedObject+json',
                'Accept': 'application/json',
                #'Accept': 'application/vnd.com.nsn.cumulocity.managedObject+json',
                'charset': 'UTF-8',
                }


    def getRequest(self,url, auth=None, host=None):
        if host is None:
            host = self.host
        return requests.get(host + url, headers=self.getHeaders(), auth=self.getAuth(auth))

    def postRequest(self, url, jsonPayload, auth=None, host=None, headers=None):
        import json

        self.logger.debug("payload is %s",json.dumps(jsonPayload))

        finalHeaders = self.getHeaders()
        if headers is not None:
            finalHeaders.update(headers)

        if host is None:
            host = self.host

        return requests.post(host + url, headers=finalHeaders,\
                auth=self.getAuth(auth), data=json.dumps(jsonPayload))

    def putRequest(self, url, jsonPayload, auth=None, host=None):
        import json

        self.logger.debug("payload is %s",json.dumps(jsonPayload))

        if host is None:
            host = self.host

        return requests.put(host + url, headers=self.getHeaders(),\
                auth=self.getAuth(auth), data=json.dumps(jsonPayload))

    def readCumulocityConfig(self):
        try:
            # 3.x name
            import configparser
        except ImportError:
            # 2.x name
            import ConfigParser as configparser

        try:
            config = configparser.RawConfigParser()
            config.read('cumulocity.cfg')

            section = self.CONFIG_SECTION
            host = config.get(section, 'deviceCredentialsHost')
            username = config.get(section, 'deviceCredentialsUsername')
            password = config.get(section, 'deviceCredentialsPassword')

            if not username or not host or not password:
                raise Exception('username "{}", host "{}" or password "{}" for device credentials AP empty'.format \
                        (username,host,password))

            self.deviceCredentialsAPI = Struct(**{
                    'host': host,
                    'username': username,
                    'password': password
                    })

            return True
        except Exception as e:
            #could not read config
            self.logger.debug('could not read config cumulocity.cfg: %s',e)
            return False

    def readAppConfig(self):
        try:
            # 3.x name
            import configparser
        except ImportError:
            # 2.x name
            import ConfigParser as configparser

        try:
            config = configparser.RawConfigParser()
            config.read('app.cfg')

            section = self.CONFIG_SECTION
            self.tenant_id = config.get(section, 'tenant_id')
            self.username = config.get(section, 'username')
            self.password = config.get(section, 'password')
            self.host = 'http://{:s}.cumulocity.com'.format(self.tenant_id)

            return True
        except Exception as e:
            #could not read config
            self.logger.debug('could not read config: %s',e)
            return False

    def writeConfig(self):
        try:
            # 3.x name
            import configparser
        except ImportError:
            # 2.x name
            import ConfigParser as configparser

        config = configparser.RawConfigParser()

        section = self.CONFIG_SECTION
        config.add_section(section)
        config.set(section,'tenant_id',self.tenant_id)
        config.set(section,'username', self.username)
        config.set(section,'password', self.password)

        with open('app.cfg', 'w') as configfile:
            config.write(configfile)

    '''
    check if object has a method called method

    returns boolean
    '''
    def hasMethod(self,object,method):
        if hasattr(object,method):
            if(callable(getattr(object, method))):
                return True
        return False


class Struct:
    def __init__(self, **entries): 
        self.__dict__.update(entries)


class Cumulocity(CumulocityUtils):
    CONFIG_SECTION = 'device'

    def __init__(self,unique_id):
        import logging
        self.unique_id= unique_id
        #self.host = "http://plieninger.cumulocity.com"
        self.logger = logging.getLogger(__name__)

        #self.username = 'plieningerweb@gmail.com'
        #self.password = 'idontknow'

        #initalized later in readCumulocityConfig
        #self.deviceCredentialsAPI = Struct(**{...})

    def hasDeviceCredentials(self):
        if hasattr(self,'username') and self.username != '':
            if hasattr(self,'password') and self.password != '':
                if hasattr(self,'host') and self.host != '':
                    return True

        return False

    def getDeviceCredentials(self):
        url = "/devicecontrol/deviceCredentials"
        payload = {
            "id" : self.unique_id
        }

        response = self.postRequest(url,payload,auth=self.deviceCredentialsAPI, host=self.deviceCredentialsAPI.host)

        self.logger.info("request to %s",response.url)
        self.logger.debug("response of getDeviceCredentials is %s (text: %s)",response, response.text)

        if response.status_code == 404:
            if response.json()['error'] == 'devicecontrol/Not Found':
                self.logger.info("device not yet registered in cumulocity online. Waiting for Acceptance")
            else:
                self.logger.info("device request failed")
        elif response.status_code == 201:
            data = response.json()
            self.password = data['password']
            self.username = data['username']
            self.tenant_id = data['tenantId']

            return True


    def isRegistered(self):
        url = "/identity/externalIds/c8y_Serial"


        response = self.getRequest(url + "/" + self.unique_id)

        self.logger.info("request to %s",response.url)
        self.logger.debug("response of isRegistered is %s (text: %s)",response, response.text)
        
        print(response.json())

        if response.status_code == 404:
            self.logger.info("devie not yet registered")
            return False
        elif response.status_code == 200:
            data = response.json()
            self.device_id = data['managedObject']['id']
            return True
        else:
            raise Exception("unexpected answer from isRegistered request")
            


    def createDevice(self):
        url = "/inventory/managedObjects"

        payload = {
            "name": "DebianDevice", 
            "c8y_IsDevice": {}, 
            #agend, so this device will receive all operations itsself
            "com_cumulocity_model_Agent": {},
            #"c8y_SupportedOperations": [ "c8y_Restart", "c8y_Configuration", "c8y_Software", "c8y_Firmware" ],
            "c8y_SupportedOperations": [ "c8y_Restart", "c8y_Configuration" ],
            #display measurements tab in cumulocity backend
            "c8y_Display": {},
            #monitor avaibility in cumulocity backend
            #also display last connection timestamp
            "c8y_RequiredAvailability": {
                #after x minutes without connection, display as Offline
                "responseInterval": 600
            },

                
        }
        response = self.postRequest(url,payload)

        if response.status_code == 201:
            self.logger.info("device successfully created")
        else:
            raise Exception("could not create device")

        data = response.json()
        self.device_id  = data['id']

        self.logger.debug("device is is %s",self.device_id)

    '''
    add measurement to cumulocity backend

    the data argument could look e.g:
    {
        #we need a type (neccessarry)
        "type": "c8y_TemperatureMeasurement"

        #custom name of measurement method or device
        "c8y_TemperatureMeasurement": {
            #measurement item with custom name        
            "T": { 
                "value": 25,
                "unit": "C" }
            },
    }
    '''
    def addMeasurement(self,data):
        url = "/measurement/measurements"

        import datetime
        payload = {
            "source": { "id": self.device_id },
            #needs +00:00 or something, otherwise it will not be displayd in measurements tab
            "time": datetime.datetime.utcnow().isoformat()+"+00:00",
        }
        payload.update(data)

        #possible cumulocity bug here
        #we can only create a measurement if content-type is this
        #application/json is not enoguh and we would get a 401
        headers = {
            'Content-Type':'application/vnd.com.nsn.cumulocity.measurement+json'
        }
        response = self.postRequest(url,payload, headers=headers)

        if response.status_code == 201:
            self.logger.info("measurement created")
            return True
        else:
            self.logger.debug('answer of request was: %s', response.text)
            raise Exception("could not create measurement")



    def addIdentifyDeviceBySerial(self):
        url = "/identity/globalIds/" + self.device_id + "/externalIds"

        payload = {
            "type" : "c8y_Serial",
            "externalId" : self.unique_id
        }

        response = self.postRequest(url,payload)
        
        if response.status_code == 201:
            self.logger.info("device identification by unique serial successfully added")
        else:
            raise Exception("could not add device identification by unique serial")

    '''
    default keys of every operations

    this is needed to find out, how the operation action is called, or "what is individual"
    '''
    OPERATIONS_DEFAULTKEYS = [u'status', u'description', u'self', u'creationTime', u'deviceId', u'id']

    '''
    get list of operations for this device for a specific status

    items in list look like:
    {   u'status': u'PENDING',
        u'description': u'Restart device',
        u'self': u'http://plieninger.cumulocity.com/devicecontrol/operations/10429',
        u'creationTime': u'2015-10-24T22:43:39.654+02:00',
        u'deviceId': u'10428',
        u'id': u'10429',
        u'c8y_Restart': {}
    }
    '''
    def getOperations(self, status):
        if not status in ['','PENDING','EXECUTING','SUCCESSFUL', 'FAILED']:
            raise Exception('status "{:s}" for quering operations is not know'.format(status))

        url = "/devicecontrol/operations?deviceId=" + str(self.device_id) + "&status=" + str(status)

        response = self.getRequest(url)


        if response.status_code == 200:
            self.logger.info("get operations for this device with status '%s'",status)
            print(response.json())
            data = response.json()
            if 'operations' in data:
                return data['operations']
            return False
        else:
            self.logger.warn("could not get operations for this device")
            return False

    '''
    update an operation

    id: id of operation
    status: new status
    data: additional dict of data to store, e.g. a command reponse or anything
    '''
    def updateOperation(self,id,status, data=None):
        url = "/devicecontrol/operations/"

        payload = {
            "status": status
        }
        if data is not None:
            payload.update(data)

        response = self.putRequest(url + id, payload)

        if response.status_code != 200:
            self.logger.warn("could not update operation %s to %s for this device", id, status)
            return False

        self.logger.info("updated operation %s to %s for this device", id, status)
        return True

    def cleanRestartOperations(self):
        operations = self.getOperations('EXECUTING')

        if operations:
            #check if we have an executing restart operation
            for o in operations:
                if 'c8y_Restart' in o:
                    #update this, because we seem to be running again
                    #we do not care about errors, because this function is 
                    #called after every system init again
                    self.updateOperation(o['id'],'SUCCESSFUL')

        self.logger.info("cleanRestartOperations finished")

    def getOperationSpecifics(self,operation):
        o = operation.copy()
        for i in operation:
            if i in self.OPERATIONS_DEFAULTKEYS:
                del o[i]

        self.logger.debug("getOperationSpecifics is %s",o)
        return o

    def dispatchOperations(self):
        operations = self.getOperations('PENDING')

        if operations:
            for o in operations:
                self.logger.info("try to dispatch operation %s",o)

                o_specifics = self.getOperationSpecifics(o)

                if len(o_specifics.keys()) > 0:
                    command = list(o_specifics.keys())[0]
                    
                    #check if operations_handler has a method, that is called
                    #like the command
                    if self.hasMethod(self.operations_handler,command):
                        self.logger.info("run operatino command %s",command)
                        handler = getattr(self.operations_handler,command)
                        #call method with operation
                        handler(o,self)
                    else:
                        self.logger.warn('could not find function to handle operation in operations_handler')
                else:
                    self.logger.warn("could not find a command in operation")

                    #update command as failed
                    self.updateOperation(o['id'],'FAILED')

    def connectAndInit(self):
        #load cumulocity config data
        if not self.readCumulocityConfig():
            raise Exception('no cumulocity.cfg config found. Please create it or app.cfg first')
            return False


        #load config data
        self.readAppConfig()

        #check if we already have device credentials
        if not self.hasDeviceCredentials():
            if self.getDeviceCredentials():

                #write new config after getting device credentials
                self.writeConfig()

        #check if we now have device credentials
        if self.hasDeviceCredentials():
            if not self.isRegistered():

                #TODO add try block around for error handling
                self.createDevice()
                self.addIdentifyDeviceBySerial()

            #check if there are operations which we can clean
            self.cleanRestartOperations()

            return True

        return False
