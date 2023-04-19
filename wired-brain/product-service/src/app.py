from flask import Flask, jsonify, request
import logging.config
from sqlalchemy import exc
import configparser
import debugpy
import os
from db import db
from Product import Product

HOST = "0.0.0.0"	# can accept connections from outside our container

# Configure the logging package from the logging ini file
logging.config.fileConfig('/config/logging.ini', disable_existing_loggers=False)

# Get a logger for this module
log = logging.getLogger(__name__) 

# Setup debugger
debug = os.getenv('DEBUG', 'False') # returns value of env variable passed as argument if found, if not found returns second argument
if debug == 'True':
	debugPort = 5678	# conventional port for debugging, but technically could be plenty of other values
	debugpy.listen( (HOST, debugPort) )
	log.info(f"Started debugger on port {debugPort}")


def get_database_url():
	"""
	Loads the database configuration from the db.ini file and returns a database URL.
	:return: A database URL, built from values in the db.ini file
	"""
	# Load our database configuration
	config = configparser.ConfigParser()
	config.read('/config/db.ini')
	database_configuration = config['mysql']

	host     = database_configuration['host']
	username = database_configuration['username']	
	database = database_configuration['database']

	password_file = open('/run/secrets/db_password')
	password = password_file.read()

	database_url = f'mysql://{username}:{password}@{host}/{database}'
	log.info(f"Connecting to database: {database_url}")
	return database_url


app = Flask(__name__) # makes a new flask app that is this script
app.config['SQLALCHEMY_DATABASE_URI'] = get_database_url()
db.init_app(app)


# curl -v http://localhost:80/products
@app.route('/products')
def get_products():
	log.debug("GET /products")
	try:
		products = [ product.json for product in Product.find_all() ] #iterates over list of products and returns a new list that contains all products as json
		return jsonify(products)	#jsonify converts our Python dictionary to a JSON string so Flask can use it
	except exc.SQLAlchemyError:
		errorMessage = "An exception occurred while retrieving all products"
		log.exception(errorMessage)
		return errorMessage, 500	# 500 = "Internal Server Error"


# curl -v http://localhost:80/product/1
@app.route('/product/<int:id>')
def get_product(id):
	log.debug(f"GET /product/{id}")
	try:
		product = Product.find_by_id(id)
		if product:
			return jsonify(product.json), 200
		log.warning(f"GET /product/{id}: Product not found")
		return f'Product with id {id} not found', 404
	except exc.SQLAlchemyError:
		errorMessage = f"An exception occurred while retreiving product with id {id}"
		log.exception(errorMessage)
		return errorMessage, 500	# 500 = "Internal Server Error"
	


# (Linux version)   curl --header "Content-Type: application/json" --request POST --data '{"name": "Product 3"}' -v http://localhost:80/product
# (Windows version) curl --header "Content-Type: application/json" --request POST --data "{\"name\": \"Product 3\"}" -v http://localhost:80/product
@app.route('/product', methods=['POST'])
def post_product():		
	# Retrieve the product from the request body
	request_product = request.json # request object contains all the info about the request
	log.debug(f"POST /product with product: {request_product}")

	# Create a new Product object
	product = Product(None, request_product['name'])

	try:
		# Save the Product to the database
		product.save_to_db()

		# Return jsonified Product
		return jsonify(product.json), 201	# 201 = "Created"
	except:
		errorMessage = f"An exception occurred while creating product with name: {product.name}"
		log.exception(errorMessage)
		return errorMessage, 500	# 500 = "Internal Server Error"


# (Linux version)   curl --header "Content-Type: application/json" --request PUT --data '{"name": "Updated Product 2"}' -v http://localhost:80/product/2
# (Windows version) curl --header "Content-Type: application/json" --request PUT --data "{\"name\": \"Updated Product 2\"}" -v http://localhost:80/product/2
@app.route('/product/<int:id>', methods=['PUT'])	# Note: PUT is indempotent; it updates an existing item in the list.
def put_product(id):	
	# Get the request payload
	updated_product = request.json
	log.debug(f"PUT /product/{id}")

	try:
		existing_product = Product.find_by_id(id)

		if existing_product:
			existing_product.name = updated_product['name']
			existing_product.save_to_db()

			return jsonify(existing_product.json), 200

		log.warning(f"PUT /product/{id}: Existing product not found")
		return f'Product with id {id} not found', 404
	except exc.SQLAlchemyError:
		errorMessage = f"An exception occurred while updating the name of product with id {id} to {updated_product.name}"
		log.exception(errorMessage)
		return errorMessage, 500	# 500 = "Internal Server Error"


# curl --request DELETE -v http://localhost:80/product/2
@app.route('/product/<int:id>', methods=['DELETE'])
def delete_product(id):
	log.debug(f"DELETE /product/{id}")

	try:
		existing_product = Product.find_by_id(id)
		
		if existing_product:
			existing_product.delete_from_db()
			return jsonify( {'message': f'Deleted product with id {id}'} ), 200

		log.warning(f"DELETE /product/{id}: Existing product not found")
		return f'Product with id {id} not found', 404
	except exc.SQLAlchemyError:
		errorMessage = f"An exception occurred while deleting the product with id {id}"
		log.exception(errorMessage)
		return errorMessage, 500	# 500 = "Internal Server Error"


if __name__ == '__main__':
	app.run(debug=False, host=HOST) # This host makes it so that external machines can access this app; needed because a container considers things outside the container to be other machines!