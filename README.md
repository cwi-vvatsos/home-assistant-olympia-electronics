# home-assistant-olympia-electronics
Home Assistant support for the Olympia Electronics Wifi Thermostat BS-850.

<img src="https://www.olympia-electronics.gr/skn/logoen.png" height="50" alt="Olympia Electronics"><img src="https://lh3.googleusercontent.com/uGa9TO5QoqdmDTEMhTWSDnmw0IdDzn8rmrkzDWJfZoRwQGMlaalMngCfn97eILEXHrg=s180-rw" height="50" alt="Olympia Electronics Thermostat"> <img src="https://www.home-assistant.io/images/components/alexa/alexa-512x512.png" alt="Home Assistant" height="50">

:balloon: :balloon: Works with Google Assistant integration of HA :balloon: :balloon:

<img src="https://i.ibb.co/sHZhwTB/thermostat.jpg">

### Some background info

> _I do not work for olympia electronics. I am no python developer. But i love HA and i've owned olympia electronics thermostats for the last 15 years. It's an affordable thermostat so when the time came to upgrade to a "smart" thermostat, the transision was easy. Using a nest or other smart thermostat would require many changes in my electrical installation so Olympia Electronics was a somewhat the only way to go. I was lucky to be able to access the api from the mobile app and it was an easy one to consume. So here we are._

### Installation
- Download [Olympia Electronics Thermostat from Google Play](https://play.google.com/store/apps/details?id=gr.olympiaelectronics.thermostat), create an account and follow the instructions to register your thermostat. Set it up properly.
- Put olympia_electronics.py inside *{homeassistantconfigfolder}*/custom_components/climate/ (create the folder structure if it not exists)
- Edit the configuration.yaml like this:
```
climate:
  - platform: olympia_electronics
    email: your@email.com
    password: your_password
````    
| Option | Required | Description |
| :------ | :------: | :------ |
| email | :heavy_check_mark: | The email you registered with on the app |
| password | :heavy_check_mark: | The password of the account you registered |

### Possible issues

Although i think this will work with multiple thermostats into your account, i haven't tested it. If you have multiple thermostats and run into any issues, open a ticket

The auth token handling is - not as efficient as i would hope it would be. I will work on optimizing it in the future. 

### Some Declerations
I'm no python developer. I've created the code based on the demos of home assistant. Although it is rough around the edges and probably not as efficient, it works.

> This **unofficial** component uses api calls i got from the mobile app. Although i will continue to try and update the code based on future changes by the developers of the app, at some point it may fail. Sorry.
