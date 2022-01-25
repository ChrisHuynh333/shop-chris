from flask import Flask, render_template, url_for, redirect, flash, request, abort
from forms import LoginForm, RegistrationForm, EditForm
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import random
import datetime

app = Flask(__name__)
# CSRF_TOKEN to use FlaskForms - stored as env variable
app.config["SECRET_KEY"] = os.environ.get('SECRET_KEY')
# Enable Bootstrap for WTForms
Bootstrap(app)

# Enable SQL Database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL1', "sqlite:///store.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- flask_login script --- #
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Database models
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(250), nullable=False, unique=True)
    password = db.Column(db.String(250), nullable=False)
    orders = db.relationship("Order", backref="user", lazy=True)


class Product(db.Model):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    # category is what is used to pass as a variable. category_title is used as the text on webpages.
    # For example for fruits and vegetables:
    # category = fruits_and_vegetables
    # category_title = Fruits & Vegetables
    category = db.Column(db.String(100), nullable=False)
    category_title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    img = db.Column(db.String(100), nullable=False)


class Order(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)
    items = db.Column(db.String(2000), nullable=False)
    quantity = db.Column(db.String(100), nullable=False)
    total_price = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)


# Used for the footer copyright year. Dynamic so it doesn't need to be manually updated.
copyright_year = datetime.datetime.now().year

# shopping_cart is used throughout the website.
# Items added to the cart will be appended to the shopping_cart list.
shopping_cart = []


# convert_shopping_cart is used to pass a new variable created from the original shopping_cart which contains all the
# user items they have added. If we pass a shopping_cart containing 2 shirts and 3 oranges, the shopping_cart would
# look like this: [orange, orange, orange, shirt, shirt]. convert_shopping_cart will take those items, pass them into
# final_shopping_cart as single items, and then create an additional list (quantity_list) containing the quantities,
# and the quantity for any respective item would be at the same index.
# Therefore, shopping_cart = [orange, orange, orange, shirt, shirt] would be converted into the following:
# final_shopping_cart = [orange, shirt]
# quantity_list = [3, 2]
# This seemed like a better way to list quantities for each item on the cart page, and also for Order database entry
# once the order is finalized.
def convert_shopping_cart(shopping_cart):
    final_shopping_cart = []
    quantity_list = []
    # sort shopping_cart in alphabetical order and group multiples of the same items together
    shopping_cart.sort()
    # each item in shopping_cart will have a minimum quantity of 1. This is used to keep count of each item's quantity.
    quantity = 1
    # count is used and increased by one per shopping_cart iteration for specifically the last item in shopping_cart,
    # the algorithm logic does not work well without it
    count = -1
    for item in shopping_cart:
        # 1. This is specifically if there's only a single item with quantity of 1. Required as the rest of the for loop
        # does not account for this.
        if len(shopping_cart) == 1:
            final_shopping_cart.append(item)
            quantity_list.append(1)
        else:
            count += 1
            # 2. first item in the shopping cart is always appended
            if not final_shopping_cart:
                final_shopping_cart.append(item)
            # 3. logic for the last item in shopping_cart
            elif count == (len(shopping_cart) - 1):
                # if the item already exists in shopping_cart, the quantity is increased by one and this item's
                # quantity is appended to quantity_list
                if item in final_shopping_cart:
                    quantity += 1
                    quantity_list.append(quantity)
                # if the item does not exist in shopping_cart, the quantity of the previous item is appended, and
                # because the current/last item does not exist in the cart, a quantity of 1 is then appended to
                # quantity_list for the last item, and the item itself is appended to the final_shopping_cart list
                else:
                    quantity_list.append(quantity)
                    quantity_list.append(1)
                    final_shopping_cart.append(item)
            # 4. if item exists in shopping_cart already, quantity is increased by 1
            elif item in final_shopping_cart:
                quantity += 1
            # 5. if the current item does not exist in the final_shopping_cart, the previous item's quantity is
            # appended to quantity_list, quantity is reset to 1, and the new item is appended to final_shopping_cart
            elif item not in final_shopping_cart and quantity > 1:
                quantity_list.append(quantity)
                quantity = 1
                final_shopping_cart.append(item)
            # 6. this is identical to step 4. but if the quantity is = 1, the quantity does not need to be reset
            else:
                quantity_list.append(quantity)
                final_shopping_cart.append(item)

    # List comprehension. Since we initially passed strings to the shopping cart, we turn them into the
    # SQL database entries to access the images, descriptions, etc. for each item in the final_shopping_cart for the
    # cart page.
    final_shopping_cart = [Product.query.filter_by(name=string_item).first() for string_item in
                           final_shopping_cart]
    return final_shopping_cart, quantity_list


