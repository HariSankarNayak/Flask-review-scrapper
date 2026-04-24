from flask import Flask, render_template, request
from flask_cors import CORS, cross_origin
import requests
from bs4 import BeautifulSoup as bs
import csv
import os

application = Flask(__name__)
CORS(application)

# Common headers to avoid blocking
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}


@application.route('/', methods=['GET'])
@cross_origin()
def homePage():
    return render_template("index.html")


@application.route('/review', methods=['POST', 'GET'])
@cross_origin()
def index():
    if request.method == 'POST':
        try:
            searchString = request.form['content'].strip().replace(" ", "")

            # Step 1: Search page
            flipkart_url = f"https://www.flipkart.com/search?q={searchString}"
            search_res = requests.get(flipkart_url, headers=HEADERS)

            if search_res.status_code != 200:
                return "Failed to fetch search page"

            flipkart_html = bs(search_res.text, "html.parser")

            bigboxes = flipkart_html.find_all("div", {"class": "lvJbLV col-12-12"})
            bigboxes = bigboxes[3:]

            if not bigboxes:
                return "No products found"

            # Step 2: First product
            box = bigboxes[0]

            try:
                productLink = "https://www.flipkart.com" + box.div.div.div.a['href']
            except:
                return "Failed to extract product link"

            # Step 3: Product page
            prodRes = requests.get(productLink, headers=HEADERS)
            prod_html = bs(prodRes.text, "html.parser")

            commentboxes = prod_html.find_all('div', {'class': "vQDoqR"})

            if not commentboxes:
                return "No reviews found"

            # Step 4: Save CSV
            os.makedirs("data", exist_ok=True)
            filename = f"data/{searchString}.csv"

            reviews = []

            with open(filename, "w", newline='', encoding='utf-8') as fw:
                writer = csv.writer(fw)
                writer.writerow(["Product", "Customer Name", "Rating", "Heading", "Comment"])

                for commentbox in commentboxes:

                    # Name
                    try:
                        name = commentbox.find('div', {'class': 'v1zwn27'}).text
                    except:
                        name = "No Name"

                    # Rating
                    try:
                        rating = commentbox.find('div', {'class': 'css-146c3p1'}).text
                    except:
                        rating = "No Rating"

                    # Heading
                    try:
                        commentHead = commentbox.find('div', {'class': 'v1zwn24'}).text
                    except:
                        commentHead = "No Heading"

                    # Comment
                    try:
                        custComment = commentbox.find('div', {'class': 'v1zwn26'}).text
                    except:
                        custComment = "No Comment"

                    # Save row
                    writer.writerow([searchString, name, rating, commentHead, custComment])

                    # Add to list for UI
                    reviews.append({
                        "Product": searchString,
                        "Name": name,
                        "Rating": rating,
                        "CommentHead": commentHead,
                        "Comment": custComment
                    })

            return render_template('results.html', reviews=reviews)

        except Exception as e:
            print("Error:", e)
            return "Something went wrong"

    else:
        return render_template('index.html')


if __name__ == "__main__":
    application.run()