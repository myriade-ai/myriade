# Vector Search for Catalog Assets

This document explains how to use vector search functionality for catalog assets in Myriade.

## Overview

Vector search provides semantic search capabilities for catalog assets, allowing users to find relevant assets based on meaning rather than just keyword matching. This is especially useful for:

- Finding assets with similar concepts but different terminology
- Discovering related assets based on descriptions
- More intelligent search that understands context

## Requirements

### Database
- **PostgreSQL with pgvector extension** (vector search is PostgreSQL-only)
- For SQLite databases, the system automatically falls back to traditional text search

### Python Dependencies
Install the optional `vector-search` dependencies:

```bash
uv sync --extra vector-search
```

Or install manually:
```bash
pip install sentence-transformers pgvector
```

## Setup

### 1. Enable pgvector Extension

The migration will automatically enable the pgvector extension when you run:

```bash
alembic upgrade head
```

The migration (`d4e5f6g7h8i9_add_vector_search_support.py`) will:
- Enable the pgvector extension (PostgreSQL only)
- Add an `embedding` column to the `asset` table

### 2. Generate Embeddings

After running the migration, you need to generate embeddings for existing assets.

**Option A: Generate embeddings for all assets**
```python
from chat.tools.catalog import CatalogTool

# Initialize the catalog tool with your session, database, and data_warehouse
catalog_tool = CatalogTool(session, database, data_warehouse)

# Generate embeddings for all assets
result = catalog_tool.generate_embeddings_for_all_assets()
print(result)  # "Generated embeddings for X assets (Y failed)"
```

**Option B: Generate embedding for a specific asset**
```python
result = catalog_tool.generate_embeddings_for_asset(asset_id="<uuid>")
```

**Automatic Generation**: Embeddings are automatically generated when assets are created or updated via the `update_asset` method.

## Usage

### Search with Vector Similarity

The `search_assets` method automatically uses vector search when available:

```python
# This will use vector search on PostgreSQL with pgvector
results = catalog_tool.search_assets("customer data")

# Explicitly disable vector search (use text search only)
results = catalog_tool.search_assets("customer data", use_vector_search=False)
```

### Search Behavior

1. **With Vector Search (PostgreSQL + pgvector)**:
   - Searches using semantic similarity
   - Returns results ordered by relevance (cosine similarity)
   - Falls back to text search if embedding generation fails

2. **Without Vector Search (SQLite or pgvector not available)**:
   - Uses traditional text search with SQL `ILIKE`
   - Searches in: asset name, description, URN, and tag names

## Technical Details

### Embedding Model
- **Model**: `all-MiniLM-L6-v2` from sentence-transformers
- **Dimensions**: 384
- **Size**: ~80MB
- **Performance**: Fast, suitable for real-time applications

### Similarity Metric
- Uses cosine distance: `1 - (embedding <=> query_embedding)`
- Lower distance = higher similarity
- Results ordered by similarity score (descending)

### Embedding Content
Embeddings are generated from:
1. Asset name/URN
2. Asset description (if available)

This provides a comprehensive semantic representation of the asset.

## Limitations

1. **PostgreSQL Only**: Vector search requires PostgreSQL with pgvector. SQLite databases will use text search.

2. **Model Loading**: The first search using vector similarity will load the embedding model (~80MB), which may take a few seconds.

3. **Storage**: Each asset's embedding takes ~1.5KB of storage (384 dimensions × 4 bytes per float).

4. **Migration Required**: Existing databases need to run the migration and generate embeddings for existing assets.

## Troubleshooting

### "pgvector extension is not installed"
**Solution**: Enable the extension manually:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### "sentence-transformers not installed"
**Solution**: Install the dependencies:
```bash
uv sync --extra vector-search
```

### Vector search not working
**Check**:
1. Are you using PostgreSQL? (Vector search is PostgreSQL-only)
2. Is the pgvector extension enabled?
3. Do assets have embeddings? Run `generate_embeddings_for_all_assets()`
4. Check logs for any errors during embedding generation

### Slow first search
**Expected Behavior**: The first search loads the embedding model (~80MB), which takes a few seconds. Subsequent searches are fast because the model stays in memory.

## Performance Considerations

1. **Indexing**: For large datasets (>10,000 assets), consider adding an index:
   ```sql
   CREATE INDEX ON asset USING ivfflat (embedding vector_cosine_ops)
   WITH (lists = 100);
   ```

2. **Batch Processing**: When generating embeddings for many assets, the `generate_embeddings_for_all_assets()` method processes them in batches.

3. **Caching**: The embedding model is cached in memory after first load for better performance.

## Future Enhancements

Possible improvements for future versions:
- Support for more embedding models
- Configurable similarity thresholds
- Hybrid search (combining vector + text search)
- Incremental embedding updates
- Support for other vector databases (e.g., Qdrant, Weaviate)