# Sums the items and their quantities from their respective lists to give a final price in the cart.
def total_price_calculator(shopping_cart_to_calculate, quantity_list_to_calculate):
    calculated_price = 0
    for item in shopping_cart_to_calculate:
        calculated_price += item.price * quantity_list_to_calculate[shopping_cart_to_calculate.index(item)]
    calculated_price_string = "{:.2f}".format(calculated_price)
    return calculated_price_string


# Home page
@app.route("/")
def home():
    # If the user is logged in, the user is passed to the front page for a specific greeting to the user.
    if current_user.is_authenticated:
        user = User.query.get(current_user.get_id())
    # Otherwise, the user who is not logged in will have the Login / Register / Shop direct links available.
    else:
        user = None
    # Query for all the items in the database.
    items = Product.query.all()
    # We will create a list of 8 random items from the above query to be placed in the "Featured Items" carousel.
    featured_items_list = []
    while len(featured_items_list) < 9:
        random_item = random.choice(items)
        # This ensures we do not add the same item twice into the list if it was already appended.
        if random_item not in featured_items_list:
            featured_items_list.append(random_item)
    # We also want to feature the categories on our home page.
    # We will generate two lists for the categories and the category_titles as both need to be used for the home page.
    categories_list = []
    category_titles_list = []
    for item in items:
        if item.category not in categories_list:
            categories_list.append(item.category)
            category_titles_list.append(item.category_title)
    return render_template("index.html", logged_in=current_user.is_authenticated, cart_size=len(shopping_cart),
                           copyright_year=copyright_year, featured_items=featured_items_list,
                           categories=categories_list, categories_titles=category_titles_list, user=user)


# Routes for shopping by all_items, by product category, or individually
@app.route("/all", methods=["GET", "POST"])
def all_items():
    items = Product.query.all()
    # We generate a list for each of categories and the titles as we will pass the categories for URL generation and
    # also need the titles for headers of each category.
    categories = []
    category_titles = []
    for item in items:
        # Because multiple items will belong to a single category, we need these if statements to ensure only one
        # category will be appended to the lists.
        if item.category_title not in category_titles:
            category_titles.append(item.category_title)
        if item.category not in categories:
            categories.append(item.category)
    # Adds item to cart after clicking add
    if request.method == "POST":
        item = request.form.get('add_button')
        shopping_cart.append(item)
        return render_template("all_items.html", logged_in=current_user.is_authenticated, cart_size=len(shopping_cart),
                               title="All Items", copyright_year=copyright_year, shopping_items=items,
                               categories=sorted(categories), category_titles=sorted(category_titles))
    return render_template("all_items.html", logged_in=current_user.is_authenticated, cart_size=len(shopping_cart),
                           title="All Items", copyright_year=copyright_year, shopping_items=items,
                           categories=sorted(categories), category_titles=sorted(category_titles))


@app.route("/products/<string:category>", methods=["GET", "POST"])
def products(category):
    # Dynamic page that will display items based on category. Items added to cart after clicking add.
    products_list = Product.query.filter_by(category=category)
    if request.method == "POST":
        item = request.form.get('add_button')
        shopping_cart.append(item)
        return render_template("products_by_category.html", logged_in=current_user.is_authenticated,
                               cart_size=len(shopping_cart), title=products_list[0].category_title,
                               copyright_year=copyright_year, products=products_list)
    return render_template("products_by_category.html", logged_in=current_user.is_authenticated,
                           cart_size=len(shopping_cart), title=products_list[0].category_title,
                           copyright_year=copyright_year, products=products_list)


@app.route("/products/<string:category>/<string:item>", methods=["GET", "POST"])
# We do not assign variable category to anything, it's passed to construct the URL so the category appears before the
# specific item (ie: /products/fruits_and_vegetables/apple).
def individual_product(category, item):
    # Dynamic page that will display the specific product with its price, image, and description. Items are added to
    # cart after clicking add
    specific_product = Product.query.filter_by(name=item).first()
    if request.method == "POST":
        item = request.form.get('add_button')
        shopping_cart.append(item)
        return render_template("products_individual.html", logged_in=current_user.is_authenticated,
                               cart_size=len(shopping_cart), title=specific_product.name.title(),
                               copyright_year=copyright_year, product=specific_product)
    return render_template("products_individual.html", logged_in=current_user.is_authenticated,
                           cart_size=len(shopping_cart), title=specific_product.name.title(),
                           copyright_year=copyright_year, product=specific_product)


