---
title: List Chases
description: 'Description for List Chases'
position: 1
category: 'Commands'
---

### Commands

<alert type="info">`listchases`  `list`  `lc`  `chases`</alert>

### Description

List chases

Pass `--showlive` to see only active chases. Pass `--index [#]`
to fetch a specific chase (working backwards from most recent).

### Examples

```
^list --index 2
```
```
^list --showlive
```
```
^list --index 4 --showid
```

