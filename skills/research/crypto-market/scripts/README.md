# scripts/

`crypto.py` — stdlib-only CLI for keyless crypto market data and wallet lookups.

```bash
python3 crypto.py price bitcoin ethereum monero
python3 crypto.py trending
python3 crypto.py feargreed
python3 crypto.py eth-balance 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
```

No deps, no API keys. Read-only, public-chain data only — never handles
private keys. Exits 2 on invalid input or network/HTTP/parse errors.
