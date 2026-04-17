CREATE TABLE user_profile (
  user_id bigint,
  mobile_no varchar(64),
  delete_flag varchar(8)
);

COMMENT ON TABLE user_profile IS '用户档案';
COMMENT ON COLUMN user_profile.user_id IS '用户编号';
COMMENT ON COLUMN user_profile.mobile_no IS '联系电话';
COMMENT ON COLUMN user_profile.delete_flag IS '删除标志';
