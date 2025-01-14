import openstack
from flask import Flask, jsonify, render_template
from openstack import connection

app = Flask(__name__)

# OpenStack ????? ??????
conn = connection.Connection(cloud='openstack')

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/instances')
def list_instances():
    instances = conn.compute.servers()
    instance_list = [{'name': instance.name, 'status': instance.status} for instance in instances]
    return jsonify(instance_list)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port='5000')
