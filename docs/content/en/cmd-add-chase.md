---
title: Add Chase
description: 'Description for Add Chase'
position: 3
category: 'Commands'
---

### Commands

<alert type="info">`addchase`  `add`  `ac`</alert>

### Description

Add chases

Requires `--name, --url, --desc, --live` any other fields are optional. Any
values that contain spaces must be surrounded by quotation marks. <alert type="warning">Only
specific users are granted access to this command.</alert>

Valid fields:
```
    --name "LA Chase"
    --url fancyurlhere.com
    --desc "some description here"
    --live true(default)/false
    --network CBSLA
    --urls "[{'network': 'google', 'url': 'https://google.com'}]"
```

### Examples

```
^add --name "LA Chase" --url cbsla.com --desc "a chase in LA" --live
```

