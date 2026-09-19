"""
Encode Benzinga news data using FinBERT embeddings
Supports both sentence-transformers and raw FinBERT extraction
"""

import pandas as pd
import numpy as np
import torch
from transformers import BertTokenizer, BertModel
from sentence_transformers import SentenceTransformer
from typing import List, Tuple
import sqlite3
import pickle
from tqdm import tqdm
import argparse


class FinBERTEncoder:
    """Encoder using FinBERT for financial news embeddings."""
    
    def __init__(self, model_type='finbert', use_gpu=True):
        """
        Initialize the encoder.
        
        Args:
            model_type: 'finbert' for raw FinBERT, 'sentence-transformer' for optimized embeddings
            use_gpu: Use GPU if available
        """
        self.device = 'cuda' if use_gpu and torch.cuda.is_available() else 'cpu'
        print(f"Using device: {self.device}")
        
        self.model_type = model_type
        
        if model_type == 'finbert':
            # Raw FinBERT - extract embeddings manually
            print("Loading ProsusAI/finbert...")
            self.tokenizer = BertTokenizer.from_pretrained('ProsusAI/finbert')
            self.model = BertModel.from_pretrained('ProsusAI/finbert')
            self.model.to(self.device)
            self.model.eval()
            self.embedding_dim = 768  # FinBERT hidden size
            
        elif model_type == 'sentence-transformer':
            # Optimized for embeddings
            print("Loading sentence-transformers model...")
            self.model = SentenceTransformer('all-mpnet-base-v2')
            self.model.to(self.device)
            self.embedding_dim = 768
            
        else:
            raise ValueError(f"Unknown model_type: {model_type}")
    
    def encode_text(self, text: str) -> np.ndarray:
        """
        Encode a single text into embedding.
        
        Args:
            text: Input text string
            
        Returns:
            Embedding vector as numpy array
        """
        if self.model_type == 'finbert':
            return self._encode_finbert(text)
        else:
            return self._encode_sentence_transformer(text)
    
    def _encode_finbert(self, text: str) -> np.ndarray:
        """Extract embedding from raw FinBERT model."""
        # Tokenize
        inputs = self.tokenizer(
            text,
            return_tensors='pt',
            truncation=True,
            max_length=512,
            padding=True
        ).to(self.device)
        
        # Get embeddings
        with torch.no_grad():
            outputs = self.model(**inputs)
            # Use [CLS] token embedding (first token)
            embedding = outputs.last_hidden_state[:, 0, :].cpu().numpy()[0]
        
        return embedding
    
    def _encode_sentence_transformer(self, text: str) -> np.ndarray:
        """Encode using sentence-transformers (optimized)."""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding
    
    def encode_batch(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Encode multiple texts efficiently.
        
        Args:
            texts: List of text strings
            batch_size: Batch size for processing
            
        Returns:
            Array of embeddings (n_texts, embedding_dim)
        """
        if self.model_type == 'sentence-transformer':
            # Sentence transformers has built-in batching
            return self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=True,
                convert_to_numpy=True
            )
        else:
            # Manual batching for raw FinBERT
            embeddings = []
            for i in tqdm(range(0, len(texts), batch_size)):
                batch = texts[i:i + batch_size]
                batch_embeddings = [self.encode_text(text) for text in batch]
                embeddings.extend(batch_embeddings)
            return np.array(embeddings)


def load_csv_data(csv_path: str) -> pd.DataFrame:
    """Load and validate CSV data."""
    print(f"Loading CSV from {csv_path}...")
    df = pd.read_csv(csv_path)
    
    # Validate required columns
    required_cols = ['id', 'title', 'teaser']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    # Handle missing values
    df['title'] = df['title'].fillna('')
    df['teaser'] = df['teaser'].fillna('')
    
    print(f"Loaded {len(df)} articles")
    return df


def encode_csv_to_sqlite(
    csv_path: str,
    db_path: str,
    model_type: str = 'sentence-transformer',
    combine_fields: bool = True,
    batch_size: int = 32,
    use_float16: bool = True
):
    """
    Encode CSV data and store in SQLite with embeddings.
    
    Args:
        csv_path: Path to input CSV file
        db_path: Path to output SQLite database
        model_type: 'finbert' or 'sentence-transformer'
        combine_fields: If True, combine title+teaser; if False, encode separately
        batch_size: Batch size for encoding
        use_float16: Use float16 to save storage (recommended)
    """
    # Load data
    df = load_csv_data(csv_path)
    
    # Initialize encoder
    encoder = FinBERTEncoder(model_type=model_type)
    
    # Prepare texts to encode
    if combine_fields:
        print("Combining title + teaser for encoding...")
        texts = (df['title'] + ' ' + df['teaser']).tolist()
        
        # Encode
        print(f"Encoding {len(texts)} texts...")
        embeddings = encoder.encode_batch(texts, batch_size=batch_size)
        
        if use_float16:
            print("Converting to float16 for storage efficiency...")
            embeddings = embeddings.astype(np.float16)
        
        # Add to dataframe
        df['combined_embedding'] = [pickle.dumps(emb) for emb in embeddings]
        
    else:
        print("Encoding title and teaser separately...")
        
        # Encode titles
        print("Encoding titles...")
        title_embeddings = encoder.encode_batch(df['title'].tolist(), batch_size=batch_size)
        
        # Encode teasers
        print("Encoding teasers...")
        teaser_embeddings = encoder.encode_batch(df['teaser'].tolist(), batch_size=batch_size)
        
        if use_float16:
            print("Converting to float16...")
            title_embeddings = title_embeddings.astype(np.float16)
            teaser_embeddings = teaser_embeddings.astype(np.float16)
        
        # Add to dataframe
        df['title_embedding'] = [pickle.dumps(emb) for emb in title_embeddings]
        df['teaser_embedding'] = [pickle.dumps(emb) for emb in teaser_embeddings]
    
    # Store in SQLite
    print(f"Storing in SQLite database: {db_path}")
    conn = sqlite3.connect(db_path)
    
    # Store main data
    df.to_sql('news_embeddings', conn, if_exists='replace', index=False)
    
    # Create indexes
    print("Creating indexes...")
    conn.execute('CREATE INDEX IF NOT EXISTS idx_created ON news_embeddings(created)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_id ON news_embeddings(id)')
    
    # Store metadata
    metadata = {
        'model_type': model_type,
        'embedding_dim': encoder.embedding_dim,
        'combine_fields': combine_fields,
        'use_float16': use_float16,
        'total_articles': len(df),
        'encoded_at': pd.Timestamp.now().isoformat()
    }
    
    metadata_df = pd.DataFrame([metadata])
    metadata_df.to_sql('encoding_metadata', conn, if_exists='replace', index=False)
    
    conn.commit()
    conn.close()
    
    print(f"✅ Successfully encoded {len(df)} articles")
    print(f"📊 Embedding dimension: {encoder.embedding_dim}")
    print(f"💾 Database saved to: {db_path}")
    
    # Calculate storage size
    import os
    db_size_mb = os.path.getsize(db_path) / (1024 * 1024)
    print(f"📦 Database size: {db_size_mb:.2f} MB")


def test_similarity_search(db_path: str, query: str, top_k: int = 5):
    """
    Test similarity search on encoded database.
    
    Args:
        db_path: Path to SQLite database
        query: Search query text
        top_k: Number of results to return
    """
    # Load database
    conn = sqlite3.connect(db_path)
    
    # Load metadata
    metadata = pd.read_sql('SELECT * FROM encoding_metadata', conn).iloc[0]
    print(f"Model: {metadata['model_type']}, Dim: {metadata['embedding_dim']}")
    
    # Load all embeddings
    df = pd.read_sql('SELECT * FROM news_embeddings', conn)
    
    # Decode embeddings
    if 'combined_embedding' in df.columns:
        embeddings = np.array([pickle.loads(blob) for blob in df['combined_embedding']])
    else:
        embeddings = np.array([pickle.loads(blob) for blob in df['title_embedding']])
    
    # Encode query
    encoder = FinBERTEncoder(model_type=metadata['model_type'])
    query_embedding = encoder.encode_text(query)
    
    if metadata['use_float16']:
        query_embedding = query_embedding.astype(np.float16)
    
    # Calculate cosine similarity
    from sklearn.metrics.pairwise import cosine_similarity
    similarities = cosine_similarity([query_embedding], embeddings)[0]
    
    # Get top results
    top_indices = similarities.argsort()[-top_k:][::-1]
    
    print(f"\n🔍 Top {top_k} results for: '{query}'")
    print("=" * 80)
    
    for i, idx in enumerate(top_indices, 1):
        score = similarities[idx]
        article = df.iloc[idx]
        print(f"\n{i}. Score: {score:.4f}")
        print(f"   Title: {article['title'][:100]}...")
        print(f"   Date: {article['created']}")
        if 'ticker_symbols' in article and pd.notna(article['ticker_symbols']):
            print(f"   Tickers: {article['ticker_symbols']}")
    
    conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Encode news CSV with FinBERT embeddings')
    parser.add_argument('--csv', required=True, help='Input CSV file path')
    parser.add_argument('--db', required=True, help='Output SQLite database path')
    parser.add_argument('--model', default='sentence-transformer', 
                       choices=['finbert', 'sentence-transformer'],
                       help='Model type to use')
    parser.add_argument('--separate', action='store_true',
                       help='Encode title and teaser separately (default: combined)')
    parser.add_argument('--batch-size', type=int, default=32,
                       help='Batch size for encoding')
    parser.add_argument('--no-float16', action='store_true',
                       help='Use float32 instead of float16')
    parser.add_argument('--test-query', type=str,
                       help='Test with a similarity search query')
    
    args = parser.parse_args()
    
    # Encode
    encode_csv_to_sqlite(
        csv_path=args.csv,
        db_path=args.db,
        model_type=args.model,
        combine_fields=not args.separate,
        batch_size=args.batch_size,
        use_float16=not args.no_float16
    )
    
    # Test if query provided
    if args.test_query:
        test_similarity_search(args.db, args.test_query)