# --- Route for login, register, account edit and logout --- #
@app.route("/login", methods=["GET", "POST"])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        email = login_form.email.data
        password = login_form.password.data
        user = User.query.filter_by(email=email).first()
        # Errors will show if the email does not exist in our User database or if the password doesn't match with that
        # email.
        if not user:
            flash("Email does not exist.")
        elif not check_password_hash(user.password, password):
            flash("Password does not match this email.")
        # Upon successful login, user is redirected to the home page.
        else:
            login_user(user)
            return redirect(url_for("home"))
    return render_template("login.html", logged_in=current_user.is_authenticated, cart_size=len(shopping_cart),
                           title="Log In", copyright_year=copyright_year, form=login_form)


@app.route("/register", methods=["GET", "POST"])
def register():
    register_form = RegistrationForm()
    if register_form.validate_on_submit():
        # Checks if the user_email is already affiliated with an account. If so, redirects to login window.
        if User.query.filter_by(email=register_form.email.data).first():
            flash("An existing account already contains this Email. Please Login.")
            return redirect(url_for('login'))
        # Adds the new user to the user database
        else:
            new_user = User(
                name=register_form.name.data,
                email=register_form.email.data,
                password=generate_password_hash(register_form.password.data, method='pbkdf2:sha256', salt_length=8)
            )
            db.session.add(new_user)
            db.session.commit()
            # Immediately logs the user in after registration
            login_user(new_user)
            return redirect(url_for("home"))
    return render_template("register.html", logged_in=current_user.is_authenticated, cart_size=len(shopping_cart),
                           title="Register", copyright_year=copyright_year, form=register_form)


@app.route("/edit_account/<int:user_id>", methods=["GET", "POST"])
def edit_account(user_id):
    # Prevents users other than the logged in user from accessing the account when searching directly by URL
    # ie: if the logged in user is user_id = 2, they can not access user_id = 1's account by searching /edit_account/1
    if current_user.id != user_id:
        return abort(403)
    else:
        user = User.query.filter_by(id=user_id).first()
        edit_form = EditForm(name=user.name, email=user.email)
        # Allows users to change their name and/or email. I did not allow password simply because I'll be allowing
        # access to my account to people visiting the site.
        if edit_form.validate_on_submit():
            user = User.query.filter_by(id=user_id).first()
            user.name = edit_form.name.data
            user.email = edit_form.email.data
            db.session.commit()
            return redirect(url_for('account', user_id=user.id))
        return render_template("edit_account.html", user=user, logged_in=current_user.is_authenticated,
                               cart_size=len(shopping_cart), title="Edit Account",
                               copyright_year=copyright_year, form=edit_form)


@app.route("/logout")
# User logs out when they click Logout in the Navbar
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/account/<int:user_id>")
def account(user_id):
    # 403 error if a user is trying to access an account directly by the URL that is not the logged in account.
    if current_user.id != user_id:
        return abort(403)
    else:
        # Accesses all the orders completed by the logged in user from the database.
        user = User.query.filter_by(id=user_id).first()
        orders = Order.query.filter_by(user_id=user_id).all()

        # In our SQL Order database, all variables were passed as single strings separated by a comma.
        # Therefore, when we query for all our orders, we will need to iterate through each order, and separate out
        # the items, their quantities, the order number, and the final price. Each of these will be added to their own
        # respective lists, and we will iterate through each list at a specific index on the account.html page to list
        # the orders.
        # ie: if we have two orders:
        # Order 1: 2 apple and 1 orange,total price of 1.5
        # Order 2: 2 broccoli and 3 carrots, total price 1.75
        # They will be appended to each list as follow:
        # item_list = [[apple, orange], [broccoli, carrots]]
        # quantities_list = [[2, 1], [2, 3]]
        # total_prices = [1.5, 1.75]
        # order_id_list = [1, 2]
        # Therefore, all items at index 0 for each list corresponds to order 1, etc.
        item_list = []
        quantities_list = []
        total_prices = []
        order_id_list = []
        for order in orders:
            # We split by ',' and then remove the last item since it will be an empty string since the last item in each
            # list is always the comma.
            items = order.items.split(",")
            items.remove(items[-1])
            item_list.append(items)
            quantities = order.quantity.split(",")
            quantities.remove(quantities[-1])
            quantities_list.append(quantities)
            total_prices.append(order.total_price)
            order_id_list.append(order.id)
        # We reverse each list so when we display the previous orders, we start with the most previous order at the top
        # of the page.
        item_list.reverse()
        quantities_list.reverse()
        total_prices.reverse()
        order_id_list.reverse()
        list_iterations = len(item_list)
        return render_template("account.html", logged_in=current_user.is_authenticated, cart_size=len(shopping_cart),
                               title=user.name.title(), copyright_year=copyright_year, user=user, items=item_list,
                               quantities=quantities_list, total_prices=total_prices, id=order_id_list,
                               iterations=list_iterations)


