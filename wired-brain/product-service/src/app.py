from flask import Flask, jsonify, request
from db import db
from Product import Product


app = Flask(__name__) # makes a new flask app that is this script
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:password@db/products' # connect to mysql in the db container, using username root and password password, and use the products data
db.init_app(app)


# curl -v http://localhost:80/products
@app.route('/products')
def get_products():
	products = [ product.json for product in Product.find_all() ] #iterates over list of products and returns a new list that contains all products as json
	return jsonify(products)	#jsonify converts our Python dictionary to a JSON string so Flask can use it


# curl -v http://localhost:80/product/1
@app.route('/product/<int:id>')
def get_product(id):
	product = Product.find_by_id(id)
	if product:
		return jsonify(product.json), 200
	return f'Product with id {id} not found', 404
	


# (Linux version)   curl --header "Content-Type: application/json" --request POST --data '{"name": "Product 3"}' -v http://localhost:80/product
# (Windows version) curl --header "Content-Type: application/json" --request POST --data "{\"name\": \"Product 3\"}" -v http://localhost:80/product
@app.route('/product', methods=['POST'])
def post_product():
	print('POST /product')
	
	# Retrieve the product from the request body
	request_product = request.json # request object contains all the info about the request

	# Create a new Product
	product = Product(None, request_product['name'])

	# Save the Product to the database
	product.save_to_db()

	# Return jsonified Product
	return jsonify(product.json), 201 # 201 = "Created"


# (Linux version)   curl --header "Content-Type: application/json" --request PUT --data '{"name": "Updated Product 2"}' -v http://localhost:80/product/2
# (Windows version) curl --header "Content-Type: application/json" --request PUT --data "{\"name\": \"Updated Product 2\"}" -v http://localhost:80/product/2
@app.route('/product/<int:id>', methods=['PUT'])
def put_product(id):	
	existing_product = Product.find_by_id(id)

	if existing_product:
		# Get the request payload
		updated_product = request.json

		existing_product.name = updated_product['name']
		existing_product.save_to_db()

		return jsonify(existing_product.json), 200

	return f'Product with id {id} not found', 404


# curl --request DELETE -v http://localhost:80/product/2
@app.route('/product/<int:id>', methods=['DELETE'])
def delete_product(id):
	existing_product = Product.find_by_id(id)
	
	if existing_product:
		existing_product.delete_from_db()
		return jsonify( {f'Deleted product with id {id}'} ), 200

	return f'Product with id {id} not found', 404


if __name__ == '__main__':
	app.run(debug=True, host='0.0.0.0') # This host makes it so that external machines can access this app; needed because a container considers things outside the container to be other machines!