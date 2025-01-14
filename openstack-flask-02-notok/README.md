# How to Run the openstack-flask apps on Docker

~~~
rm -rf openstack-flask
git clone https://github.com/SumonPaul18/openstack-flask.git
cd openstack-flask/openstack-flask-02-notok
docker compose up -d
docker compose ps
~~~

# How to Run the openstack-flask apps on Host

~~~
rm -rf openstack-flask
git clone https://github.com/SumonPaul18/openstack-flask.git
cd openstack-flask/openstack-flask-02-notok
pip install -r requirements.txt
python app.py
~~~

# Python OpenStack
```
apt install python3-virtualenv
sudo apt install python3-virtualenv
sudo apt install python3.12-venv
python3 -m venv .venv
source .venv/bin/activate
pip install openstacksdk
python -m pip install openstacksdk
python -m openstack version
python3 -m openstack version
pip install openstacksdk --break-system-packages
python3 app.py 
python3 op.py 
```
