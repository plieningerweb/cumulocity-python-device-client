# Cumulocity python device client
**A Device Client for the Cumulocity Rest API written in Python**

It can run, as example, on a raspberry pi or any other linux computer with installed python 3

## How to run it

```
#git clone this repo
#cd cumulocity-python-device-client

python3 app.py
```

* Go to your cumulocity backend, e.g. https://yourusername.cumulocity.com/apps/devicemanagement/
* Go to device registration page
* Enter your raspberry serial number here (if you dont know, check how it is defined in the program output above. It should be something like "rpi-0123012539985245")
* Click on accept
* Now the device is connected to your cumulocity account
* The data is stored in the app.cfg file
* Next time you run `python3 app.py`, it is already registered

Now you can checkout some nice random measurements, reported under the measurements tap in your cumulocity backend.

