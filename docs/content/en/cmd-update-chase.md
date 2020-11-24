---
title: Update Chase
description: 'Description for Update Chase'
position: 2
category: 'Commands'
---

### Commands

<alert type="info">`updatechase`  `update`  `uc`</alert>

### Description

Update chases

Requires either `--last` or `--id [ChaseApp chase ID]` along with some
fields to modify (`--name "[new name]"` or `--url [new url]` etc). Any
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
^update --last --name "LA Chase"
```
```
^update --id 7e171514-9c51-11ea-b6a3-0b58aa4cbde4 --url fancyurlhere.com
```

