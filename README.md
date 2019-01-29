# home-assistant-olympia-electronics
Home Assistant support for the Olympia Electronics Wifi Thermostat BS-850.

### Installation
- Download [Olympia Electronics Thermostat from Google Play](https://play.google.com/store/apps/details?id=gr.olympiaelectronics.thermostat), create an account and follow the instructions to register your thermostat. Set it up properly.
- Put olympia_electronics.py inside *{homeassistantconfigfolder}*/custom_components/climate/ (create the folder structure if it not exists)
- Edit the configuration.yaml accordingly using the account credentials you created on step 1:
```
climate:
  - platform: olympia_electronics
    email: your@email.com
    password: your_password
````    
### Possible issues

Although i think this will work with multiple thermostats into your account, i haven't tested it. If you have multiple thermostats and run into any issues, open a ticket

The auth token handling is - not as efficient as i would hope it would be. I will work on optimizing it in the future. 

### Some Declerations
I'm no python developer. I've created the code based on the demos of home assistant. Although it is rough around the edges and probably not as efficient, it works.

This **unofficial** component uses api calls i got from the mobile app. Although i will continue to try and update the code based on future changes by the developers of the app, at some point it may fail. Sorry.
