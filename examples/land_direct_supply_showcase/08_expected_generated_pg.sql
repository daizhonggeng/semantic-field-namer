CREATE TABLE t_land_supply_case_generated (
  parcel_name varchar(255),
  parcel_no bigint,
  project_name varchar(255),
  parent_block_notice_no varchar(255),
  block_notice_no varchar(255),
  geometry_data_source varchar(255),
  administrative_division_code varchar(255),
  approval_authority varchar(255),
  land_use varchar(255),
  centralized_land_supply_year varchar(255),
  centralized_land_supply_batch varchar(255),
  centralized_land_supply_round varchar(255),
  high_quality_competition_result varchar(255),
  three_major_pilot_industry_name varchar(255),
  six_key_industry_name varchar(255),
  national_economy_industry_medium_category varchar(255),
  supply_area varchar(255),
  land_bid_heat_index varchar(255)
);

COMMENT ON TABLE t_land_supply_case_generated IS '自动生成表';
COMMENT ON COLUMN t_land_supply_case_generated.parcel_name IS '地块名称';
COMMENT ON COLUMN t_land_supply_case_generated.parcel_no IS '地块编号';
COMMENT ON COLUMN t_land_supply_case_generated.project_name IS '项目名称';
COMMENT ON COLUMN t_land_supply_case_generated.parent_block_notice_no IS '地块公告号';
COMMENT ON COLUMN t_land_supply_case_generated.block_notice_no IS '子地块公告号';
COMMENT ON COLUMN t_land_supply_case_generated.geometry_data_source IS '图形数据源';
COMMENT ON COLUMN t_land_supply_case_generated.administrative_division_code IS '行政区代码';
COMMENT ON COLUMN t_land_supply_case_generated.approval_authority IS '批准机关';
COMMENT ON COLUMN t_land_supply_case_generated.land_use IS '土地用途';
COMMENT ON COLUMN t_land_supply_case_generated.centralized_land_supply_year IS '集中供地年份';
COMMENT ON COLUMN t_land_supply_case_generated.centralized_land_supply_batch IS '集中供地批次';
COMMENT ON COLUMN t_land_supply_case_generated.centralized_land_supply_round IS '集中供地轮次';
COMMENT ON COLUMN t_land_supply_case_generated.high_quality_competition_result IS '高品质竞赛结果';
COMMENT ON COLUMN t_land_supply_case_generated.three_major_pilot_industry_name IS '三大先导产业名称';
COMMENT ON COLUMN t_land_supply_case_generated.six_key_industry_name IS '六大重点产业名称';
COMMENT ON COLUMN t_land_supply_case_generated.national_economy_industry_medium_category IS '国民经济行业分类中类';
COMMENT ON COLUMN t_land_supply_case_generated.supply_area IS '用地面积';
COMMENT ON COLUMN t_land_supply_case_generated.land_bid_heat_index IS '地块竞得热度指数';
