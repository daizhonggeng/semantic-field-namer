CREATE TABLE user_profile_demo (
  user_id bigint,
  mobile_no varchar(255),
  delete_flag boolean,
  created_at timestamp,
  user_name varchar(255)
);

COMMENT ON TABLE user_profile_demo IS '自动生成表';
COMMENT ON COLUMN user_profile_demo.user_id IS '用户编号';
COMMENT ON COLUMN user_profile_demo.mobile_no IS '联系电话';
COMMENT ON COLUMN user_profile_demo.delete_flag IS '删除标志';
COMMENT ON COLUMN user_profile_demo.created_at IS '创建时间';
COMMENT ON COLUMN user_profile_demo.user_name IS '用户名称';
