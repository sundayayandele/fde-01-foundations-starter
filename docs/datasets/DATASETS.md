# Datasets

Datasets are downloaded at run time into `data/` (git-ignored) and never committed.

## Banking77 (primary benchmark)

| Field | Value |
| --- | --- |
| Source | PolyAI, https://github.com/PolyAI-LDN/task-specific-datasets (`banking_data/`) |
| Paper | Casanueva et al., *Efficient Intent Detection with Dual Sentence Encoders*, NLP4ConvAI 2020 |
| Licence | CC BY 4.0 (LICENSE file in the repository, checked 2026-10-13). Attribution required |
| Version | Git commit `57ec275d8078af65b7731c2a98be812d844a6d6b` |
| Files | `train.csv` SHA-256 `b06e26ac675513959a63135f11b94ea7786ed02da65db93a5650d8838cbc664b`; `test.csv` SHA-256 `d12d6e3bc4c3103966ae786dc435913c0c563dfa328f5a3646d0e62cfeeb474d` |
| Size | 10,003 train and 3,080 test single-sentence English customer queries, 77 intents |
| Download | `make download` (verifies both checksums; a mismatch deletes the file and fails) |
| Leakage | 7 test texts duplicate training texts after normalisation; they are removed from the test split |

## CFPB complaints (flagship domain)

| Field | Value |
| --- | --- |
| Source | US CFPB Consumer Complaint Database, ingested by [fde-00-programming](https://github.com/sundayayandele/fde-00-programming) or downloaded as the bulk CSV |
| Licence | US government open data; see fde-00's DATASETS for terms to verify |
| Use here | `narrative` → `product` (or `issue`) |
| Loaders | `cfpb-db:<DATABASE_URL>` reads fde-00's `complaints` table; `cfpb-csv:<path>` reads the bulk CSV |
| Filters | Rows with a narrative only; classes with at least 50 examples; at most 5,000 per class (`--max-per-class`), sampled with seed 42 |
| Version | CSV: SHA-256 prefix of the file; database: row count at training time (record the fde-00 run IDs too) |
| Not measured here | The build sandbox cannot reach the CFPB. Run it on your machine and add the rows to the results table |

Product and issue taxonomies changed over the years; train on a recent date window or merge old labels before comparing across years.

## Fixture

`load_fixture()` generates a small four-intent dataset (card arrival, lost card, failed transfer, refund) for tests, `make e2e` and offline image builds. It is not a benchmark.

## Extension datasets (stretch labs)

| Dataset | Domain | Where | Licence (verify) |
| --- | --- | --- | --- |
| LEDGAR (LexGLUE) | Legal contract provisions, 100 classes | Hugging Face `coastalcph/lex_glue`, config `ledgar` | CC BY-SA 4.0 |
| CLINC150 | Multi-domain intents incl. out-of-scope | Hugging Face `clinc_oos` | CC BY 3.0 |

Add a loader returning a `Dataset`, then train and evaluate with the same commands.
