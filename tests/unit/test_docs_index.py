from scripts.check_docs_index import missing_index_links


def test_docs_index_links_exist() -> None:
    assert missing_index_links() == []
