# Catalog Command Reference

Full flag reference for `shop search`, `shop catalog lookup`, and
`shop catalog get-product`. Read this when a search needs pagination, price
bounds, taxonomy attribute filters, similarity search, or image search beyond
the basic examples in SKILL.md.

```text
global                   --country <ISO2> (context signal, NOT a ships-to filter)
                         --currency <code> (context signal, e.g. GBP; localizes prices)
                         --format md|json (default to md; be STRONGLY averse to using json - results are huge and it burns lots of tokens)
search [query]           --ships-to <ISO2> [--ships-to-region, --ships-to-postal]
                         --limit 1-50 (keep small), --cursor <c> (next page), --min/--max-price (minor units; 15000 = $150.00)
                         --condition new,secondhand (default new), --ships-from <ISO2,...> (comma list)
                         --shop-id <id...>, --category <id...>, --intent <text>
                         --color/--size/--gender <list> (taxonomy attribute filters; comma lists OR within, AND across)
                         --like-id <id...> (similar; product or variant gid), --image ./photo.jpg
                         (query is optional when --like-id or --image is given)
catalog lookup <ids...>  --ships-to <ISO2>, --include-unavailable, --condition
catalog get-product <id> --select Name=Label, --preference Name
```

- `--ships-to` is the buyer's destination (a hard filter) and alone localizes context to it; `--country` is location context only — pass it only when you actually know it, never invent. Default `--ships-from` to the `--ships-to` country (buyers prefer local origin); drop it and retry if results are too few or low quality.

```bash
shop search "trail running shoes" --country GB --currency GBP --ships-to GB --ships-from GB --limit 10 --condition new
shop search "tshirt" --country US --color White --size M --gender Female
shop search "black crewneck sweater" --like-id gid://shopify/p/abc123
shop search --image ./photo.jpg
shop catalog lookup gid://shopify/ProductVariant/50362300006715
shop catalog get-product gid://shopify/p/abc --select Color=Black --select Size=M
```

## Similar items

- `shop search --like-id <id>` — pass a product (`gid://shopify/p/...`) or variant (`gid://shopify/ProductVariant/...`) reference; both return similar items.
- `shop search --image ./photo.jpg` — the CLI base64-encodes it for you. Formats: jpeg, png, webp, avif, heic; max ~3 MB on disk (4 MB base64). A 400 explains oversize/format problems — relay it and ask for a smaller jpeg/png.
