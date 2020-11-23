# chasebot

Instruction manual for operating the ChaseApp API via chasebot

## List chases

Pass `--showlive` to see only active chases. Pass `--index [#]`
to fetch a specific chase (working backwards from most recent).

Examples:

```
^list --index 2
^list --showlive
^list --index 4 --showid
```

## Update chases

Requires either `--last` or `--id [ChaseApp chase ID]` along with some
fields to modify (`--name "[new name]"` or `--url [new url]` etc). Any
values that contain spaces must be surrounded by quotation marks. Only
specific users are granted access to this command.

Valid fields and examples:

```
--name "LA Chase"
--url fancyurlhere.com
--desc "some description here"
--live true(default)/false
--network CBSLA
--urls "[{'network': 'google', 'url': 'https://google.com'}]"

e.g. ^update --last --name "LA Chase"
     ^update --id 7e171514-9c51-11ea-b6a3-0b58aa4cbde4 --url fancyurlhere.com
```

## Add chases

Requires `--name, --url, --desc, --live` any other fields are optional. Any
values that contain spaces must be surrounded by quotation marks. Only
specific users are granted access to this command.

Valid fields and examples:

```
--name "LA Chase"
--url fancyurlhere.com
--desc "some description here"
--live true(default)/false
--network CBSLA
--urls "[{'network': 'google', 'url': 'https://google.com'}]"

e.g. ^add --name "LA Chase" --url cbsla.com --desc "a chase in LA" --live
```

## Delete chases

Requires either `--last` or `--id [ChaseApp chase ID]`. Only specific users
are granted access to this command.

Examples:

```
e.g. ^delete --last
     ^delete --id 7e171514-9c51-11ea-b6a3-0b58aa4cbde4
```
