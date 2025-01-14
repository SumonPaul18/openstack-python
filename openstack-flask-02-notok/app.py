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

@app.route('/instances/<instance_id>', methods=['GET'])
def get_instance(instance_id):
    instance = conn.compute.get_server(instance_id)
    if instance:
        instance_info = {'name': instance.name, 'status': instance.status, 'id': instance.id}
        return jsonify(instance_info)
    else:
        return jsonify({'error': 'Instance not found'}), 404

@app.route('/create_instance', methods=['GET', 'POST'])
def create_instance():
    if request.method == 'POST':
        name = request.form['name']
        image_id = request.form['image']
        flavor_id = request.form['flavor']
        network_id = request.form['network']
        package_type = request.form['package']

        instance = conn.compute.create_server(
            name=name,
            image_id=image_id,
            flavor_id=flavor_id,
            networks=[{"uuid": network_id}]
        )
        
        conn.compute.wait_for_server(instance)

        if package_type == 'free':
            # Schedule instance shutdown after 10 minutes
            threading.Timer(600, shutdown_instance, args=[instance.id]).start()

        return jsonify({'name': instance.name, 'status': instance.status, 'id': instance.id})

    images = conn.compute.images()
    flavors = conn.compute.flavors()
    networks = conn.network.networks()
    return render_template('create_instance.html', images=images, flavors=flavors, networks=networks)

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
