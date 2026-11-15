# Results and retained evidence

**All planned trials are finished.**

Observed at: `2026-11-14T23:07:11+00:00`.

This Markdown snapshot reads [data/results.json](data/results.json) (export status `complete`, scope `evaluation`). The canonical matrix is **144 trials: 36 tasks × four agents/models**. `full-oracle-verified` is the canonical oracle; interrupted `full-oracle`, smoke jobs and repeats are excluded.

Progress: **144/144 graded**, including **2 warned**; **0 failed/missing**, **0 pending**. Warned trials are included in graded, not clean completions.

Source manifest SHA-256: `a37aedd4587d16ad07b30738fcdf53f1706afd4302ccdfa5f4250e52bd3ff834`. Individual source hashes appear below. The live export can advance after this observation.

## Full-set matrix

| Job | Agent / model | Expected | Graded | Warned | Failed / missing | Pending | Mean reward | Inference cost USD | Mean recorded trial duration (n) |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| `full-oracle-verified` | `oracle` | 36 | 36 | 0 | 0 | 0 | 1.000000 | unavailable | 19.21 s (36) |
| `full-nop` | `nop` | 36 | 36 | 0 | 0 | 0 | 0.000000 | unavailable | 30.61 s (36) |
| `full-deepseek` | `verda/deepseek-4-1-flash-1017` | 36 | 36 | 2 | 0 | 0 | 0.392409 | unavailable | 276.82 s (36) |
| `full-kimi` | `verda/kimi-k3-1-pro` | 36 | 36 | 0 | 0 | 0 | 0.807308 | unavailable | 231.78 s (36) |

Means use [the exporter’s `summarize`](scripts/export_results.py): any pending row makes its group mean unavailable. Once a group finishes, valid official rewards are summed over **all expected tasks**; finished failed/missing trials contribute zero. A score file does not supply an official reward when the Harbor trial failed. The model means aggregate task rows, not unequal family means.

Unknown cost is unavailable (`null`), never zero. Reported inference cost does not establish total Modal infrastructure charges. Duration means use only rows with a recorded `duration_sec`, derived from trial `started_at`/`finished_at`; the parenthesized count gives coverage. These can include finished failures. They are not inference-only latency or enclosing job wall time, and concurrent trial durations must not be summed as job wall time.

### Family × condition means

| Family | Condition | Expected per model | Oracle | No-op | DeepSeek | Kimi |
|---|---|---:|---:|---:|---:|---:|
| area | clean | 2 | 1.000000 | 0.000000 | 0.263929 | 0.810952 |
| area | scan | 2 | 1.000000 | 0.000000 | 0.452660 | 0.781999 |
| area | vector | 2 | 1.000000 | 0.000000 | 0.024080 | 0.868983 |
| openings | clean | 2 | 1.000000 | 0.000000 | 0.449750 | 0.974990 |
| openings | scan | 2 | 1.000000 | 0.000000 | 0.069750 | 0.958656 |
| openings | vector | 2 | 1.000000 | 0.000000 | 0.929794 | 0.958686 |
| piping | clean | 3 | 1.000000 | 0.000000 | 0.923268 | 0.916657 |
| piping | scan | 3 | 1.000000 | 0.000000 | 0.932684 | 0.899990 |
| piping | vector | 3 | 1.000000 | 0.000000 | 0.916871 | 0.866657 |
| skirting | clean | 3 | 1.000000 | 0.000000 | 0.023250 | 0.872859 |
| skirting | scan | 3 | 1.000000 | 0.000000 | 0.195332 | 0.872470 |
| skirting | vector | 3 | 1.000000 | 0.000000 | 0.190676 | 0.855436 |
| slab | clean | 2 | 1.000000 | 0.000000 | 0.062780 | 0.136416 |
| slab | scan | 2 | 1.000000 | 0.000000 | 0.000000 | 0.556521 |
| slab | vector | 2 | 1.000000 | 0.000000 | 0.037500 | 0.558241 |

