# 04 — Acceptance checklist (SWD-86 / SWD-100)

**Tracker:** [SWD-100](https://marcusknielsen.atlassian.net/browse/SWD-100)  
**Parent:** [SWD-86](https://marcusknielsen.atlassian.net/browse/SWD-86) · [`docs/PLAN.md`](../PLAN.md)

Automated contract/unit tests with mocked HA (`MockEntityStore` + `ThinIntegrationStub` + `IoImage`). No real Home Assistant instance.

Primary module: [`tests/test_swd86_acceptance.py`](../../tests/test_swd86_acceptance.py). Broader coverage also lives in `test_io_image_quality.py`, `test_io_binding.py`, `test_io_integration_stub.py`, and wedge tests.

## Checklist → tests

| Acceptance (PLAN) | Test name |
|-------------------|-----------|
| Sync refresh: IN at start, OUT at end every scan | `test_sync_refresh_in_at_start_out_at_end_every_scan` |
| Quality transitions GOOD / UNCERTAIN / BAD + reasons | `test_quality_transitions_good_uncertain_bad_with_reasons` |
| Last-good retention | `test_last_good_retention_when_quality_not_good` |
| Defaults before first GOOD (`BAD` / `unavailable`) | `test_defaults_before_first_good_bad_unavailable` |
| Direction enforcement | `test_direction_enforcement_in_reads_out_writes_only` |
| Multi-IN OK / single-OUT writer rejected | `test_multi_in_ok_single_out_writer_rejected` |
| Unit conversion scale / offset | `test_unit_conversion_scale_offset` |
| Mock path ≡ field path into Add-on image (same stub API) | `test_mock_path_equiv_field_path_same_stub_api` |
| No real HA imports in production or tests | `test_no_homeassistant_imports_in_production_or_tests` |

## How to run

```bash
python3 -m pytest -q
# or just the checklist:
python3 -m pytest -q tests/test_swd86_acceptance.py
```

## Example config

Acceptance scenarios use gravity-skid tag names (`LT_TANK`, `LT_RES`, `FT_INLET`, `CMD_SPEED`, `SP_LEVEL_REQ`, `SP_LEVEL`) aligned with [`docs/wedge/02-io-hmi-contract.md`](../wedge/02-io-hmi-contract.md) and the packaging sketch.

## References

- Image & quality: [`01-image-quality.md`](01-image-quality.md)
- Binding model: [`02-binding-model.md`](02-binding-model.md)
- Thin-integration stub: [`03-thin-integration-stub.md`](03-thin-integration-stub.md)
- Parent plan: [`docs/PLAN.md`](../PLAN.md)
