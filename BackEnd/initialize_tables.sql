DROP TABLE IF EXISTS grp;
CREATE TABLE grp (
  id integer primary key autoincrement,
  name text,
  total_weight real
);

INSERT INTO grp(id,name,total_weight) VALUES (1,'grp1',2.0);
INSERT INTO grp(id,name,total_weight) VALUES (2,'grp2',2.0);

DROP TABLE IF EXISTS task;
CREATE TABLE task (
   id integer primary key autoincrement,
   group_id integer,
   mean_weight real,
   desc TEXT,
   FOREIGN KEY (group_id) REFERENCES grp(id)
);
INSERT INTO task(id,group_id,mean_weight,desc) VALUES (1,1,2.0,'Test Desc 1');
INSERT INTO task(id,group_id,mean_weight,desc) VALUES (2,2,3.0,'Test Desc 2');

DROP TABLE IF EXISTS member;
CREATE TABLE member(
  id integer primary key autoincrement,
  user_name text
);
INSERT INTO member(id,user_name) VALUES (1,'ankur');
INSERT INTO member(id,user_name) VALUES (2,'abhiram');


DROP TABLE IF EXISTS member_task;
CREATE TABLE member_task(
  member_id integer,
  task_id integer,
  voted_weight real,
  task_done  integer,
  weight_contribution real,
  PRIMARY KEY (member_id,task_id),
  FOREIGN KEY (member_id) REFERENCES member(id),
  FOREIGN KEY (task_id) REFERENCES task(id)
);

INSERT INTO member_task(member_id,task_id,task_done,weight_contribution) VALUES (1,1,1,0.0);
INSERT INTO member_task(member_id,task_id,task_done,weight_contribution) VALUES (2,1,0,0.0);

DROP TABLE IF EXISTS group_member;
CREATE TABLE group_member(
  member_id integer,
  group_id integer,
  weight real,
  PRIMARY KEY (member_id,group_id),
  FOREIGN KEY (member_id) REFERENCES member(id),
  FOREIGN KEY (group_id) REFERENCES grp(id)
);

INSERT INTO group_member(member_id,group_id,weight) VALUES (1,1,2.0);

DROP TABLE IF EXISTS account_details;
CREATE TABLE account_details(
  username text,
  password text,
  user_id  int,
  PRIMARY KEY (username,password)
);
INSERT INTO account_details (username, password, user_id) VALUES ('ankur@umass','ankur',1);
INSERT INTO account_details (username, password, user_id) VALUES ('abhiram@umass','abhiram',2);
INSERT INTO account_details (username, password, user_id) VALUES ('abhay@umass','abhay',3);
INSERT INTO account_details (username, password, user_id) VALUES ('suraj@umass','suraj',4);