The 36 tasks are **12 paired scenarios on three drawings**, not 36 independent buildings. The `scan` condition uses synthetic degradation. Scenario train/holdout splits share the three drawings; all scenarios were inspected during curation. These baseline evaluations train no model weights and cannot establish unseen-building or real-scan generalization.

## Recorded model examples

Examples require a real exported model result and its allowlisted replay bundle. Selection is deterministic by run ID; quantity success means recorded `score.value_score >= 0.99`, not necessarily perfect overall reward. No reference quantities are reproduced.

### Success

[`full-deepseek-bp-01-scan`](data/trajectories/full-deepseek-bp-01-scan.json) — `verda/deepseek-4-1-flash-1017`; status `completed`.

Question: What is the floor area of the fitness room?

Saved submission: value **26.7**, unit `m2`, confidence **0.72**.

Official reward: 0.857160. Recorded value/evidence/calibration scores: 1.000000 / 0.100000 / 0.921600. Weighted contributions: `{"calibration": 0.09216, "evidence": 0.014999999999999996, "value": 0.75}`. Exception: `none`.

Quantity succeeded; recorded evidence/calibration can still reduce total reward.

### Failure

[`full-deepseek-bp-01-clean`](data/trajectories/full-deepseek-bp-01-clean.json) — `verda/deepseek-4-1-flash-1017`; status `completed`.

Question: What is the floor area of the fitness room?

Saved submission: value **29.1**, unit `m2`, confidence **0.6**.

Official reward: 0.466297. Recorded value/evidence/calibration scores: 0.524735 / 0.058304 / 0.640000. Weighted contributions: `{"calibration": 0.064, "evidence": 0.00874559145934611, "value": 0.3935516156705748}`. Exception: `none`.

Recorded numeric/value miss; its cause is not established.

### Trap

[`full-deepseek-bp-09-clean`](data/trajectories/full-deepseek-bp-09-clean.json) — `verda/deepseek-4-1-flash-1017`; status `completed`.

Question: What is the gross plan area of the rectangular 150 mm slab-on-grade with D13 @ 300?

Saved submission: value **303.0**, unit `m2`, confidence **0.62**.

Official reward: 0.061560. Recorded value/evidence/calibration scores: 0.000000 / 0.000000 / 0.615600. Weighted contributions: `{"calibration": 0.06156, "evidence": 0.0, "value": 0.0}`. Exception: `none`.

Trap quantity missed; no specific misread is established.

## Smoke and historical diagnostics — separate from the matrix

These rows derive from retained local Harbor trial results. Missing local artifacts remain unavailable. Reward means cover recorded official rewards only in this diagnostic table, never the canonical expected denominator.

| Job | Recorded / expected | Graded | Warned | Failed | Unfinished¹ | Recorded official reward mean (n) | Mean recorded trial duration (n) | Enclosing job elapsed | Cost USD |
|---|---:|---:|---:|---:|---:|---|---|---|---|
| `smoke-oracle-v2` | 1 / 1 | 1 | 0 | 0 | 0 | 1.000000 (1) | 54.02 s (1) | 54.15 s | unavailable |
| `smoke-no-snapshot` | 1 / 1 | 1 | 0 | 0 | 0 | 0.956143 (1) | 54.46 s (1) | 54.54 s | unavailable |
| `smoke-deepseek` | 1 / 1 | 1 | 1 | 0 | 0 | 0.974360 (1) | 159.73 s (1) | 159.94 s | unavailable |
| `smoke-preinstalled` | 0 / unavailable | 0 | 0 | 0 | unavailable | unavailable (0) | unavailable s (0) | unavailable s | unavailable |
| `smoke-preinstalled-v2` | 1 / 1 | 1 | 1 | 0 | 0 | 0.956983 (1) | 245.95 s (1) | 246.16 s | unavailable |
| `full-oracle` | 33 / 36 | 31 | 0 | 2 | 3 | 1.000000 (31) | 54.47 s (33) | unavailable s | unavailable |

