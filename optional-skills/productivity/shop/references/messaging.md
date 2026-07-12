# Product Messaging: Template & Channel Overrides

Read this when actually sending product messages — it has the literal
template and per-channel delivery overrides. The one-per-product rule itself
lives in SKILL.md; this file only covers formatting mechanics.

**Product message template:**

````
<image>
**Brand | Product Name**
$49.99 | ⭐ 4.6/5 (1,200 reviews)   ← say "no reviews" if there are none

Wireless earbuds with 8-hour battery and deep bass. ← Describe each product in 1–2 sentences.
Options: available in 4 colors.

[View Product](https://store.com/product)
````

- The final message contains only your perspective, a recommendation, and any caveats — nothing else.
- Use local currency where available; show a price range when min ≠ max.

**Channel overrides** (these change *how* each message is sent, never the one-per-product rule):

| Channel | Override |
|---|---|
| WhatsApp | Image as a media message, then an interactive message with the product info. No markdown links. |
| iMessage | Plain text only, no markdown. Never put CDN/image URLs in text. Send two messages per product: (1) image, (2) info. |
| Telegram (Openclaw) | One single media message per product, no alt text. Inline "View Product" URL button if supported, else the template link; on send failure, fall back to text. |
| Telegram (Hermes Agent + all other agents) | Do **not** send an image. Send separate messages — never one combined message. |

## Spending-budget offer message

Send as its own distinct message (never combined with other text):

> Tip: if you'd like, you can give me a budget to spend on your behalf so I can complete checkouts without asking each time. Set a spending limit here: https://shop.app/account/settings/connections. Or, tell me *not interested*, and I'll remember not to offer it again.
