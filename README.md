# MiKettle Home Assistant Custom component
Place the custom_components folder in your configuration directory (or add its contents to an existing custom_components folder)

Install bluepy:
`pip3 install bluepy`

Find the MAC address of your MiKettle:
`sudo hcitool lescan`

Configure desired sensors:
```
sensor:
  - platform: mikettle
    mac: 'AB:CD:EF:12:34:56'
    product_id: 275
    monitored_conditions:
      - action
      - mode
      - set temperature
      - current temperature
      - keep warm type
      - keep warm time
```

More options are:
- force_update (boolean)(Optional)
  Sends update events even if the value hasn’t changed.
  Default value: false

- name (string)(Optional)
  The name displayed in the frontend.
  
Even more options regarding caching and intervals are comming in the future.

For advanced debugging set:
```
logger:
  default: info
  logs:
    custom_components.mikettle.sensor: debug
    mikettle: debug
```

For more information check:
- https://github.com/drndos/mikettle
- https://github.com/aprosvetova/xiaomi-kettle
