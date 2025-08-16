import openstack
from flask import Flask, jsonify, request, render_template
from openstack import connection
import threading

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

@app.route('/api/images', methods=['GET'])
def list_images():
    images = conn.compute.images()
    return jsonify({'images': [{'id': image.id, 'name': image.name} for image in images]})

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

@app.route('/create_instance', methods=['POST'])
def create_instance():
    name = request.form['name']
    image_id = request.form['image']
    flavor_id = request.form['flavor']
    network_id = request.form['network']
    package_type = request.form['package']
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

    # Allocate a floating IP and associate it with the instance
    floating_ip = conn.network.create_ip(floating_network_id='public')  # Replace 'public' with your actual floating network ID
    conn.compute.add_floating_ip_to_server(instance, floating_ip.floating_ip_address)

    if package_type == 'free':
        # Schedule instance shutdown after 10 minutes
        threading.Timer(600, shutdown_instance, args=[instance.id]).start()

    return jsonify({'name': instance.name, 'status': instance.status, 'id': instance.id})

def shutdown_instance(instance_id):
    conn.compute.stop_server(instance_id)

@app.route('/instances/<instance_id>', methods=['DELETE'])
def delete_instance(instance_id):
    instance = conn.compute.get_server(instance_id)
    if instance:
        conn.compute.delete_server(instance)
        return jsonify({'status': 'Instance deleted'})
    else:
        return jsonify({'error': 'Instance not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port='5000')
