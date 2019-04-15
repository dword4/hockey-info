# hockey-info
---
An app written in Python utilizing Flask and the NHL API to present hockey data
in a simple and easy to view manner with a focus on mobile users

# Disclaimer
---
I do this for fun, there is absolutely no warranty or guarantee with any of this.
I don't have rights to anything the NHL does, just another hockey nerd that knows
a few neat programming tricks trying to help others absolutely

# How to run it?
---
```
export FLASK_APP=app.py
flask run
```
It will start a server running on localhost and accessible on port 5000 (http://127.0.0.1:5000/)
q
If you need to run it on a different port invoke flask thusly

```
flask run --host=0.0.0.0
```

If you happen to have a Docker server you can use [hockey-info-docker](https://gitlab.com/dword4/hockey-info-docker) to deploy it.

