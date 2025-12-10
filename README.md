# E-commerce Backend

FastAPI backend with PostgreSQL, Redis, Elasticsearch, and Stripe integration.

## Features

- **Authentication**: JWT-based auth with user roles (customer/admin)
- **Products**: CRUD operations with image upload (Cloudinary)
- **Search**: Elasticsearch integration with Vietnamese text support
- **Cart & Orders**: Shopping cart and order management
- **Payment**: Stripe payment integration
- **AI Chatbot**: OpenAI-powered product recommendations
- **Caching**: Redis for performance optimization

## Tech Stack

- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache**: Redis
- **Search**: Elasticsearch (Elastic Cloud)
- **Storage**: Cloudinary (images)
- **Payment**: Stripe
- **AI**: OpenAI GPT

## Setup

### Prerequisites

- Python 3.9+
- PostgreSQL database
- Redis instance
- Elasticsearch cluster (Elastic Cloud)
- Cloudinary account
- Stripe account

### Installation

1. **Clone repository**
```bash
git clone <your-backend-repo>
cd ecommerce-backend
```

2. **Create virtual environment**
```bash
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required variables:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `ELASTICSEARCH_URL`: Elastic Cloud endpoint
- `ELASTICSEARCH_API_KEY`: Elastic Cloud API key
- `CLOUDINARY_URL`: Cloudinary credentials
- `STRIPE_SECRET_KEY`: Stripe API key
- `OPENAI_API_KEY`: OpenAI API key

5. **Run database migrations**
```bash
alembic upgrade head
```

6. **Initialize Elasticsearch index**
```bash
python scripts/reindex_products.py --confirm
```

7. **Start server**
```bash
# Development
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Elasticsearch Setup (Elastic Cloud)

### Create Deployment

1. Go to [Elastic Cloud Console](https://cloud.elastic.co)
2. Create new deployment
3. Choose region (e.g., us-central1 GCP)
4. Note the Elasticsearch endpoint URL

### Create API Key

1. In deployment, go to **Management** > **Dev Tools**
2. Run this command to create API key:

```json
POST /_security/api_key
{
  "name": "ecommerce-backend",
  "role_descriptors": {
    "ecommerce_writer": {
      "cluster": ["all"],
      "index": [
        {
          "names": ["products"],
          "privileges": ["all"]
        }
      ]
    }
  }
}
```

3. Copy the returned `encoded` key to `.env` as `ELASTICSEARCH_API_KEY`

### Configure Connection

Update `.env`:
```bash
ELASTICSEARCH_URL=https://your-deployment.es.region.gcp.elastic-cloud.com:9243
ELASTICSEARCH_API_KEY=<your-encoded-api-key>
ELASTICSEARCH_INDEX_PRODUCTS=products
```

### Index Products

```bash
python scripts/reindex_products.py --confirm
```

This will:
- Create `products` index with Vietnamese analyzer
- Bulk index all products from PostgreSQL
- Enable full-text search with typo tolerance

## API Endpoints

### Authentication
- `POST /register` - Register new user
- `POST /login` - Login and get JWT token

### Products
- `GET /products` - List products with filters
- `GET /products/{slug}` - Get product details
- `POST /products` - Create product (admin only)
- `PUT /products/{id}` - Update product (admin only)
- `DELETE /products/{id}` - Delete product (admin only)

### Search (Elasticsearch)
- `GET /search/products?q={query}` - Search products
- `GET /search/autocomplete?q={query}` - Autocomplete suggestions
- `GET /search/aggregations` - Get facets (categories, price ranges)
- `GET /search/health` - Check ES cluster health

### Cart & Orders
- `GET /cart` - Get user's cart
- `POST /cart/items` - Add item to cart
- `POST /orders` - Create order
- `GET /orders` - List user's orders

### Payment
- `POST /create-checkout-session` - Create Stripe checkout
- `POST /webhook` - Stripe webhook handler

## Project Structure

```
ecommerce-backend/
├── app/
│   ├── models/         # SQLAlchemy models
│   ├── schemas/        # Pydantic schemas
│   ├── routers/        # API endpoints
│   ├── services/       # Business logic
│   ├── search/         # Elasticsearch integration
│   │   ├── elastic_client.py
│   │   ├── product_index.py
│   │   └── product_sync.py
│   ├── cache/          # Redis caching
│   └── db/             # Database connection
├── alembic/            # Database migrations
├── scripts/            # Utility scripts
│   └── reindex_products.py
├── tests/              # Unit tests
├── requirements.txt
├── main.py
└── .env.example
```

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_product_service.py

# With coverage
pytest --cov=app tests/
```

## Deployment

### Render.com (Recommended)

1. Create new **Web Service**
2. Connect GitHub repository
3. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables from `.env`
5. Deploy

### Docker

```bash
# Build image
docker build -t ecommerce-backend .

# Run container
docker run -p 8000:8000 --env-file .env ecommerce-backend
```

## Troubleshooting

### Elasticsearch Connection Issues

**Problem**: `NotFoundError(404, "Unknown resource")`

**Solutions**:
1. Verify Elasticsearch URL format (should be `https://...elastic-cloud.com:9243`)
2. Check API key has proper permissions (`cluster: all`, `index: all` on `products`)
3. Ensure deployment is healthy in Elastic Cloud console
4. Try regenerating API key with full permissions

**Test connection**:
```bash
curl -H "Authorization: ApiKey YOUR_API_KEY" \
  https://your-deployment.es.region.gcp.elastic-cloud.com:9243/_cluster/health
```

### Database Connection Issues

Check `DATABASE_URL` format:
```
postgresql://username:password@host:port/database
```

### Redis Connection Issues

Verify `REDIS_URL`:
```
redis://username:password@host:port
```

## License

MIT
