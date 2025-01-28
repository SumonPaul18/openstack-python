# How to Run the openstack-flask apps

~~~
rm -rf openstack-flask
git clone https://github.com/SumonPaul18/openstack-flask.git
cd openstack-flask
~~~
---
# Details:

# Python OpenStack
```
sudo apt install python3-virtualenv
sudo apt install python3.12-venv
python -m venv .venv
source .venv/bin/activate
pip install openstacksdk
python -m pip install openstacksdk
python -m openstack version
pip install openstacksdk --break-system-packages
python app.py 
```
