# Import necessary libraries
import google.generativeai as genai
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords
import string

# Configure Google Generative AI
genai.configure(api_key='')  # Put in your API Key
model = genai.GenerativeModel('gemini-pro')

# Download stopwords
nltk.download('stopwords')

# Load the dataset
df = pd.read_csv('googleplaystore.csv')

# Define the preprocessing function
def preprocess_text(text):
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    stop_words = set(stopwords.words('english'))
    text = ' '.join([word for word in text.split() if word not in stop_words])
    return text

# Apply preprocessing to relevant text columns
df['processed_name'] = df['App'].apply(preprocess_text)
df['processed_category'] = df['Category'].apply(preprocess_text)
df['processed_genre'] = df['Genres'].apply(preprocess_text)

# Combine text features for similarity comparison
df['combined_features'] = df['processed_name'] + ' ' + df['processed_category'] + ' ' + df['processed_genre']

# Function to get app recommendations and integrate with Gemini for additional info
def recommend_apps_with_gemini(search_text, num_recommendations=5):
    # Preprocess the search text
    search_text = preprocess_text(search_text)

    # Use TF-IDF Vectorizer to transform the combined features into vectors
    tfidf_vectorizer = TfidfVectorizer()
    tfidf_matrix = tfidf_vectorizer.fit_transform(df['combined_features'])

    # Transform the search text into a TF-IDF vector
    search_vector = tfidf_vectorizer.transform([search_text])

    # Calculate cosine similarity between search vector and the dataset
    cosine_similarities = cosine_similarity(search_vector, tfidf_matrix).flatten()

    # Get the indices of the apps with the highest similarity scores
    recommended_indices = cosine_similarities.argsort()[-num_recommendations:][::-1]

    # Get the recommended apps
    recommended_apps = df.iloc[recommended_indices][['App', 'Category', 'Rating', 'Genres']]

    # Create a detailed prompt for Gemini including app names
    app_names = ', '.join(recommended_apps['App'])
    prompt = (
        f"I have the following recommended apps based on the search: {app_names}. "
        f"Can you provide a brief description, their current rating on the Google Play Store, and a link to their images? "
        f"Also, please suggest 3 more similar apps overall that are popular and relevant to these recommendations."
    )

    # Generate content using the Gemini model
    response = model.generate_content(prompt)

    # Extract relevant response information (assuming response has this structure)
    if response and response._result.candidates:
        gemini_text = response._result.candidates[0].content.parts[0].text
    else:
        gemini_text = "No additional information found."

    # Return the recommended apps along with Gemini's additional information
    return recommended_apps, gemini_text

# Example usage with the updated function
search_text = "photo editor"
recommendations, additional_info = recommend_apps_with_gemini(search_text)

# Display the recommendations and additional information
print("Recommended Apps:")
print(recommendations)
print("\nAdditional Info from Gemini:")
print(additional_info)