# hockey-info
---
An app written in Python utilizing Flask and the NHL API to present hockey data
in a simple and easy to view manner with a focus on mobile users

# Disclaimer
---
I do this for fun, there is absolutely no warranty or guarantee with any of this.
I don't have rights to anything the NHL does, just another hockey nerd that knows
a few neat programming tricks trying to help others absolutely


# Python Virtual Env Setup (venv)
---
It is best practice to setup an isolated Python3 "virtual environment" for any
project. Many IDEs may do this for you, automatically. However, if you need to
do this yourself, this is the basic method:

    python3 -m venv venv-hockey
    . ./venv-hockey/bin/activate
    pip install pip setuptools wheel --upgrade
    pip install -r requirements.txt

You can then work within this project without affecting other Python envs, or
your system installation. Once you are done, you should be sure to deactivate
the environment.

    deactivate


# How to run it?
---
```
export FLASK_APP=app.py
flask run
```
It will start a server running on localhost and accessible on port 5000 (http://127.0.0.1:5000/)

If you need to run it on a different port invoke flask thusly

```
flask run --host=0.0.0.0
```

If you happen to have a Docker server you can use [hockey-info-docker](https://gitlab.com/dword4/hockey-info-docker) to deploy it.

---
