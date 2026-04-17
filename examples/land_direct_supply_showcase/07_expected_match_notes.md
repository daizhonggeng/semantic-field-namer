# Expected Match Notes

## Exact

- 地块名称 -> `parcel_name`
- 地块编号 -> `parcel_no`
- 项目名称 -> `project_name`
- 地块公告号 -> `parent_block_notice_no`
- 子地块公告号 -> `block_notice_no`
- 批准机关 -> `approval_authority`
- 土地用途 -> `land_use`
- 集中供地年份 -> `centralized_land_supply_year`
- 集中供地批次 -> `centralized_land_supply_batch`
- 集中供地轮次 -> `centralized_land_supply_round`
- 高品质竞赛结果 -> `high_quality_competition_result`
- 三大先导产业名称 -> `three_major_pilot_industry_name`
- 六大重点产业名称 -> `six_key_industry_name`
- 国民经济行业分类中类 -> `national_economy_industry_medium_category`

## Lexical

- 图形数据源 -> `geometry_data_source`
- 行政区代码 -> `administrative_division_code`

## Semantic

- 用地面积 -> likely reuse `supply_area`

This depends on embedding availability and threshold configuration.

## LLM fallback

- 地块竞得热度指数 -> likely a new term, expected to use model fallback

The exact final name may vary by active model/provider, but it should remain snake_case and consistent with the project style.