# Route for cart
@app.route("/cart", methods=["GET", "POST"])
def cart():
    # Only a logged-in user can access their cart, otherwise we redirect them to the login page first.
    if current_user.is_authenticated:
        if request.method == "POST":
            # The following is when a user types in a new quantity into the quantity field and updates their cart.
            if request.form.get('update_button'):
                # Once the update_button is clicked, we query for that item and get the new quantity.
                item = Product.query.filter_by(name=request.form.get('update_button')).first()
                quantity = request.form.get(item.name + '_quantity')
                # The following is based on the convert_shopping_cart logic. If 5 shirts exist in shopping_cart,
                # they exist as 5 separate string entries (ie: [shirt, shirt, shirt, shirt, shirt]. Therefore,
                # if we change our quantity from 5 to 2, we will first iterate through the shopping_cart to remove all
                # 5 shirts from the shopping_cart list, and then append 2 new shirts.
                if item.name in shopping_cart:
                    try:
                        while True:
                            shopping_cart.remove(item.name)
                    except ValueError:
                        pass
                # If the new quantity is 0, we will remove the items with the above script, and then not append any new
                # items. However, if the updated quantity is non-0, we will append that item in the quantity number of
                # times to the shopping cart.
                if quantity == 0:
                    pass
                else:
                    for x in range(0, int(quantity)):
                        shopping_cart.append(item.name)
            # The following is for when the user clicks the place_order button to finalize their order.
            else:
                # The final_shopping_cart, quantity_list, and total_price are all finalized for database entry
                # once the order is finalized.
                final_shopping_cart, quantity_list = convert_shopping_cart(shopping_cart)
                total_price = total_price_calculator(final_shopping_cart, quantity_list)
                # Entries in the quantity_list are turned into strings for database entry.
                quantity_list = [str(quantity_item) for quantity_item in quantity_list]

                # Because our database will only accept strings, we have to concatenate all the items and quantities
                # into a single string. We separate each entry with a comma for simple separating when we need access
                # to previous orders for the user's account page.
                item_database_entry = ""
                quantity_database_entry = ""
                for item in final_shopping_cart:
                    item_database_entry += item.name + ","
                for entry in quantity_list:
                    quantity_database_entry += entry + ","
                new_order = Order(
                    items=item_database_entry,
                    quantity=quantity_database_entry,
                    total_price=total_price,
                    user_id=current_user.id
                )
                db.session.add(new_order)
                db.session.commit()
                # After the order is complete, we delete the items in the shopping_cart to return it to empty.
                # We used a while loop because the shopping_cart would sometimes bug and not remove some items near the
                # end of its list. The while loop ensures all items are deleted.
                while shopping_cart:
                    for item in shopping_cart:
                        try:
                            shopping_cart.remove(item)
                        except ValueError:
                            pass
                return render_template("order_complete.html", logged_in=current_user.is_authenticated,
                                       cart_size=len(shopping_cart), title=f"Order #{new_order.id} Complete!",
                                       copyright_year=copyright_year, order_num=new_order.id, user=current_user)

        # This displays the cart page with all the items currently in the cart
        final_shopping_cart, quantity_list = convert_shopping_cart(shopping_cart)
        total_price = total_price_calculator(final_shopping_cart, quantity_list)

        return render_template("cart.html", logged_in=current_user.is_authenticated, cart_size=len(shopping_cart),
                               title="Cart", copyright_year=copyright_year, cart=final_shopping_cart,
                               quantity=quantity_list, total_price=total_price)
    else:
        flash("Please login in to checkout.")
        return redirect(url_for('login'))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
