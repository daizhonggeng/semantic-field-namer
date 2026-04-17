create table user_profile
(
    user_id bigint,
    mobile_no varchar(64),
    delete_flag varchar(8),
    created_at timestamp
);

comment on table user_profile is '用户档案';

comment on column user_profile.user_id is '用户编号';
comment on column user_profile.mobile_no is '联系电话';
comment on column user_profile.delete_flag is '删除标志';
comment on column user_profile.created_at is '创建时间';
