from flask import Flask, render_template, request, redirect, url_for, jsonify
from selenium import webdriver
from bs4 import BeautifulSoup
from pymongo import MongoClient

app = Flask(__name__)

client = MongoClient('mongodb://localhost:27017/')
db = client['pricemonitoring']
users_collection = db['users']
products_collection = db['products']

PER_PAGE = 25

@app.route('/')
def index():
    return render_template('index.html')
@app.route('/products')
def get_products():
    products = products_collection.find()
    formatted_products = []
    for product in products:
        # Convert binary image data to base64
        with open(product['image'], 'rb') as f:
            image_data = f.read()
        base64_image = base64.b64encode(image_data).decode('utf-8')

        # Add base64 image data to product document
        product['image'] = base64_image
        formatted_products.append(product)

    return jsonify({'products': formatted_products})

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    users = users_collection.find()
    for user in users:
        if user['username']==username and user['password']==password : 
            return redirect(url_for('monitoring'))
    
    message = "Invalid Credentials! Try Again!"
    return render_template('index.html', message=message)

@app.route('/logout')
def logout():
    return redirect(url_for('index'))

@app.route('/monitoring')
def monitoring():
      # Pagination logic
    page = request.args.get('page', default=1, type=int)
    skip_count = (page - 1) * PER_PAGE
    
    total_products = products_collection.count_documents({})
    total_pages = ((total_products + PER_PAGE - 1) // PER_PAGE)
    end_page = min(6, total_pages + 1)  # Calculate the end page
    
    products = products_collection.find().skip(skip_count).limit(PER_PAGE)
    
    return render_template('monitoring.html', products=products, page=page, total_pages=total_pages, end_page=end_page)

    products = products_collection.find()
    return render_template('monitoring.html',products=products)

@app.route('/ebay')
def get_ebay_price():
    url="https://www.ebay.com/itm/256458485567"
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  
    driver = webdriver.Chrome(options=options)

    driver.get(url)
    html = driver.page_source
    driver.quit()  
    soup = BeautifulSoup(html, 'html.parser')

    price_element = soup.find("div", {"class": "x-price-primary"})
    if price_element:
        return jsonify({'ebay_price': price_element.text})
    else:
        return "NaN"
    
@app.route('/amazon')
def get_amazon_price():
    url = "https://www.amazon.com/Epson-DURABrite-Ultra-Capacity-Cartridge/dp/B08DX5F6XV"
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  
    driver = webdriver.Chrome(options=options)

    driver.get(url)
    html = driver.page_source
    driver.quit() 
    soup = BeautifulSoup(html, 'html.parser')

    price_element = soup.find("span", {"id": "style_name_0_price"})
    if price_element:
        price_text = price_element.find("span", {"class": "a-size-mini olpWrapper"}).text.strip()
        amazon_price = price_text.split("from ")[1].split(" ")[0]
        return jsonify({'amazon_price': amazon_price})
    else:
        return "NaN"

@app.route('/cityblue')
def get_citybluetechnologies_price():
    product_url ="https://citybluetechnologies.com/product/t812-exra-high-capacity-black-ink-cartridge-sensormatic/"

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  
    driver = webdriver.Chrome(options=options)

    driver.get(product_url)
    html = driver.page_source
    driver.quit()  
    soup = BeautifulSoup(html, 'html.parser')

    price_element = soup.find("span", {"class": "woocommerce-Price-amount amount"})
    if price_element:
        return jsonify({'cityblue_price':price_element.text.strip()})
    else:
        return "NaN"

@app.route('/update_price', methods=['POST'])
def update_price():
    product_id = request.json['product_id']
    new_price = request.json['new_price']
    db.products.update_one({'id': product_id}, {'$set': {'updated_cityblue': new_price}})
    return {"data":"Updated"}


if __name__ == '__main__':
    app.run(debug=True)

    #search functionality
@app.route('/search', methods=['POST'])
def search_products():
    search_query = request.json.get('query', '')
    results = products_collection.find({"$text": {"$search": search_query}})
    products = list(results)
    return jsonify(products)

if __name__ == '__main__':
    app.run(debug=True)  
