import requests
from bs4 import BeautifulSoup
import pymongo

# Define a list of base URLs
base_urls = [
    "https://www.javatpoint.com/aptitude/numbers-",
    "https://www.javatpoint.com/aptitude/average-",
    "https://www.javatpoint.com/aptitude/compound-interest-",
    "https://www.javatpoint.com/aptitude/partnership-",
    "https://www.javatpoint.com/aptitude/problem-on-ages-",
    "https://www.javatpoint.com/aptitude/boats-and-streams-",
    "https://www.javatpoint.com/aptitude/profit-and-loss-"
    "https://www.javatpoint.com/aptitude/speed-time-and-distance-"
    "https://www.javatpoint.com/aptitude/simple-interest-",
    "https://www.javatpoint.com/aptitude/alligation-and-mixture-",
    "https://www.javatpoint.com/aptitude/area-",
    "https://www.javatpoint.com/aptitude/ratio-and-proportion-",
    "https://www.javatpoint.com/aptitude/decimal-fraction-",
    
]

# Define the range of page numbers (1 to 8 in this case)
start_page = 1
end_page = 8

# Initialize a list to store the scraped data
all_scraped_data = []

# Iterate through each base URL
for base_url in base_urls:
    for page_number in range(start_page, end_page + 1):
        # Construct the URL for the current page
        url = f"{base_url}{page_number}"

        # Send an HTTP GET request to the URL
        response = requests.get(url)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(response.text, "html.parser")

            # Find all the question elements (adjust this based on the HTML structure)
            question_elements = soup.find_all("p", class_="pq")

            # Find all the option elements (adjust this based on the HTML structure)
            option_elements = soup.find_all("ol", type="A") or soup.find_all("ol", class_="pointsu") or soup.find_all("ol", class_="pointsa")

            # Find all the answer elements (adjust this based on the HTML structure)
            answer_elements = soup.find_all("div", class_="testanswer")

            # Loop through each question, option, and answer element
            for i in range(len(question_elements)):
                question = question_elements[i].text.strip()
                options = [opt.text.strip() for opt in option_elements[i].find_all("li")]

                # Extract the correct answer from the answer text and remove parentheses if present
                answer_text = answer_elements[i].find("p").text
                correct_answer = answer_text.split()[-1]  # Get the last word as the correct answer
                # Remove parentheses if present
                if correct_answer.startswith("(") and correct_answer.endswith(")"):
                    correct_answer = correct_answer[1:-1]

                # Create a dictionary to store the data
                data = {
                    "Question": question,
                    "Option A": options[0],
                    "Option B": options[1],
                    "Option C": options[2],
                    "Option D": options[3],
                    "Correct Answer": correct_answer
                }

                # Append the data to the list
                all_scraped_data.append(data)

        else:
            print(f"Failed to retrieve data from {url}")

# Connect to MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["Aptitude"]
collection = db["scraped_questions"]

# Insert all scraped data into the MongoDB collection
collection.insert_many(all_scraped_data)

# Close the MongoDB connection
client.close()

print(f"{len(all_scraped_data)} questions saved to MongoDB.")
