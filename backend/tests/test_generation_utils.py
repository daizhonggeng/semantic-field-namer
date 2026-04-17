from app.services.normalization import normalize_comment, similarity, snake_case


def test_normalize_comment_merges_synonyms():
    assert normalize_comment("用户编号") == normalize_comment("用户ID")


def test_similarity_matches_phone_variants():
    assert similarity("手机号", "联系电话") >= 0.5


def test_snake_case_output():
    assert snake_case("DeleteFlag") == "delete_flag"
