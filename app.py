
from Cumulocity import Cumulocity

'''
class is used to handle operations issued by backend

name of operation is the individual key name of the operation
as the argument, the operation item (dict) is passed, which might look like

example:
function 'c8y_Restart' will be called with argument
operation = 
    {   u'status': u'PENDING',
        u'description': u'Restart device',
        u'self': u'http://plieninger.cumulocity.com/devicecontrol/operations/10429',
        u'creationTime': u'2015-10-24T22:43:39.654+02:00',
        u'deviceId': u'10428',
        u'id': u'10429',
        u'c8y_Restart': {}
    }
and the Cumulocity instance
call: c8y_Restart(operation,Cumulocity)

the handler function also has to update the operation afterwards
with status success or failed

otherwise, the function will be called again and again
'''
class OperationHandler(object):
    def test(self,operation, cumulocity):
        print("run operation test")

        data = {
                'result': 'pretty bad shape'
                }
        cumulocity.updateOperation(operation['id'], 'SUCCESSFUL', data=data)
    
    def c8y_Restart(self,operation, cumulocity):
        print("run operation cy8_Restart")

        cumulocity.updateOperation(operation['id'], 'EXECUTING')

    def shellcommand(self,operation, cumulocity):
        """
        shellcommand
        execute a custom shell command and get answer

        example to call it:
        {
        

        }

        timeout: DURATION  is  a  floating point number with an optional suffix: 's' for seconds (the default), 'm' for minutes, 'h' for hours or 'd' for days

        """

        print('run operation shellcommand')
        from subprocess import STDOUT, CalledProcessError, check_output

        if not 'cmd' in operation['shellcommand']:
            print('could not find command in operation')
            print('update operation to failed')
            
            data = {
                    'error': 'missing "cmd" key in operation'
                    }
            cumulocity.updateOperation(operation['id'], 'FAILED', data=data)

            return
        else:
            cmd = operation['shellcommand']['cmd']

        #check if wrong character & in command
        #we dont want to run it, could open antoher thread and
        #circumvent timeout system
        if '&' in 'cmd' in operation['shellcommand']:
            print('do not run commands with "&"')
            
            data = {
                    'error': 'found character "&" in command; do not run, to prevent circumventing timeout'
                    }
            cumulocity.updateOperation(operation['id'], 'FAILED', data=data)

            return


        timeout='15s'
        if 'timeout' in operation['shellcommand']:
            timeout = str(operation['shellcommand']['timeout'])

        #use unix timeout for every command
        cmd = 'timeout --kill-after ' + timeout + ' ' + timeout + ' ' + cmd

        #send error also to output
        #set timeout to seconds
        err = ''
        errcode = 0
        output = b''
        try:
            print("run command {}".format(cmd)) 
            output = check_output(cmd, stderr=STDOUT, shell=True, executable="/bin/bash")
        except CalledProcessError as e:
            err = str(e)
            errcode = e.returncode

        #decode output from byte array to utf8
        output_u8 = output.decode('utf-8')

        data = {
            'out': output_u8,
            'err': err,
            'returncode': errcode
                }

        cumulocity.updateOperation(operation['id'], 'SUCCESSFUL', data=data)


'''
measure a value and send it to the backend

this is an example, how this can look like
'''
def measure(cumulocity):
    import random
    data = {
        "type": "bc",
        "bc": {
            "random value": {
                "value": random.randint(0,100),
                "unit": ""
                }
            }
    }
    cumulocity.addMeasurement(data)

def human2bytes(s):
    """
    >>> human2bytes('1M')
    1048576
    >>> human2bytes('1G')
    1073741824
    """
    symbols = ('Byte', 'KiB', 'MiB', 'GiB', 'T', 'P', 'E', 'Z', 'Y')
    import re
    num = re.findall(r"[0-9\.]+", s)
    assert (len(num) == 1)
    num = num[0]
    num = float(num)
    for i, n in enumerate(symbols):
        if n in s:
            multiplier = 1 << (i)*10
            return int(num * multiplier)
    raise Exception('human number not parsable')

def getMonthlyDataUsage():
    """
    get monthly data usage from vnstat
    value is negative if failed
    otherwise in KByte
    """
    from subprocess import check_output
    from math import floor

    out = check_output(['/usr/bin/vnstat','-i', 'eth0', '--oneline'])

    monthly_kib = -1

    #check if not empty
    try:
        if out:
            #get 11.field (monthly datatransfer on interface
            ps = out.split(';')
            if len(ps) >= 12:
                monthly = ps[10]

                monthly_kib = floor(human2bytes(monthly) / 1024)
    except Exception as e:
        print("exception is",e)
        pass

    return monthly_kib



def measureDataUsage(cumulocity):
    from subprocess import check_output

    out = check_output(['vnstat' '-i eth0 --oneline'])

    #check if not empty
    if out:
        #get 11.field (monthly datatransfer on interface
        ps = out.split(';')
        if len(ps) >= 12:
            monthly = ps[10]

            monthly_kib = floor(human2bytes(monthly) / 1024)

            data = {
                "type": "traffic",
                "traffic": {
                    "monthly_eth0": {
                        "value": monthly,
                        "unit": "KByte"
                        }
                    }
            }

            #cumulocity.addMeasurement(data)

def main():
    import logging
    logging.basicConfig(level=logging.DEBUG)

    #load with unique id of this device
    #e.g. a serial number or something else...
    c = Cumulocity('apl-pv-1')

    #set operation handler
    c.operations_handler = OperationHandler()

    import time

    while True:
        time.sleep(2)

        #if we can regiser and connect 
        if c.connectAndInit():

            #repeat cycle phase
            for i in range(1,200):
                #execute operations
                c.dispatchOperations()

                #update inventory
                #is not implemented
                
                #send measurements
                measure(c)

                #send events
                #not implemented

                #wait short moment to repeat cycle
                time.sleep(5)

if __name__ == "__main__":
    main()
