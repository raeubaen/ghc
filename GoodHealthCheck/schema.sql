drop table if exists flags
create table flags (channel_id INTEGER NOT NULL, flag TEXT NOT NULL, PRIMARY KEY (channel_id, flag))
drop table if exists flags_description
create table flags_description (flag TEXT NOT NULL PRIMARY KEY, description TEXT NOT NULL)
drop table if exists runs
create table runs (run_num INTEGER NOT NULL, run_type TEXT NOT NULL, comment TEXT DEFAULT "")
drop table if exists all_channels
create table all_channels (channel_id INTEGER PRIMARY KEY NOT NULL, location TEXT)
drop table if exists missed_channels
create table missed_channels (channel_id INTEGER PRIMARY KEY)
drop table if exists data_pedestal_hvon
create table data_pedestal_hvon (channel_id INTEGER, key TEXT, value REAL, PRIMARY KEY (channel_id, key))
drop table if exists data_testpulse
create table data_testpulse (channel_id INTEGER, key TEXT, value REAL, PRIMARY KEY (channel_id, key))
drop table if exists data_laser
create table data_laser (channel_id INTEGER, key TEXT, value REAL, PRIMARY KEY (channel_id, key))
drop table if exists data_pedestal_hvoff
create table data_pedestal_hvoff (channel_id INTEGER, key TEXT, value REAL, PRIMARY KEY (channel_id, key))
drop table if exists options
create table options (name TEXT NOT NULL PRIMARY KEY, value)
drop index if exists ichannels
create index ichannels on all_channels (channel_id)
drop index if exists ipon
create index ipon on data_pedestal_hvon (channel_id, key)
drop index if exists ipoff
create index ipoff on data_pedestal_hvoff (channel_id, key)
drop index if exists itp
create index itp on data_testpulse (channel_id, key)
drop index if exists il
create index il on data_laser (channel_id, key)
drop index if exists iflags
create index iflags on flags (channel_id)
