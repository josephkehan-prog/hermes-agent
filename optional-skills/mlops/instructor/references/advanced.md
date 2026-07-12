# Advanced Model & Configuration Patterns

Modeling patterns beyond a flat Pydantic model, plus mode/context configuration
and a comparison to alternative libraries.

## Nested Models

```python
class Address(BaseModel):
    street: str
    city: str
    country: str

class Person(BaseModel):
    name: str
    age: int
    address: Address  # Nested model

person = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": "John lives at 123 Main St, Boston, USA"
    }],
    response_model=Person
)

print(person.address.city)  # "Boston"
```

## Optional Fields

```python
from typing import Optional

class Product(BaseModel):
    name: str
    price: float
    discount: Optional[float] = None  # Optional
    description: str = Field(default="No description")  # Default value

# LLM doesn't need to provide discount or description
```

## Enums for Constraints

```python
from enum import Enum

class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"

class Review(BaseModel):
    text: str
    sentiment: Sentiment  # Only these 3 values allowed

review = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{"role": "user", "content": "This product is amazing!"}],
    response_model=Review
)

print(review.sentiment)  # Sentiment.POSITIVE
```

## Union Types

```python
from typing import Union

class TextContent(BaseModel):
    type: str = "text"
    content: str

class ImageContent(BaseModel):
    type: str = "image"
    url: HttpUrl
    caption: str

class Post(BaseModel):
    title: str
    content: Union[TextContent, ImageContent]  # Either type

# LLM chooses appropriate type based on content
```

## Dynamic Models

```python
from pydantic import create_model

# Create model at runtime
DynamicUser = create_model(
    'User',
    name=(str, ...),
    age=(int, Field(ge=0)),
    email=(EmailStr, ...)
)

user = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[...],
    response_model=DynamicUser
)
```

## Custom Modes

```python
# For providers without native structured outputs
client = instructor.from_anthropic(
    Anthropic(),
    mode=instructor.Mode.JSON  # JSON mode
)

# Available modes:
# - Mode.ANTHROPIC_TOOLS (recommended for Claude)
# - Mode.JSON (fallback)
# - Mode.TOOLS (OpenAI tools)
```

## Context Management

```python
# Single-use client
with instructor.from_anthropic(Anthropic()) as client:
    result = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=[...],
        response_model=YourModel
    )
    # Client closed automatically
```

## Comparison to Alternatives

| Feature | Instructor | Manual JSON | LangChain | DSPy |
|---------|------------|-------------|-----------|------|
| Type Safety | Yes | No | Partial | Yes |
| Auto Validation | Yes | No | No | Limited |
| Auto Retry | Yes | No | No | Yes |
| Streaming | Yes | No | Yes | No |
| Multi-Provider | Yes | Manual | Yes | Yes |
| Learning Curve | Low | Low | Medium | High |

**When to choose Instructor:** need structured, validated outputs; want type
safety and IDE support; require automatic retries; building data extraction
systems.

**When to choose alternatives:** DSPy for prompt optimization, LangChain for
complex chains, manual JSON for simple one-off extractions.
