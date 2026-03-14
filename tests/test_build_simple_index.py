import importlib.util
import pathlib
import sys

import pytest

MODULE_PATH = (
    pathlib.Path(__file__).resolve().parents[1] / "scripts" / "build_simple_index.py"
)
SPEC = importlib.util.spec_from_file_location("build_simple_index", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
build_simple_index = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = build_simple_index
SPEC.loader.exec_module(build_simple_index)


def test_resolve_min_published_at_prefers_earlier_local_tag(monkeypatch):
    monkeypatch.setattr(
        build_simple_index,
        "get_local_tag_created_at",
        lambda _tag: "2022-07-31T15:52:51Z",
    )
    monkeypatch.setattr(
        build_simple_index,
        "fetch_release_by_tag",
        lambda **_kwargs: {"published_at": "2026-03-14T09:03:14Z"},
    )

    min_published_at, source = build_simple_index.resolve_min_published_at(
        repository="ringsaturn/tzfpy",
        tag="v0.6.0",
        token=None,
    )

    assert min_published_at == "2022-07-31T15:52:51Z"
    assert source == "local-tag"


def test_resolve_min_published_at_uses_release_when_no_local_tag(monkeypatch):
    monkeypatch.setattr(build_simple_index, "get_local_tag_created_at", lambda _tag: "")
    monkeypatch.setattr(
        build_simple_index,
        "fetch_release_by_tag",
        lambda **_kwargs: {"published_at": "2023-01-19T14:43:13Z"},
    )

    min_published_at, source = build_simple_index.resolve_min_published_at(
        repository="ringsaturn/tzfpy",
        tag="v0.12.0",
        token=None,
    )

    assert min_published_at == "2023-01-19T14:43:13Z"
    assert source == "release"


def test_resolve_min_published_at_raises_when_all_sources_missing(monkeypatch):
    monkeypatch.setattr(build_simple_index, "get_local_tag_created_at", lambda _tag: "")

    def _raise_release_lookup_error(**_kwargs):
        raise RuntimeError("mocked release lookup failure")

    monkeypatch.setattr(
        build_simple_index,
        "fetch_release_by_tag",
        _raise_release_lookup_error,
    )

    with pytest.raises(RuntimeError, match="Unable to resolve min-tag boundary"):
        build_simple_index.resolve_min_published_at(
            repository="ringsaturn/tzfpy",
            tag="v9.9.9",
            token=None,
        )


def test_sort_wheels_uses_release_commit_at_descending():
    older_commit = build_simple_index.WheelAsset(
        key="old",
        release_tag="v0.6.0",
        release_published_at="2026-03-14T09:03:14Z",
        release_commit_at="2022-07-31T15:52:51Z",
        release_prerelease=False,
        asset_id="1",
        name="tzfpy-0.6.0-cp310.whl",
        url="https://example.com/old.whl",
        updated_at="2026-03-14T09:03:13Z",
        digest="",
        uploader_login="github-actions[bot]",
    )
    newer_commit = build_simple_index.WheelAsset(
        key="new",
        release_tag="v1.0.0",
        release_published_at="2025-03-25T04:51:27Z",
        release_commit_at="2025-03-25T04:51:27Z",
        release_prerelease=False,
        asset_id="2",
        name="tzfpy-1.0.0-cp310.whl",
        url="https://example.com/new.whl",
        updated_at="2025-03-25T04:51:27Z",
        digest="",
        uploader_login="github-actions[bot]",
    )

    sorted_wheels = build_simple_index.sort_wheels([older_commit, newer_commit])

    assert [wheel.key for wheel in sorted_wheels] == ["new", "old"]


def test_from_csv_row_defaults_release_commit_at_to_empty():
    wheel = build_simple_index.WheelAsset.from_csv_row(
        {
            "key": "k",
            "release_tag": "v0.1.0",
            "release_published_at": "2022-01-01T00:00:00Z",
            "release_prerelease": "false",
            "asset_id": "1",
            "asset_name": "tzfpy-0.1.0.whl",
            "asset_url": "https://example.com/file.whl",
            "asset_updated_at": "2022-01-01T00:00:00Z",
            "asset_digest": "",
            "uploader_login": "ci",
        }
    )

    assert wheel.release_commit_at == ""


def test_parse_release_tag_key_orders_prerelease_before_final():
    rc_key = build_simple_index.parse_release_tag_key("v0.8.4rc1")
    final_key = build_simple_index.parse_release_tag_key("v0.8.4")
    alpha_key = build_simple_index.parse_release_tag_key("v1.1.3-alpha.2")

    assert rc_key is not None
    assert final_key is not None
    assert alpha_key is not None
    assert rc_key < final_key
    assert alpha_key < build_simple_index.parse_release_tag_key("v1.1.3")


def test_matches_filters_uses_min_release_tag():
    wheel = build_simple_index.WheelAsset(
        key="legacy",
        release_tag="v0.6.0",
        release_published_at="2026-03-14T09:03:14Z",
        release_commit_at="2022-07-31T15:52:51Z",
        release_prerelease=False,
        asset_id="1",
        name="tzfpy-0.6.0-cp310.whl",
        url="https://example.com/legacy.whl",
        updated_at="2026-03-14T09:03:13Z",
        digest="",
        uploader_login="github-actions[bot]",
    )

    assert not wheel.matches_filters(package_name="tzfpy", min_release_tag="v0.11.0")
    assert wheel.matches_filters(package_name="tzfpy", min_release_tag="v0.6.0")
