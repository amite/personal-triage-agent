import chromadb
import openai
import os
from pprint import pprint
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize ChromaDB client
client = chromadb.Client()

# Create a collection
collection = client.create_collection(name="my_collection")

# Define products
products = [
    "Fresh organic apples, rich in vitamins and fiber, perfect for a healthy snack",
    "Crisp and juicy carrots, ideal for salads or as a nutritious side dish",
    "Sweet and ripe bananas, a great source of potassium and natural energy",
    "Premium beef steak, grass-fed and perfect for grilling or pan-searing",
    "Organic spinach, packed with iron and vitamins, great for smoothies or salads",
    "Latest iPhone with advanced camera features, A15 chip, and 5G connectivity",
    "Samsung Galaxy S22, featuring a dynamic AMOLED display and powerful performance",
    "Google Pixel 6, known for its AI-powered camera and smooth Android experience",
    "OnePlus 9 Pro, offering fast charging and a fluid 120Hz display",
    "Xiaomi Mi 11, delivering flagship performance at an affordable price"
]

# Add documents to the collection
collection.add(
    ids=[f"id{i}" for i in range(1, len(products) + 1)],
    documents=products,
    metadatas=[{"category": "fruit", "type": "food"},
                {"category": "vegetable", "type": "food"},
                {"category": "fruit", "type": "food"},
                {"category": "meat", "type": "food"},
                {"category": "vegetable", "type": "food"},
                {"category": "smartphone", "type": "electronics"},
                {"category": "smartphone", "type": "electronics"},
                {"category": "smartphone", "type": "electronics"},
                {"category": "smartphone", "type": "electronics"},
                {"category": "smartphone", "type": "electronics"}]
)

# Step 1: Query the vector database (cast a wide net)
user_query = "i want a phone under 20000"
results = collection.query(
    query_texts=[user_query],
    n_results=5  # Get more results than needed
)

print("Raw vector DB results:")
pprint(results)
print("\n" + "="*50 + "\n")


# Step 2: Use LLM to filter and format the response
retrieved_items = results['documents'][0] if results and 'documents' in results and results['documents'] else []

# Show the formatted items for debugging
formatted_items = chr(10).join(f"{i+1}. {item}" for i, item in enumerate(retrieved_items))
print("Formatted items for LLM prompt:")
pprint(formatted_items)
print("\n" + "="*50 + "\n")

prompt = f"""You are a helpful food and electronics store recommendation assistant.

User query: "{user_query}"

Available items from our database:
{formatted_items}

Based on the user's query, select the MOST appropriate items that closely (not perfectly) match their needs and constraints.
Then provide a clear succinct recommendation without suggesting other models.

Respond in a conversational way, suggesting 1-2 items that best fit their request."""

# Call OpenAI API using the new responses API
from openai import OpenAI

# Get API key from environment
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set")

client = OpenAI(api_key=api_key)
response = client.responses.create(
    model="gpt-5-nano",
    input=prompt
)

recommendation = response.output_text
print("LLM-filtered recommendation:")
print(recommendation)