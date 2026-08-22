# python_scripts/embedding_service.py
import os
from typing import List
from openai import OpenAI
from cohere import Client  #← alternative if you prefer Cohere

# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# If you prefer Cohere, uncomment and configure:
co = Client(api_key=os.getenv("COHERE_API_KEY"))

def get_embedding(text: str, model: str = "text-embedding-3-small") -> List[float]:
    """
    Generate embedding using OpenAI (recommended) or Cohere.
    Returns a list of floats (vector).
    """
    if not text.strip():
        raise ValueError("Cannot embed empty text")

    # try:
    #     response = client.embeddings.create(
    #         input=text,
    #         model=model,
    #         dimensions=1536  # or 512 for smaller model
    #     )
    #     return response.data[0].embedding

    # except Exception as e:
    #     raise RuntimeError(f"Embedding failed: {str(e)}")

    # Cohere alternative (if you switch):
    response = co.embed(
        texts=[text],
        model="embed-english-v3.0",
        input_type="search_document"
    )
    return response.embeddings[0]