¹ Unfinished means expected minus retained finished trial records; it does not distinguish running, cancelled or never-started trials. The stopped original `full-oracle` is diagnostic evidence, not the canonical oracle baseline. Its verifier timeouts include Modal verifier-log download operations; missing official rewards remain missing even when a score artifact exists.

The clean `smoke-no-snapshot` is one check-valve task, not a full-set accuracy estimate. Its trial duration and reward above come from persisted trial timestamps and verifier results; no informal duration estimate is used. Warning-bearing smoke rows retain valid rewards when Harbor marks them valid; they are not clean successes.

Complete original logs live under `runs/raw/JOB/TRIAL/` on the team machine. These ignored local paths are not GitHub evidence links. The [clean-smoke config](configs/evaluation-smoke-no-snapshot.json) and [sanitized retained smoke replay](data/trajectories/smoke-no-snapshot-bp-10-vector.json) remain separate from the active matrix; a retained smoke bundle need not be allowlisted by the live replay API.

The recorded clean-smoke configuration uses native OpenCode `1.19.5` with `snapshot: false`. The symptoms of earlier EPIPE/nonzero exits resemble the primary upstream [Harbor write-success/EPIPE report](https://github.com/harbor-framework/harbor/issues/4019) and [OpenCode snapshot/subprocess report](https://github.com/anomalyco/opencode/issues/60447). The retained clean trial is local evidence for this configuration, not a universal upstream fix. No custom adapter patch is used.

## Reproduce this Markdown snapshot

After the evaluation owner refreshes the public export, run from any working directory:

```sh
nice -n 15 python /path/to/afterquery-blueprints/scripts/render_results.py
nice -n 15 python /path/to/afterquery-blueprints/scripts/render_results.py --check
```

The default writes root `RESULTS.md` atomically. `--check` compares substantive content without rewriting; only the observation timestamp is ignored. Invalid/mixed input or inconsistent replay metadata aborts before replacing the previous report. No inference, remote calls, export mutation or publication occurs. Source hashes identify exactly the bytes read, including locally available diagnostics.

<details>
<summary>Source SHA-256 manifest</summary>

| Source | SHA-256 |
|---|---|
| `configs/evaluation-smoke-no-snapshot.json` | `219b42219e265d11f3d1122b3fc5be23eebae6b1da6db712d7b261547a90d180` |
| `data/catalog.json` | `9d77ae49410396bf50e33a9205511f18bc2f5bb19e2a183ff81a8106761d52ae` |
| `data/results.json` | `69999d30e6f5c714da0796ef0437b274b5ca0824bf67a2269abe2e99eee46102` |
| `data/trajectories/full-deepseek-bp-01-clean.json` | `32b498c6fea62e4639cf2128e7f8507e380d80f77c6a9130a60c29e921ede60d` |
| `data/trajectories/full-deepseek-bp-01-scan.json` | `87db02943354ad05d6cd8894056327110e52aa8b59acf67eb20fb2e369a69515` |
| `data/trajectories/full-deepseek-bp-01-vector.json` | `a8b376b6910c38d79064d13e76880d2f9746bd2473e7f6f003c6773e1c2c9b26` |
| `data/trajectories/full-deepseek-bp-02-clean.json` | `281c9b8dd8552c18793c751117a1b3fed9cce963dc10d39f74e6bcbb839b542f` |
| `data/trajectories/full-deepseek-bp-02-scan.json` | `3958a21dbe59275645013ae518aa74444daa9e6f4b88ee736eb3bcf62ee2e479` |
| `data/trajectories/full-deepseek-bp-02-vector.json` | `f266fcb9987a3776e0f5986f613e724de820f57c03310772bb9ddef40f50a01e` |
| `data/trajectories/full-deepseek-bp-03-clean.json` | `a02594783626e4de236543ae5ff5adb46add866c636bdfd3d49bf233cd292e29` |
| `data/trajectories/full-deepseek-bp-03-scan.json` | `6a5208243c3b25f2126954814219cfe913296720c4aa9197f30eb090a03e258f` |
| `data/trajectories/full-deepseek-bp-03-vector.json` | `6ea2675d34ec8be716ff38ee1ad31f246047dc5cd58ef8eee814854b4e6f3ed0` |
| `data/trajectories/full-deepseek-bp-04-clean.json` | `eb98009423d224ddb399794ca56ab33c23fadcb806f8b3ccc4a5309f5ee2ee1a` |
| `data/trajectories/full-deepseek-bp-04-scan.json` | `7588b5c88bd2f6dbc0ad3bb01f3d3c4fa12738575f65f111345399e0f1366776` |
| `data/trajectories/full-deepseek-bp-04-vector.json` | `b878b8032f83af6edb4e047fa1bd614509096e0d134be244f718b4fbbd84f5bb` |
| `data/trajectories/full-deepseek-bp-05-clean.json` | `97b71e6b12424ad9134edf5923bf80e015f77586c3b34d7f0d9e0059caa26f83` |
| `data/trajectories/full-deepseek-bp-05-scan.json` | `76f738b3053ea9c673e54d4310970989240b261c8e010ff5f952eb9df8be61df` |
| `data/trajectories/full-deepseek-bp-05-vector.json` | `d523e64a7e4c4bf3f16a872e100f2938e74d677242a789cfe4ea2ea53d111996` |
| `data/trajectories/full-deepseek-bp-06-clean.json` | `935564e8fb8aa86a247b01bed5f87a3f05dec6eaa6603e6a0b9bc8f1bdb8d630` |
| `data/trajectories/full-deepseek-bp-06-scan.json` | `fef8d42f6fd11fed5dc4cc88f1917a3084475a03cd4b019c9f9d3c29a67464c5` |
| `data/trajectories/full-deepseek-bp-06-vector.json` | `155adafd83c54fbd5ff08507ee713cae11bc2460e7a20eeac4f60189d3088687` |
| `data/trajectories/full-deepseek-bp-07-clean.json` | `fb38e92183bfb2ed277402a2f70f6bb86f17e1746e1b8ff21988e4a6a8b3fbca` |
| `data/trajectories/full-deepseek-bp-07-scan.json` | `bf3eb82bb60c85aace004ec564aa6d1075d748e5004715ba4cd4712510bd4624` |
| `data/trajectories/full-deepseek-bp-07-vector.json` | `ecc05a8dda2fc434483917d68f33307717e9b661eb69eb1c2c35b6472e143031` |
| `data/trajectories/full-deepseek-bp-08-clean.json` | `eed3c598d6810a0c9b4ac2c13820b085835af32b4dff495ce304864757f8bb9b` |
| `data/trajectories/full-deepseek-bp-08-scan.json` | `b33025f36f53b1471a61f52577f960b9acaed407325314d2e50259f9871201fe` |
| `data/trajectories/full-deepseek-bp-08-vector.json` | `56567764e2d808794e61b7db55269a8a18c08471a75cbb760877067ae9831d05` |
| `data/trajectories/full-deepseek-bp-09-clean.json` | `1a1ebb5a911a79ed6312e52b22159ea33b84fc7d9bd6d7dd8e4f4e9fd55d7d00` |
| `data/trajectories/full-deepseek-bp-09-scan.json` | `57d4e69093dbd9fd19ac5e94819a5c83a58b70938f4e29aadb9756863ad51d92` |
| `data/trajectories/full-deepseek-bp-09-vector.json` | `f316f7fee57278c8df1707006e6e90b5ede318d1dc0610d6a76fdcc4c1ab501a` |
| `data/trajectories/full-deepseek-bp-10-clean.json` | `7fe94c42e59c676c5ae27b44feb464da34d8688a7d984d1ce66e05e7a407de7f` |
| `data/trajectories/full-deepseek-bp-10-scan.json` | `5d5fb36e23cbb72f9025767a6cb21f1b2913bfc169d34c0ff81895a6e1f6f3e7` |
| `data/trajectories/full-deepseek-bp-10-vector.json` | `1c8da5df0ae2f0ad622623bd2ce4d7474560886406ceb34c2fd591e0134dbf48` |
| `data/trajectories/full-deepseek-bp-11-clean.json` | `257d457a144b9897a488995256ba23bf8fcddd4914fdb7459d2317fa812fb465` |
| `data/trajectories/full-deepseek-bp-11-scan.json` | `9fa1a60d8ddab754dd67f6208bba461fdf2984a82b1a8011cfccac4d60146866` |
| `data/trajectories/full-deepseek-bp-11-vector.json` | `988ee73a78fed271d2a163c8ceffdcaf48584edcc643de173a77c4623bc60b8d` |
| `data/trajectories/full-deepseek-bp-12-clean.json` | `89501d9a40a1575c63120e0711add9110b64e95330c4de652087795daadfc85e` |
| `data/trajectories/full-deepseek-bp-12-scan.json` | `825f4df8883e85d2afbde1d6357c2d29395e021ad3369d53e57accdfc8449a6f` |
| `data/trajectories/full-deepseek-bp-12-vector.json` | `645466507402779b2c0be991a44b7dadf73c1974d0e5fe0a43029efc3e1255cb` |
| `data/trajectories/full-kimi-bp-01-clean.json` | `5ed1eeca16f3ef109e42e850794821703e50ff0c93dbc95f79dd24c89a795ae9` |
| `data/trajectories/full-kimi-bp-01-scan.json` | `a48e7b4b2f3187f61d4a480902b8be6beb7ca4330149a099ae484bb617c48722` |
| `data/trajectories/full-kimi-bp-01-vector.json` | `f0dc9f1710bfe7ffe49d63b9a5adf5411aa47e2d7d370cd7c320999b76c83adc` |
| `data/trajectories/full-kimi-bp-02-clean.json` | `6022193a9a6d165859a72c773ff7e31781cb5cd7ede802adf7868e251ccca3bb` |
| `data/trajectories/full-kimi-bp-02-scan.json` | `64465ffd6322963c865b0480a04207ef90ce582df2f25c4426423cb0be9d2205` |
| `data/trajectories/full-kimi-bp-02-vector.json` | `2daa3bdc60f9e06186215c8a281a91acd9df452df584002b48a15a4305f45bcf` |
| `data/trajectories/full-kimi-bp-03-clean.json` | `e6b729828b1ad96b421e69261b2049e6d0b8fdbba8a10a43f5eb36b13854a3a5` |
| `data/trajectories/full-kimi-bp-03-scan.json` | `cb17b6b5c7880f44167ee20d189e38e454a94457c94c907a7700d2374cb03aec` |
| `data/trajectories/full-kimi-bp-03-vector.json` | `1a4bb65ac5c6a044f484039cb28dc959fa7477f2b9b8e61576dfce05f916af4a` |
| `data/trajectories/full-kimi-bp-04-clean.json` | `905ebfdabea365a909d6d0abd79ec244e1bfa4d57dd555a44d2d989e9af2df1a` |
| `data/trajectories/full-kimi-bp-04-scan.json` | `e21ef014395fa49b52aca305d38f6cb04b27b83104d8ab20e8b49c783f365396` |
| `data/trajectories/full-kimi-bp-04-vector.json` | `dd181234f52a028ccee1ba6c885d7b2ff4ad1005e37ea862d4948d04668ec82c` |
| `data/trajectories/full-kimi-bp-05-clean.json` | `6e767d5662cab735b5848ca8b6a79aa1bae0b3db47d3b6a6f82c23f898568b7f` |
| `data/trajectories/full-kimi-bp-05-scan.json` | `dd007547a955d6d537ac8038348c7fe814fa0581b0fd9121703d8faf27c57e90` |
| `data/trajectories/full-kimi-bp-05-vector.json` | `903939f0aad02a6396344491e8959ba52cfba7c6f77c8d999c50505ab4bcf694` |
| `data/trajectories/full-kimi-bp-06-clean.json` | `3d5656beb2ec7a5924d1632648947c966a758829e683986bb0b0b9c0267a9639` |
| `data/trajectories/full-kimi-bp-06-scan.json` | `fbd58d50119715d6e8e84deb8236d17d46575dfef8e888265b69ef5271d45c47` |
| `data/trajectories/full-kimi-bp-06-vector.json` | `e390fb7983e03154601a9bd0927b9c89d2959520ecd7082e8b684098763dbcf5` |
| `data/trajectories/full-kimi-bp-07-clean.json` | `d07ac0a51916bdb5c019ef27b74613698020173f89758c75306ba4b6f66074e7` |
| `data/trajectories/full-kimi-bp-07-scan.json` | `8c93adffa257c13df93a19de6496c260388e7554686a0db3658954b7bec202a2` |
| `data/trajectories/full-kimi-bp-07-vector.json` | `6552f3c1a23ff04b4715ba685b9552b9e0ee138004ade9b5ac5633e7da67a63f` |
| `data/trajectories/full-kimi-bp-08-clean.json` | `095d9442ad4661e647ba3f09fbe60f83960e139dd872308af4bedf9074198dfc` |
| `data/trajectories/full-kimi-bp-08-scan.json` | `c75de0f49bad4f1a3210e4946725aa35c828406b20d03690a7ff664c70e307e0` |
| `data/trajectories/full-kimi-bp-08-vector.json` | `5d3fd9e3a3632ea6b256c831cc08279a0fcca5660faad69c326e86c6b2f7d98c` |
| `data/trajectories/full-kimi-bp-09-clean.json` | `4ca9887fbba35dc19d8e08992496486f8ad3e5bf17a313a46279234ebd4a6890` |
| `data/trajectories/full-kimi-bp-09-scan.json` | `4b5753af47e4e7aac689f6dfc7c04e3e47691445aeb05ad70bdaafa32fc90eca` |
| `data/trajectories/full-kimi-bp-09-vector.json` | `e967436057ff6d92406f66457288f8099a05769ed43f2c73a65f60970dcbb200` |
| `data/trajectories/full-kimi-bp-10-clean.json` | `76220386eea1192ee313ca96ee09ccf14cc5b1c2af20f1c3d4e6055af4c07f90` |
| `data/trajectories/full-kimi-bp-10-scan.json` | `a6b213c4e8493bb97692b492e7be488294ef7ca618a6a3ca16542f2b788304cd` |
| `data/trajectories/full-kimi-bp-10-vector.json` | `7e1614bdb13b261591aa40b1c2cc17081610000b1d738ae3629c32e182ef00e2` |
| `data/trajectories/full-kimi-bp-11-clean.json` | `61f03b508adec1ee311bbadd1dc2d43b74ade446e4d74f6f9cbd2bb4022e7710` |
| `data/trajectories/full-kimi-bp-11-scan.json` | `80b40035e64273dcd40935d197619f826b25cfcbf5537c5e152f373e48f1ffad` |
| `data/trajectories/full-kimi-bp-11-vector.json` | `32a7fd7c9e729deb9cfd1b8a7bcbb816f283d66f714d0cbaeb2553bee6459207` |
| `data/trajectories/full-kimi-bp-12-clean.json` | `60376657d1143c500c2eeed1a398aa4567ae370e584dc9dd845a1bf127c143dc` |
| `data/trajectories/full-kimi-bp-12-scan.json` | `bef48f467d4387a7f6d6da0db488ce31c4ac71985e222fa539e8b2fc35513d8b` |
| `data/trajectories/full-kimi-bp-12-vector.json` | `56f26e260de0975d172e9ec174ad174797d1de227f592ba785972ed90c8276d4` |
| `runs/raw/full-oracle/bp-01-clean__Cigu9c9/result.json` | `a1b39523e0d88a736616d697f942f39c54adaf060a72541edf2330daf130a6e8` |
| `runs/raw/full-oracle/bp-01-scan__VQP3ktV/result.json` | `b136ed2a316ce4bc9489bf733623278a832012a59587a1bd6739f47f9564a224` |
| `runs/raw/full-oracle/bp-01-vector__6YUvhup/result.json` | `20989b68ed28ca044014731f6a9e803bc348f5a9318fb8580219c00ff8c8ccdc` |
| `runs/raw/full-oracle/bp-02-clean__87ccK2f/result.json` | `ee8a9ca9dd2347538423c264c912a364b2c96a5a307be58f64e3ef2470368878` |
| `runs/raw/full-oracle/bp-02-scan__zQyh6m9/result.json` | `b70f6f64f55d3dd2ec317909e63014fb0c2cd1fe7fad601407edd40e574f6e3e` |
| `runs/raw/full-oracle/bp-02-vector__qXydiSM/result.json` | `435ddb26cf044016b5e77b9ead5d86455ab3ab92a617d814163e3096eedd0c85` |
| `runs/raw/full-oracle/bp-03-clean__GSo2Cco/result.json` | `e143073285c50f55f990991308f1110e71e5f989fbc7c177aea43e4b741a110d` |
| `runs/raw/full-oracle/bp-03-scan__PbSP8RR/result.json` | `9eb91693d6f3bf16d4b3dd99a7c7ea7d4e73c3149d4520984efd384da96646a1` |
| `runs/raw/full-oracle/bp-03-vector__rbKirg6/result.json` | `01e9246d1f0a5bb1d20eaeb9e4ffab7d7635991302d9557fb1785a84549be3d1` |
| `runs/raw/full-oracle/bp-04-clean__G7hxA2B/result.json` | `9328d8ea82e1b17e095dade757d7a16b878584ea3fb2c5bfb7d9b5450fca55dc` |
| `runs/raw/full-oracle/bp-04-scan__ihxavcg/result.json` | `03e300f0d7426e682fa4b15ef74e1cbd5f4060b48115abcb732a2614c1c47174` |
| `runs/raw/full-oracle/bp-04-vector__iqDejQ3/result.json` | `c33b363f8c9403e05390492c6f99199c1bae4d265c971ad32d39a4af170acef4` |
| `runs/raw/full-oracle/bp-05-clean__BLSwLbF/result.json` | `568879e4fccad8bae0ed94f23f94aa5aced28faeb6f3c2ae2bcb1b2be68ac8e7` |
| `runs/raw/full-oracle/bp-05-scan__veq2Emg/result.json` | `37a8849825c3f1401d6ba7089df510f26605fa8504deda0126b5a1fb6cd8fff7` |
| `runs/raw/full-oracle/bp-05-vector__LcaXX25/result.json` | `4a9909f126584f8a36d0205a0e2cfeb7ae70e66f5a900a49ee4666824b215f72` |
| `runs/raw/full-oracle/bp-06-clean__8j4bUuH/result.json` | `3144c68e5f08fb34833aee023cb9a41b4728af34dca983ff85ab54769a1fe734` |
| `runs/raw/full-oracle/bp-06-scan__bKYiniX/result.json` | `0cd49baf4f3a83bb9d7460a84b35fb1d1c24c0cc476c0262f7a3829b35fea90d` |
| `runs/raw/full-oracle/bp-06-vector__BJmUTbr/result.json` | `cd7d8e4d018c7a9985a19f3f5ccf73af81e556540329e69397d87d86b6f0cdc7` |
| `runs/raw/full-oracle/bp-07-clean__Rwifzys/result.json` | `de44784d5a72c2c7ee8b79bf73658f0a0390ce92b3757d2880770a7d4f11ef61` |
| `runs/raw/full-oracle/bp-07-scan__o7ZdaUV/result.json` | `5898e54bba68d6edff23a9bf169f16557b16d81a5290ba74642835370edc39f6` |
| `runs/raw/full-oracle/bp-07-vector__aLbXGG3/result.json` | `4931fd9d2d8feeaaafae9ef73f1f00a20abf4cc94d781eec58170dcb7e4c0e47` |
| `runs/raw/full-oracle/bp-08-clean__sYmRJY2/result.json` | `9d7583e475180558adc1f9abdf0a04d0367100e51af95209c51fac720c0ecc30` |
| `runs/raw/full-oracle/bp-08-scan__SeupQW8/result.json` | `b8e9813b982667003c265fdcdea5e8bb25cc84480fc080fec6e78c097a7478f4` |
| `runs/raw/full-oracle/bp-08-vector__4QET8eX/result.json` | `1c413132394ee79a5a4a4cd3bbb32d697cb8eb8c28aef66fdd5edcdce414eb48` |
| `runs/raw/full-oracle/bp-09-clean__nZapWf4/result.json` | `e86268163ce2cbfa9145913f53c1818f4339a2232b598e57185aa7d54f648f85` |
| `runs/raw/full-oracle/bp-09-scan__cs8j8it/result.json` | `616b79e7da50107bc526c6f170b1d004d4688068cbae8283f1478bb1d0030ac8` |
| `runs/raw/full-oracle/bp-09-vector__jj6BXtf/result.json` | `ab5cc81d0c0aedacfcf42a67ba05d14579bba14edca659fa97c23623fa403ff0` |
| `runs/raw/full-oracle/bp-10-clean__chbhc3o/result.json` | `1ae8e673d2713793e8024a6416cf65be305e1a8867e0118b83553829d643edeb` |
| `runs/raw/full-oracle/bp-10-scan__thpxC3M/result.json` | `c148a5be7083dc29b901e239ba9cdbece8bb2a173b13cf225c59045db45b1ab4` |
| `runs/raw/full-oracle/bp-10-vector__jEgd7Qq/result.json` | `022c636cbac4de0f241f3fb2993d09e06d39f339efd6c83eedf63fbceb39ec60` |
| `runs/raw/full-oracle/bp-11-clean__UMCg7iX/result.json` | `b039937566b7250e78465d6561de789e069f92f5e35c9b0c0f8dd49f525c3b40` |
| `runs/raw/full-oracle/bp-11-scan__xctA6V6/result.json` | `20045a2957dd097e5066badf1386ef7010f3421496e9aa589143c8009227785d` |
| `runs/raw/full-oracle/bp-11-vector__fmicKur/result.json` | `69237fc2c77a9dded6fb1fd4093422c0e3d1f1e02db1101c463b185ba794c6ed` |
| `runs/raw/full-oracle/result.json` | `93597a8a697ce6592e3fe844f0cc4a087d5f6a27dc3c9c762f08af92578d5179` |
| `runs/raw/smoke-deepseek/bp-10-vector__VoCgSfh/result.json` | `9ed96dc6a38072765461bc746d0ca1fa8a47d4cec404ea051be0fea8230d0a14` |
| `runs/raw/smoke-deepseek/result.json` | `f77b504a9d99eb9e8344996b01c31b328aa93d227c7689eacec46571abc0d99a` |
| `runs/raw/smoke-no-snapshot/bp-10-vector__L5aZfwW/result.json` | `7383193db60d3b78426981e8ad39236f3fbcd4ae29371971f71d0793710ce0ac` |
| `runs/raw/smoke-no-snapshot/result.json` | `bdcfacf2bdcb3c63e64f2070a2f2d10e331dd461388f4d890fc8c2b3964acd56` |
| `runs/raw/smoke-oracle-v2/bp-10-vector__bffVs4e/result.json` | `8d415e184fe17696904d973ea7a6b499f37cddf506b6b364f8cc204a748a090f` |
| `runs/raw/smoke-oracle-v2/result.json` | `21ed6b9fe09223268d4516c107dfdeb6a48e9836b5ea24f30cc6443e78c51bbb` |
| `runs/raw/smoke-preinstalled-v2/bp-10-vector__YGVeokQ/result.json` | `1e4b043330de466c7afb2bd2cef043468f8170ed9de36d05285d416eb78991f8` |
| `runs/raw/smoke-preinstalled-v2/result.json` | `3a2750d4d12e3fed6a4b673665af32084963d6f81feaac2b1cdaccb889289feb` |

</details>
