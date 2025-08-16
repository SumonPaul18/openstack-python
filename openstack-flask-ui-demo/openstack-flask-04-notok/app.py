import openstack
from flask import Flask, jsonify, request, render_template
from openstack import connection

app = Flask(__name__)

# Establish OpenStack connection
conn = connection.Connection(cloud='openstack')

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/instances', methods=['GET'])
def list_instances():
    instances = conn.compute.servers()
    instance_list = [{'name': instance.name, 'status': instance.status, 'id': instance.id} for instance in instances]
    return render_template('list_instances.html', instances=instance_list)

@app.route('/create_instance_page', methods=['GET'])
def create_instance_page():
    images = conn.compute.images()
    flavors = conn.compute.flavors()
    networks = conn.network.networks()
    keys = conn.compute.keypairs()
    
    return render_template('create_instance_page.html', images=images, flavors=flavors, networks=networks, keys=keys)

@app.route('/create_instance', methods=['POST'])
def create_instance():
    name = request.form['name']
    image_id = request.form['image']
    flavor_id = request.form['flavor']
    network_id = request.form['network']
    ssh_key_name = request.form['ssh_key']
    
    # Create the server
    instance = conn.compute.create_server(
        name=name,
        image_id=image_id,
        flavor_id=flavor_id,
        networks=[{"uuid": network_id}],
        key_name=ssh_key_name
    )
    
    # Wait for the server to be active
    conn.compute.wait_for_server(instance)
    
    return jsonify({'status': 'Instance created', 'name': instance.name})

@app.route('/create_project', methods=['POST'])
def create_project():
    project_name = request.form['project_name']
    
    # Create a project in OpenStack
    project = conn.identity.create_project(name=project_name)
    
    return jsonify({'status': 'Project created', 'name': project.name})

@app.route('/create_ssh_key', methods=['POST'])
def create_ssh_key():
    key_name = request.form['key_name']
    
    # Create a new SSH key pair in OpenStack
    keypair = conn.compute.create_keypair(name=key_name)
    
    return jsonify({'status': 'SSH Key created', 'key_name': keypair.name, 'private_key': keypair.private_key})

@app.route('/api/images', methods=['GET'])
def list_images():
    images = conn.compute.images()
    return jsonify({'images': [{'id': image.id, 'name': image.name} for image in images if image.status == 'active']})

@app.route('/api/flavors', methods=['GET'])
def list_flavors():
    flavors = conn.compute.flavors()
    return jsonify({'flavors': [{'id': flavor.id, 'name': flavor.name} for flavor in flavors]})

@app.route('/api/networks', methods=['GET'])
def list_networks():
    networks = conn.network.networks()
    return jsonify({'networks': [{'id': network.id, 'name': network.name} for network in networks]})

@app.route('/api/keys', methods=['GET'])
def list_ssh_keys():
    keys = conn.compute.keypairs()
    return jsonify({'keys': [{'name': key.name} for key in keys]})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port='5000')
