create table t_land_supply_case
(
    parcel_no varchar(255),
    parcel_name varchar(255),
    parcel_location varchar(255),
    project_name varchar(255),
    land_use varchar(255),
    supply_area numeric(18, 2),
    geometry_data_source varchar(255),
    administrative_division_code varchar(255),
    approval_authority varchar(255),
    approval_document_no varchar(255),
    parent_block_notice_no varchar(255),
    block_notice_no varchar(255),
    acquisition_method varchar(255),
    centralized_land_supply_year varchar(255)
);

comment on table t_land_supply_case is '土地直供案例';

comment on column t_land_supply_case.parcel_no is '地块编号';
comment on column t_land_supply_case.parcel_name is '地块名称';
comment on column t_land_supply_case.parcel_location is '地块坐落';
comment on column t_land_supply_case.project_name is '项目名称';
comment on column t_land_supply_case.land_use is '土地用途';
comment on column t_land_supply_case.supply_area is '供地面积';
comment on column t_land_supply_case.geometry_data_source is '图形数据来源';
comment on column t_land_supply_case.administrative_division_code is '行政区划代码';
comment on column t_land_supply_case.approval_authority is '批准机关';
comment on column t_land_supply_case.approval_document_no is '批准文号';
comment on column t_land_supply_case.parent_block_notice_no is '地块公告号';
comment on column t_land_supply_case.block_notice_no is '子地块公告号';
comment on column t_land_supply_case.acquisition_method is '拿地方式';
comment on column t_land_supply_case.centralized_land_supply_year is '集中供地年份';
