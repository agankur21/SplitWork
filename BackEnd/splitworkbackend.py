import os
from sqlite3 import dbapi2 as sqlite3
import json as js
import sys
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, jsonify
import random

# create our little application :)
app = Flask(__name__)
DATABASE = 'splitwork.db'
DATABASE_RESOURCE = 'initialize_tables.sql'

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, DATABASE),
    DEBUG=True
))

"""
Initializing functions for Database connections
"""


def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def init_db():
    """Initializes the database."""
    with app.app_context():
        db = get_db()
        with app.open_resource(DATABASE_RESOURCE, mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


@app.cli.command('initdb')
def initdb_command():
    """Creates the database tables."""
    init_db()
    print('Initialized the database.')


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


"""
Define API end Points
"""


@app.route("/", methods=["GET"])
def get_my_ip():
    return jsonify({'ip': request.remote_addr}), 200


@app.route('/login', methods=['POST'])
def get_user_id():
    if request.headers['Content-Type'] == 'application/json':
        data_json = request.data
        data = js.loads(data_json)
        user_name = data['userName']
        password = data['password']
        sql_query = "select user_id from account_details where username = '%s' and password ='%s'" % (
            user_name, password)
        out = query_db(sql_query)
        if (out is not None) and (len(out) > 0):
            return jsonify(userId=out[0]['user_id']), 200
        else:
            return ""
    else:
        return "415 Unsupported Media Type"


@app.route('/member/groups', methods=['GET'])
def get_member_groups():
    user_id = request.args["userid"]
    sql_query = "select member.user_name as user_name,group_id,grp.name as group_name from group_member inner join member on member.id = group_member.member_id inner join grp on grp.id = group_member.group_id  where group_member.member_id = %s" % (
        user_id)
    out = query_db(sql_query)
    if (out is not None) and (len(out) > 0):
        out_dict = {}
        out_dict['groups'] = []
        for item in out:
            user_name = item['user_name']
            out_dict["userName"] = user_name
            temp_dict = {}
            temp_dict["groupId"] = item['group_id']
            temp_dict["groupName"] = item['group_name']
            out_dict['groups'].append(temp_dict)
        jsonString = js.dumps(out_dict, indent=2, separators=(',', ': '))
        return jsonString, 200
    else:
        return ""


@app.route('/member/tasks', methods=['GET'])
def get_member_tasks():
    user_id = request.args["userid"]
    sql_query = "select grp.name as group_name,grp.id as group_id, T1.task_id as task_id,T1.task_desc as task_desc, T1.task_done as task_done from (select task.group_id as group_id,member_task.task_id as task_id,member_task.task_done as task_done,task.desc as task_desc from member_task inner join task where task.id = member_task.task_id and member_task.member_id= %s)T1 inner join grp where T1.group_id=grp.id" % (
        user_id)
    out = query_db(sql_query)
    if (out is not None) and (len(out) > 0):
        out_dict = []
        for item in out:
            temp_dict = {}
            temp_dict['taskId'] = item['task_id']
            temp_dict["taskDesc"] = item['task_desc']
            temp_dict["groupId"] = item['group_id']
            temp_dict["groupName"] = item['group_name']
            temp_dict["isDone"] = item['task_done']
            out_dict.append(temp_dict)
        jsonString = js.dumps(out_dict, indent=2, separators=(',', ': '))
        return jsonString
    else:
        return ""


@app.route('/member/group', methods=['GET'])
def get_member_group():
    user_id = request.args["userid"]
    group_id = request.args["groupid"]
    sql_query = "select grp.name as group_name,member.user_name as user_name,T3.member_id as user_id,T3.weight as weight,T3.task_id as task_id,T3.task_desc as task_desc, T3.task_done as task_done FROM (SELECT group_id,group_member.member_id as member_id,weight,T2.task_desc as task_desc,T2.task_id as task_id,T2.task_done as task_done FROM group_member INNER JOIN (SELECT task.desc as task_desc, member_task.member_id as member_id,task.id as task_id, member_task.task_done as task_done FROM task INNER JOIN member_task ON (task.id = member_task.task_id) WHERE task.group_id = %s and member_task.member_id = %s)T2 ON ( T2.member_id= group_member.member_id))T3 INNER JOIN grp ON (T3.group_id = grp.id)  INNER JOIN member on (T3.member_id = member.id)" % (
        group_id, user_id)
    out = query_db(sql_query)
    if (out is not None) and (len(out) > 0):
        out_dict = {}
        out_dict["members"] = []
        out_dict["tasks"] = []
        for item in out:
            temp_dict1 = {}
            temp_dict2 = {}
            out_dict["groupName"] = item['group_name']
            temp_dict2['taskId'] = item['task_id']
            temp_dict2["taskDesc"] = item['task_desc']
            temp_dict2["isDone"] = item['task_done']
            temp_dict1["userName"] = item['user_name']
            temp_dict1["userId"] = item['user_id']
            temp_dict1["totalWeight"] = item['weight']
            out_dict["members"].append(temp_dict1)
            out_dict["tasks"].append(temp_dict2)
        jsonString = js.dumps(out_dict, indent=2, separators=(',', ': '))
        return jsonString
    else:
        return ""


@app.route('/group/task/create', methods=['GET'])
def create_task():
    group_id = request.args["groupid"]
    description = request.args["desc"]
    task_id = random.randint(1, sys.maxint)
    sql_create_task = "insert into task(id,group_id,mean_weight,desc) values(%s,%s,0.0,'%s')" % (
    task_id, group_id, description)
    query_db(sql_create_task)
    sql_create_member_task = ""
    sql_get_all_users_group = "select member_id from group_member where group_id =%s" % (group_id)
    users = query_db(sql_get_all_users_group)
    if (users is not None) and (len(users) > 0):
        for user in users:
            user_id = user['member_id']
            sql_create_member_task += "insert into member_task(member_id,task_id,task_done,weight_contribution) values(%d,%d,0,0.0);" % (
            user_id, task_id)
    query_db(sql_create_member_task)
    return "{\"taskId\" : %d}" % task_id, 200


@app.route('/member/create', methods=['POST'])
def create_member():
    if request.headers['Content-Type'] == 'application/json':
        data_json = request.data
        data = js.loads(data_json)
        username = data['userName']
        password = data['password']
        user_id = random.randint(1, sys.maxint)
        sql_create_account = "INSERT INTO account_details (username, password, user_id) SELECT '%s','%s',%d WHERE NOT EXISTS(SELECT 1 FROM account_details where username='%s' and password = '%s')" % (username, password,user_id,username,password)
        query_db(sql_create_account)
        sql_create_member = "INSERT INTO member(id,user_name) VALUES(%d,'%s')" %(user_id,username)
        query_db(sql_create_member)
        return "{\"userId\" : %d}" % user_id, 200
    else:
        return "415 Unsupported Media Type"



@app.route('/member/task/vote', methods=['POST'])
def update_member_task_vote():
    if request.headers['Content-Type'] == 'application/json':
        data_json = request.data
        data = js.loads(data_json)
        user_id = data['userId']
        task_id = data['taskId']
        vote_weight = data['vote']
        sql_query_update_vote = "update member_task set voted_weight = %f where member_id = %d and task_id = %d;" % (
            vote_weight, user_id, task_id)
        sql_query_get_mean_weight = "select avg(voted_weight) as weight from member_task where task_id=%d ;" % (task_id)
        query_db(sql_query_update_vote)
        average_weight = query_db(sql_query_get_mean_weight)[0]['weight']
        sql_query_update_mean_weight = "update task set mean_weight= %f where id = %d" % (average_weight, task_id)
        query_db(sql_query_update_mean_weight)
        out = query_db("select sum(task_done) as count from member_task where task_id= %s" % (task_id))
        num_people_contributed = out[0]['count']
        query_db("update member_task set weight_contribution = %f/%d*task_done where task_id = %s" % (average_weight, num_people_contributed, task_id))
        users = query_db(
            "select member_id,group_id,sum(weight_contribution) as weight from member_task inner join task on (task.id=member_task.task_id)  where task_id=%s group by member_id,group_id" % task_id)
        if (users is not None) and (len(users) > 0):
            for user in users:
                user_id = user['member_id']
                weight = user['weight']
                group_id = user['group_id']
                update_weight_query = "update group_member set weight= %f where member_id=%d and group_id = %d;" % (
                weight, user_id, group_id)
                query_db(update_weight_query)
        return "Done!!!", 200
    else:
        return "415 Unsupported Media Type"

@app.route('/member/task/involved',methods=['GET'])
def update_member_task_involvement():
    user_id = request.args["userid"]
    task_id = request.args["taskid"]
    sql_update_task_done = "update member_task set task_done=1 where member_id =%s and task_id =%s" %(user_id,task_id)
    query_db(sql_update_task_done)
    out =query_db("select sum(task_done) as count from member_task where task_id= %s" %(task_id))
    num_people_contributed=out[0]['count']
    out = query_db("select mean_weight from task where id= %s" %task_id)
    mean_weight_task=out[0]['mean_weight']
    query_db("update member_task set weight_contribution = %f/%d*task_done where task_id = %s" %(mean_weight_task,num_people_contributed,task_id))
    users = query_db("select member_id,group_id,sum(weight_contribution) as weight from member_task inner join task on (task.id=member_task.task_id)  where task_id=%s group by member_id,group_id" %task_id )
    if(users is not None) and (len(users) > 0):
        for user in users:
            user_id = user['member_id']
            weight = user['weight']
            group_id=user['group_id']
            update_weight_query = "update group_member set weight= %f where member_id=%d and group_id = %d;" %(weight,user_id,group_id)
            query_db(update_weight_query)
    return "Done!!!" ,200

@app.route('/group/member/add',methods=['GET'])
def add_member_group():
    print request.args
    user_id = request.args["userid"]
    group_id = request.args["groupid"]
    query_db("insert into group_member(member_id,group_id,weight) values (%s,%s,0.0)" %(user_id,group_id))
    return "Done!!!\n",200



if __name__ == '__main__':
    init_db()
    app.run(
        host="128.119.180.165",
        port=int("8080"),
        debug=True
    )
