# Shopify Advanced Operations Reference

Full curl/GraphQL examples for inventory management, metafields/metaobjects, the Storefront API, bulk operations, and webhooks. Read this when working with any of these beyond basic product/order/customer CRUD (covered in SKILL.md).

## Inventory

Inventory lives on **inventory items** tied to variants, quantities tracked per **location**.

```bash
# Get inventory for a variant across all locations
shop_gql '
query($id: ID!) {
  productVariant(id: $id) {
    id sku
    inventoryItem {
      id tracked
      inventoryLevels(first: 10) {
        edges { node { location { id name } quantities(names: ["available","on_hand","committed"]) { name quantity } } }
      }
    }
  }
}' '{"id":"gid://shopify/ProductVariant/..."}'
```

Adjust stock (delta) — uses `inventoryAdjustQuantities`:

```bash
shop_gql '
mutation($input: InventoryAdjustQuantitiesInput!) {
  inventoryAdjustQuantities(input: $input) {
    inventoryAdjustmentGroup { reason changes { name delta } }
    userErrors { field message }
  }
}' '{
  "input": {
    "reason": "correction",
    "name": "available",
    "changes": [{"delta": 5, "inventoryItemId": "gid://shopify/InventoryItem/...", "locationId": "gid://shopify/Location/..."}]
  }
}'
```

Set absolute stock (not delta) — `inventorySetQuantities`:

```bash
shop_gql '
mutation($input: InventorySetQuantitiesInput!) {
  inventorySetQuantities(input: $input) {
    inventoryAdjustmentGroup { id }
    userErrors { field message }
  }
}' '{"input":{"reason":"correction","name":"available","ignoreCompareQuantity":true,"quantities":[{"inventoryItemId":"gid://shopify/InventoryItem/...","locationId":"gid://shopify/Location/...","quantity":100}]}}'
```

## Metafields & Metaobjects

Metafields attach custom data to resources (products, customers, orders, shop).

```bash
# Read
shop_gql '
query($id: ID!) {
  product(id: $id) {
    metafields(first: 10, namespace: "custom") {
      edges { node { key type value } }
    }
  }
}' '{"id":"gid://shopify/Product/..."}'

# Write (works for any owner type)
shop_gql '
mutation($metafields: [MetafieldsSetInput!]!) {
  metafieldsSet(metafields: $metafields) {
    metafields { id key namespace }
    userErrors { field message code }
  }
}' '{"metafields":[{"ownerId":"gid://shopify/Product/...","namespace":"custom","key":"care_instructions","type":"multi_line_text_field","value":"Wash cold. Tumble dry low."}]}'
```

## Storefront API (public read-only)

Different endpoint, different token, used for customer-facing apps/hydrogen-style headless setups. Headers differ:

- **Endpoint:** `https://$SHOPIFY_STORE_DOMAIN/api/$SHOPIFY_API_VERSION/graphql.json`
- **Auth header (public):** `X-Shopify-Storefront-Access-Token: <public token>` — embeddable in browser
- **Auth header (private):** `Shopify-Storefront-Private-Token: <private token>` — server-only

```bash
curl -sS -X POST \
  "https://${SHOPIFY_STORE_DOMAIN}/api/${SHOPIFY_API_VERSION:-2026-01}/graphql.json" \
  -H "Content-Type: application/json" \
  -H "X-Shopify-Storefront-Access-Token: ${SHOPIFY_STOREFRONT_TOKEN}" \
  -d '{"query":"{ shop { name } products(first: 5) { edges { node { id title handle } } } }"}' | jq
```

## Bulk Operations

For dumps larger than rate limits allow (full product catalog, all orders for a year):

```bash
# 1. Start bulk query
shop_gql '
mutation {
  bulkOperationRunQuery(query: """
    { products { edges { node { id title handle variants { edges { node { sku price } } } } } } }
  """) {
    bulkOperation { id status }
    userErrors { field message }
  }
}'

# 2. Poll status
shop_gql '{ currentBulkOperation { id status errorCode objectCount fileSize url partialDataUrl } }'

# 3. When status=COMPLETED, download the JSONL file
curl -sS "$URL" > products.jsonl
```

Each JSONL line is a node, and nested connections are emitted as separate lines with `__parentId`. Reassemble client-side if needed.

## Webhooks

Subscribe to events so you don't have to poll:

```bash
shop_gql '
mutation($topic: WebhookSubscriptionTopic!, $sub: WebhookSubscriptionInput!) {
  webhookSubscriptionCreate(topic: $topic, webhookSubscription: $sub) {
    webhookSubscription { id topic endpoint { __typename ... on WebhookHttpEndpoint { callbackUrl } } }
    userErrors { field message }
  }
}' '{"topic":"ORDERS_CREATE","sub":{"callbackUrl":"https://example.com/webhook","format":"JSON"}}'
```

Verify incoming webhook HMAC using the app's client secret (not the access token):

```bash
echo -n "$REQUEST_BODY" | openssl dgst -sha256 -hmac "$APP_SECRET" -binary | base64
# Compare to X-Shopify-Hmac-Sha256 header
```
