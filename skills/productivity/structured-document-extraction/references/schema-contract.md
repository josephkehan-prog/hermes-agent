# Extraction schema contract

Define:

- stable field names and scalar/object/array types;
- required versus optional fields;
- enum values, date format, currency/unit treatment, and null policy;
- table row identity and nested-object boundaries;
- whether text must be verbatim or normalized;
- evidence fields: page number, bounding description, and source excerpt.

Do not encode unknown values as empty strings. Use `null` plus a reason. Reject
extra fields by default so model commentary cannot leak into machine records.
