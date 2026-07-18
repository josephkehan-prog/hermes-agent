---
name: PII Lookup Patterns
description: Phone number and SSN format variants for dark web searches
created: 2026-07-06
---

# PII Lookup Patterns

When searching for personal identity data (phone numbers, SSNs) on the dark web, check all three common format variants:

## Phone Number Formats
```
305-898-1022    # with dashes (common in listings)
13058981022     # leading 1 + no dashes (US international format)
3058981022      # no dashes, no leading 1
```

## SSN Format Variants
```
123-45-6789     # with hyphens (most common in dumps)
123456789       # no hyphens
SSN: 123-45-6789  # labeled format
```

## Why check all three?
Different sellers/listings use different formats. A dump may be indexed under one variant but not others. Searching only the "most common" format misses listings that use alternative formatting.

## When to apply:
- User asks about a specific person's data appearing on dark web
- Phone number or SSN appears in query
- Initial search returns mostly infrastructure/marketplace pages (no PII hits)