# Description
This site is my first attempt at creating a fully fledged, functional website. The goal was to create a mock e-commerce store from scratch with similar functionality as an actual live store, tying in the usage of Python's Flask framework with SQL databases. The SQL databases were used to track registered Users information, the users' orders, which is available in their account page, and a database for the store's products/items.

The store's functionality includes:
  - User registration log in and authentication
  - Add to cart feature for all items and the ability to update quantities on the cart page
  - Cart size tracked on navigation bar throughout the entire site
  - Full navigation with various levels for the products
    - Navigate by all items, by category, or by individual item
  - Order number tracking which automatically increases by each order completed
  - User account page displaying their details (name, email, partial encryped password)
  - User account page displaying their order history in descending order

# Known Bugs
  - After completing an order, and being redirected to the order_complete page which states "Order Complete. Order #xx ...", the user can refresh on this page, which will generate a new empty order.
  - On a product page, after adding an item to the cart, the user can refresh, which will prompt a resubmission confirmation through the browser, and if once confirmed, another single quantity of the same item will be added to the cart.
  - The following an issue when the site was deployed, and not when hosted locally.
    - After website deployment, the website's cart is extremely buggy. It's almost like the cart is refreshing between different instances. 
    -   Examples of this include:
      -    Adding to cart and updating cart will sometimes delete items/change the cart quantities.
      -    Navigating between pages will flip-flop the cart quantity.
      -    After completing an order, the cart will sometimes not empty, however, when you place another order, the order is empty.

# Improvements to be made
  - I used raw HTML and CSS bootstrap coding of my own rather than using a template/theme as I wanted to get more practice with HTML/CSS. Therefore, this is an area that can be improved on the website.
  - The code should be refactored and 'fixed' further. Although functional, many of the list elements should be condensed from multiple lists into single dictionaries.
  - In addition to the above point, the website's responsiveness can be improved.
  - The addition of a front-end language would help better the quality of life for the website.
    - This would include not refreshing the page to the top every time an item is updated or added to cart.
    - Pop-up on the cart every time an item is added.
    - I'm assuming the bugs happening on the site after deployment could be resolved with the addition of a front-end language to 'smooth' navigation/browsing. 

# Technologies Used
  - Python
  - Flask
  - SQL
  - HTML
  - CSS
