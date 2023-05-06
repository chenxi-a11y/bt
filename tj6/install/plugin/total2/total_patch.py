#!/usr/bin/python
# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyleft (c) 2015-2099 宝塔软件(http://bt.cn) All lefts reserved.
# +-------------------------------------------------------------------
# | Author: linxiao
# | Date: 2021/4/21 
# +-------------------------------------------------------------------
# +--------------------------------------------------------------------
# |   宝塔网站监控报表 - 更新补丁
# +--------------------------------------------------------------------
from __future__ import absolute_import, print_function, division
import datetime
import os
import sys
import time
import json
import re
import sqlite3
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from total_report import parse_logs_data

os.chdir("/www/server/panel")
sys.path.insert(0, "/www/server/panel/class")

import public
from tsqlite import tsqlite
from lua_maker import LuaMaker
import total_tools as tool
ISOLATION_LEVEL = "EXCLUSIVE"

_ver = sys.version_info
is_py2 = (_ver[0] == 2)
is_py3 = (_ver[0] == 3)

def get_log_db_path(site):
    db_path = os.path.join("/www/server/total", "logs/{}/logs.db".format(site))
    return db_path

keep_indexes = ['id_inx', 'time_inx']
migrating_file = "/www/server/total/migrating"

def check_database():
    ts = None
    try:
        # print("开始优化数据存储结构，优化后每个站点每天将减少26%~30%的磁盘占用空间。")
        print(tool.getMsg("TIPS_OPTIMIZE_DATA_STRUCTURE"))
        print(tool.getMsg("TIPS_WAITING"))
        public.writeFile(migrating_file, "migrating")
        sites = public.M('sites').field('name').order("addtime").select()
        for site_info in sites:
            site = site_info["name"]
            print(tool.getMsg("TIPS_CHECK_SITE", args=(site,)))
            db_path = get_log_db_path(site)
            if not os.path.isfile(db_path):
                continue
            ts = tsqlite()
            ts.ISOLATION_LEVEL = ISOLATION_LEVEL
            ts.dbfile(db_path)
            indexes = ts.query("select name from sqlite_master where type='index' and tbl_name='site_logs';")
            tips = {
                "id": "ID",
                "ip": "IP",
                "uri": "URL",
                "status_code": "状态码",
                "method": "请求方法"
            }
            drop = False
            for arr in indexes:
                index = arr[0]
                if index not in keep_indexes:
                    drop = True
                    # print("正在优化{}数据存储...".format(tips[index[0:index.find("_inx")]]))
                    print(tool.getMsg("TIPS_OPTIMIZE_DATA", args=(tips[index[0:index.find("_inx")]],)))
                    start = time.time()
                    ts.execute("DROP INDEX " + index)
                    end = time.time()
                    diff = end-start
                    if diff > 59:
                        # print("已完成，耗时:{}分{}秒".format(int(diff/60), round(diff%60)))
                        print(tool.getMsg("TIPS_COMPLETE_WITH_TIME", args=(int(diff/60), round(diff%60))))
                    else:
                        print(tool.getMsg("TIPS_COMPLETE_WITH_SECONDS", args=(round(diff),)))
                        # print("已完成，耗时:{}秒".format(round(diff)))
            if drop:
                # print("站点:{}已优化完成，未来新增数据将减少30%左右的存储空间。".format(site))
                print(tool.getMsg("TIPS_OPTIMIZE_SITE_COMPLETED", args=(site,)))
            # ts.execute("VACUUM;")
        # print("数据存储结构优化完成！")
        print(tool.getMsg("TIPS_OPTIMIZE_COMPLETED"))
        return True
                # print(columns)
    except Exception as e:
        # print(str(e))
        print(tool.getMsg("OPTIMIZE_ERROR", args=(str(e),)))
    finally:
        if os.path.isfile(migrating_file):
            os.remove(migrating_file)
        if ts:
            ts.close()
    return False

keep_columns = {
    "request_stat":["time", "req", "pv", "uv", "ip", "length", "spider"],
    "site_logs": ["is_spider", "request_headers", "ip_list"],
    "client_stat": ["other", "machine", "mobile"],
    "spider_stat": ["other", "mpcrawler", "yahoo", "duckduckgo"],
    "ip_stat": [],
    "uri_stat": [],
}
keep_columns_info = {
    "request_headers": "request_headers TEXT DEFAULT ''",
    "spider": "spider INTEGER DEFAULT 0",
    "is_spider": "is_spider INTEGER DEFAULT 0",
    "other": "other INTEGER DEFAULT 0",
    "machine": "machine INTEGER DEFAULT 0",
    "mobile": "mobile INTEGER DEFAULT 0",
    "ip_list": "ip_list TEXT DEFAULT ''",
    "mpcrawler": "mpcrawler INTEGER DEFAULT 0",
    "yahoo": "yahoo INTEGER DEFAULT 0",
    "duckduckgo": "duckduckgo INTEGER DEFAULT 0",
}
status_code_50x = [500, 501, 502, 503, 504, 505, 506, 507, 509, 510]
status_code_40x = [400, 401, 402, 403, 404, 405, 406, 407, 408, 409,
                   410, 411, 412, 413, 414, 415, 416, 417, 418, 421, 
                   422, 423, 424, 425, 426, 449, 451]
http_methods = ["get", "post", "put", "patch", "delete"]

# 添加状态列
for s in status_code_50x:
    column = "status_"+repr(s)
    keep_columns["request_stat"].append(column)
    keep_columns_info.update({column: column + " INTEGER DEFAULT 0"})

for s in status_code_40x:
    column = "status_"+repr(s)
    keep_columns["request_stat"].append(column)
    keep_columns_info.update({column: column + " INTEGER DEFAULT 0"})

# 添加请求方法列
for method in http_methods:
    column = "http_"+method
    keep_columns["request_stat"].append(column)
    keep_columns_info.update({column: column+" INTEGER DEFAULT 0"})

# 添加流量统计列
for i in range(1, 32):
    column = "flow"+repr(i)
    keep_columns["ip_stat"].append(column)
    keep_columns["uri_stat"].append(column)
    keep_columns_info.update({column: column+" INTEGER DEFAULT 0"})

# 添加URI蜘蛛流量列
for i in range(1, 32):
    column = "spider_flow"+repr(i)
    keep_columns["uri_stat"].append(column)
    keep_columns_info.update({column: column+" INTEGER DEFAULT 0"})


def get_timestamp_interval(local_time):
    start = None
    end = None
    start = time.mktime((local_time.tm_year, local_time.tm_mon, local_time.tm_mday, 0, 0, 0, 0, 0, 0))
    end = time.mktime((local_time.tm_year, local_time.tm_mon, local_time.tm_mday, 23, 59, 59, 0, 0, 0))
    return start, end

def get_last_days_by_timestamp(day):
    now = time.localtime()
    t1 = time.mktime((now.tm_year, now.tm_mon, now.tm_mday - day + 1, 0, 0, 0, 0, 0, 0))
    t2 = time.localtime(t1)
    start, _ = get_timestamp_interval(t2)
    _, end = get_timestamp_interval(now)
    return start, end

def get_time_interval(local_time):
    start = None
    end = None
    time_key_format = "%Y%m%d00"
    start = int(time.strftime(time_key_format, local_time))
    time_key_format = "%Y%m%d23"
    end = int(time.strftime(time_key_format, local_time))
    return start, end

def get_last_days(day):
    now = time.localtime()
    t1 = time.mktime((now.tm_year, now.tm_mon, now.tm_mday - day + 1, 0, 0, 0, 0, 0, 0))
    t2 = time.localtime(t1)
    start, _ = get_time_interval(t2)
    _, end = get_time_interval(now)
    return start, end

sync_logs = {}
def mark_sync(site, item):
    log_path = "/www/server/panel/plugin/total/sync.log"
    key = site+"_"+item
    origin_content = ""
    if os.path.isfile(log_path):
        origin_content = public.readFile(log_path)
    public.writeFile(log_path, origin_content + key+"\n")
    sync_logs[key] = True

def is_synced(site, item):
    log_path = "/www/server/panel/plugin/total/sync.log"
    if not os.path.isfile(log_path):
        return False
    if not sync_logs:
        lines = public.readFile(log_path)
        if lines:
            lines = lines.split("\n")
            for line in lines:
                sync_logs[line.strip()] = True
    key = site+"_"+item
    if key in sync_logs.keys():
        return True
    return False    

keep_tables = ["uri_stat", "ip_stat", "referer_stat"]
table_create_sqls = {
    "uri_stat": """
            CREATE TABLE uri_stat (
					uri_md5 CHAR(32) PRIMARY KEY,
					uri TEXT,
					day1 INTEGER DEFAULT 0,
					day2 INTEGER DEFAULT 0,
					day3 INTEGER DEFAULT 0,
					day4 INTEGER DEFAULT 0,
					day5 INTEGER DEFAULT 0,
					day6 INTEGER DEFAULT 0,
					day7 INTEGER DEFAULT 0,
					day8 INTEGER DEFAULT 0,
					day9 INTEGER DEFAULT 0,
					day10 INTEGER DEFAULT 0,
					day11 INTEGER DEFAULT 0,
					day12 INTEGER DEFAULT 0,
					day13 INTEGER DEFAULT 0,
					day14 INTEGER DEFAULT 0,
					day15 INTEGER DEFAULT 0,
					day16 INTEGER DEFAULT 0,
					day17 INTEGER DEFAULT 0,
					day18 INTEGER DEFAULT 0,
					day19 INTEGER DEFAULT 0,
					day20 INTEGER DEFAULT 0,
					day21 INTEGER DEFAULT 0,
					day22 INTEGER DEFAULT 0,
					day23 INTEGER DEFAULT 0,
					day24 INTEGER DEFAULT 0,
					day25 INTEGER DEFAULT 0,
					day26 INTEGER DEFAULT 0,
					day27 INTEGER DEFAULT 0,
					day28 INTEGER DEFAULT 0,
					day29 INTEGER DEFAULT 0,
					day30 INTEGER DEFAULT 0,
					day31 INTEGER DEFAULT 0,
					day32 INTEGER DEFAULT 0
				) """,
    "ip_stat": """CREATE TABLE ip_stat (
					ip CHAR(15) PRIMARY KEY,
					area CHAR(8) DEFAULT "",
					day1 INTEGER DEFAULT 0,
					day2 INTEGER DEFAULT 0,
					day3 INTEGER DEFAULT 0,
					day4 INTEGER DEFAULT 0,
					day5 INTEGER DEFAULT 0,
					day6 INTEGER DEFAULT 0,
					day7 INTEGER DEFAULT 0,
					day8 INTEGER DEFAULT 0,
					day9 INTEGER DEFAULT 0,
					day10 INTEGER DEFAULT 0,
					day11 INTEGER DEFAULT 0,
					day12 INTEGER DEFAULT 0,
					day13 INTEGER DEFAULT 0,
					day14 INTEGER DEFAULT 0,
					day15 INTEGER DEFAULT 0,
					day16 INTEGER DEFAULT 0,
					day17 INTEGER DEFAULT 0,
					day18 INTEGER DEFAULT 0,
					day19 INTEGER DEFAULT 0,
					day20 INTEGER DEFAULT 0,
					day21 INTEGER DEFAULT 0,
					day22 INTEGER DEFAULT 0,
					day23 INTEGER DEFAULT 0,
					day24 INTEGER DEFAULT 0,
					day25 INTEGER DEFAULT 0,
					day26 INTEGER DEFAULT 0,
					day27 INTEGER DEFAULT 0,
					day28 INTEGER DEFAULT 0,
					day29 INTEGER DEFAULT 0,
					day30 INTEGER DEFAULT 0,
					day31 INTEGER DEFAULT 0,
					day32 INTEGER DEFAULT 0
				) """,
    "referer_stat": """
        CREATE TABLE referer_stat(
            time INTEGER,
            domain TEXT,
            count INTEGER DEFAULT 0
        ) """
}

def check_table(ts):
    select_res = ts.execute("select name from sqlite_master where type='table';").fetchall()
    cur_tables = [t[0] for t in select_res]
    for new_table in keep_tables:
        if new_table not in cur_tables:
            if new_table in table_create_sqls.keys():
                sql = table_create_sqls[new_table]
                ts.execute(sql)

def alter_columns():
    try:
        ts = None
        conn = None
        error_count = 0
        # print("正在同步数据...")
        print(tool.getMsg("TIPS_SYNC_DATA"))
        # print("可能会耗费较长时间(与数据量、站点数量相关)，请耐心等待。")
        print(tool.getMsg("TIPS_WAITING"))
        sites = public.M('sites').field('name').order("addtime").select()
        for site_info in sites:
            try:
                public.writeFile(migrating_file, "migrating")
                site = site_info["name"]
                # if site != "www.163.com":
                #     continue
                # print("正在同步站点:{}".format(site))
                print(tool.getMsg("TIPS_SYNC_SITE_DATA", args=(site,)))
                site = site.replace("_", ".")
                db_path = get_log_db_path(site)
                if not os.path.isfile(db_path):
                    continue
                # ts = tsqlite()
                # ts.dbfile(db_path)
                import sqlite3
                conn = sqlite3.connect(db_path, isolation_level=ISOLATION_LEVEL)
                ts = conn.cursor()
                conn.execute("BEGIN TRANSACTION;")

                check_table(ts)

                for table_name, kcolumns in keep_columns.items():
                    columns = ts.execute(
                        "PRAGMA table_info([{}])".format(table_name))
                    columns = [column[1] for column in columns]
                    for column_name in kcolumns:
                        if column_name not in columns:
                            # print("检查列:" + column_name)
                            if column_name in keep_columns_info.keys():
                                column_info = keep_columns_info[column_name]
                                alter_sql = "ALTER TABLE {} ADD COLUMN {};".format(
                                    table_name, column_info)
                                ts.execute(alter_sql)
                                has_sync_action = True

                    if table_name == "spider_stat":
                        for column_name in columns:
                            if column_name.find("_flow") > 0: continue
                            if column_name == "time":continue
                            flow_column = column_name+"_flow"
                            if flow_column in columns: continue
                            alter_sql = "ALTER TABLE {} ADD COLUMN {} INTEGER DEFAULT 0".format("spider_stat", flow_column)
                            ts.execute(alter_sql)

                if not is_synced(site, "spider"):
                    # spider
                    start, end = get_last_days(30)
                    spiders = ts.execute(
                        "PRAGMA table_info([{}])".format("spider_stat"))
                    fields = ""
                    for s in spiders:
                        if s[1] == "time": continue
                        if fields:
                            fields += "+"
                        fields += s[1]
                    sync_sql = "select sum({}) as total, time from spider_stat where time between {} and {} group by time;"
                    sync_sql = sync_sql.format(fields, start, end)
                    # print("sync spider:" + sync_sql)
                    spider_data = ts.execute(sync_sql).fetchall()
                    for data in spider_data:
                        total = data[0]
                        time_key = data[1]
                        # print(total, time_key)
                        insert_sql = "INSERT INTO request_stat(time) SELECT {time_key} WHERE NOT EXISTS(SELECT time FROM request_stat WHERE time={time_key});".format(
                            time_key=time_key)
                        ts.execute(insert_sql)
                        ts.execute(
                            "UPDATE request_stat set {column}={column}+{total} where time={time_key}".format(
                                column="spider", total=total,
                                time_key=time_key))
                    mark_sync(site, "spider")
                    has_sync_action = True

                if not is_synced(site, "status_code"):
                    # 50x
                    start, end = get_last_days_by_timestamp(30)
                    status_codes = ",".join([str(status) for status in
                                             status_code_50x + status_code_40x])
                    # print("status codes:" + status_codes)
                    sync_sql = "select status_code, strftime('%Y%m%d%H', datetime(time, 'unixepoch')) as time1, count(*) from site_logs where time between {} and {} and status_code in ({}) group by time1, status_code"
                    # print("sync 50x:" +sync_sql.format(start, end))
                    data_status = ts.execute(
                        sync_sql.format(start, end, status_codes)).fetchall()
                    # print(len(data_500))
                    total_data = {}
                    for data in data_status:
                        status_code = int(data[0])
                        time_key = data[1]
                        count = data[2]
                        if time_key not in total_data.keys():
                            total_data[time_key] = {}
                        if status_code not in total_data[time_key].keys():
                            total_data[time_key][status_code] = count

                    # print("total data:")
                    # print(total_data)

                    for time_key, values in total_data.items():
                        insert_sql = "INSERT INTO request_stat(time) SELECT {time_key} WHERE NOT EXISTS(SELECT time FROM request_stat WHERE time={time_key});".format(
                            time_key=time_key)
                        ts.execute(insert_sql)
                        fields = ""
                        for status, count in values.items():
                            if fields: fields += ","
                            fields += "status_" + repr(
                                status) + "=" + "status_" + repr(
                                status) + "+" + repr(count)

                        ts.execute(
                            "UPDATE request_stat set {fields} where time={time_key}".format(
                                fields=fields, time_key=time_key))
                    mark_sync(site, "status_code")
                    has_sync_action = True

                if not is_synced(site, "http_method"):

                    start, end = get_last_days_by_timestamp(30)
                    method_conditions = ""
                    for m in http_methods:
                        if method_conditions: method_conditions += ","
                        method_conditions += "\'" + m.upper() + "\'"

                    # print("condition:" + method_conditions)
                    sync_sql = "select method, strftime('%Y%m%d%H', datetime(time, 'unixepoch')) as time1, count(*) from site_logs where time between {} and {} and method in ({}) group by time1, method"
                    sync_sql = sync_sql.format(start, end, method_conditions)
                    # print(sync_sql)
                    results = ts.execute(sync_sql).fetchall()
                    method_data = {}
                    for data in results:
                        method = data[0].lower()
                        time_key = str(data[1])
                        count = data[2]
                        if time_key not in method_data.keys():
                            method_data[time_key] = {}
                        if method not in method_data[time_key].keys():
                            method_data[time_key][method] = count

                    # print("method data")
                    # print(method_data)

                    for time_key, values in method_data.items():
                        insert_sql = "INSERT INTO request_stat(time) SELECT {time_key} WHERE NOT EXISTS(SELECT time FROM request_stat WHERE time={time_key});".format(
                            time_key=time_key)
                        ts.execute(insert_sql)
                        fields = ""
                        for method, count in values.items():
                            if fields: fields += ","
                            fields += "http_" + method + "=" + "http_" + method + "+" + repr(
                                count)
                        ts.execute(
                            "UPDATE request_stat set {fields} where time={time_key}".format(
                                fields=fields, time_key=time_key))

                    mark_sync(site, "http_method")
                    has_sync_action = True

                if not is_synced(site, "mobile"):

                    start, end = get_last_days(30)
                    select_sql = "select sum(android+iphone) as old_mobile, time from client_stat where time between {} and {} group by time".format(
                        start, end)
                    mobile_data = ts.execute(select_sql).fetchall()
                    for data in mobile_data:
                        total = data[0]
                        time_key = data[1]
                        # print(total, time_key)
                        insert_sql = "INSERT INTO client_stat(time) SELECT {time_key} WHERE NOT EXISTS(SELECT time FROM client_stat WHERE time={time_key});".format(
                            time_key=time_key)
                        ts.execute(insert_sql)
                        ts.execute(
                            "UPDATE client_stat set {column}={column}+{total} where time={time_key}".format(
                                column="mobile", total=total,
                                time_key=time_key))

                    mark_sync(site, "mobile")
                    has_sync_action = True

                try:
                    conn.execute("COMMIT;")
                except Exception as e:
                    err_msg = str(e)
                    if err_msg.find("no transaction is active") < 0:
                        print(site+" error:" + str(e))
            except Exception as e:
                print(site+" error:" + str(e))
                error_count += 1

        if os.path.isfile(migrating_file):
            os.remove(migrating_file)
        # print("数据同步完成。")
        print(tool.getMsg("TIPS_SYNC_COMPLETED"))
        return error_count == 0
    except Exception as e:
        print(tool.getMsg("TIPS_SYNC_ERROR", args=(str(e),)))
    finally:
        if os.path.isfile(migrating_file):
            os.remove(migrating_file)
        try:
            if ts:
                ts.close()
            if conn:
                conn.close()
        except:
            pass
    return False

def write_site_domains():
    sites = public.M('sites').field('name,id').select();
    my_domains = []
    for my_site in sites:
        tmp = {}
        tmp['name'] = my_site['name']
        tmp_domains = public.M('domain').where('pid=?',
                                               (my_site['id'],)).field(
            'name').select()
        tmp['domains'] = []
        for domain in tmp_domains:
            tmp['domains'].append(domain['name'])
        binding_domains = public.M('binding').where('pid=?',
                                                    (my_site['id'],)).field(
            'domain').select()
        for domain in binding_domains:
            tmp['domains'].append(domain['domain'])
        my_domains.append(tmp)
    config_domains = LuaMaker.makeLuaTable(my_domains)
    domains_str = "return " + config_domains
    public.WriteFile("/www/server/total/domains.lua", domains_str)
    return True

def sync_config():
    # print("正在同步配置...")
    print(tool.getMsg("TIPS_SYNC_SETTINGS"))
    config = json.loads(public.readFile("/www/server/total/config.json"))
    if "global" not in config.keys():
        os.system("mv /www/server/total/config.json /www/server/total/config.json.bak")
        os.system("cp /www/server/total/config/default_config.json /www/server/total/config.json")
        time.sleep(1)
        config = json.loads(public.readFile("/www/server/total/config.json"))

    global_config = config["global"]
    if "statistics_machine_access" not in global_config.keys():
        global_config["statistics_machine_access"] = True
    if "exclude_url" not in global_config.keys():
        global_config["exclude_url"] = []
    if "statistics_ip" not in global_config.keys():
        global_config["statistics_ip"] = True
    if "statistics_uri" not in global_config.keys():
        global_config["statistics_uri"] = True
    if "record_post_args" not in global_config.keys():
        global_config["record_post_args"] = False
    if "record_get_403_args" not in global_config.keys():
        global_config["record_get_403_args"] = False
    if "data_dir" not in global_config.keys():
        global_config["data_dir"] = "/www/server/total/logs"
    if "history_data_dir" not in global_config.keys():
        global_config["history_data_dir"] = "/www/server/total/logs"
    if "ip_top_num" not in global_config.keys():
        global_config["ip_top_num"] = 50
    if "uri_top_num" not in global_config.keys():
        global_config["uri_top_num"] = 50
    if "push_report" not in global_config.keys():
        global_config["push_report"] = False
    if "exclude_ip" not in global_config.keys():
        global_config["exclude_ip"] = []
    # config["global"] = global_config
    for site, site_config in config.items():
        if site.find("_") >= 0:
            config[site.replace("_", ".")] = site_config
            del config[site]
    task_config = "/www/server/panel/plugin/total/task_config.json"
    if os.path.exists(task_config):
        tconfig = json.loads(public.readFile(task_config))
        if "task_list" in tconfig:
            task_list = tconfig["task_list"]
            if "migrate_hot_logs" not in task_list:
                task_list.append("migrate_hot_logs")
                tconfig["task_list"] = task_list
                public.WriteFile(task_config, json.dumps(tconfig))

    public.writeFile("/www/server/total/config.json", json.dumps(config))
        
    lua_config = LuaMaker.makeLuaTable(config)
    lua_config = "return " + lua_config
    public.WriteFile("/www/server/total/total_config.lua", lua_config)
    write_site_domains()
    # print("配置同步完成。")
    print(tool.getMsg("TIPS_SYNC_SETTINGS_COMPLETED"))
    return True

def split_total_data(ori_db, new_db):
    """分离出统计表和所有数据"""
    total_tables = ["request_stat", "client_stat", "referer_stat", "uri_stat", "ip_stat", "spider_stat"]
    for table in total_tables:
        ori_conn = None
        ori_cur = None
        new_conn = None
        new_cur = None
        insert_sql = ""
        try:
            # 初始化表
            if not tool.init_db_from(ori_db, new_db, tables=table):
                return False

            # 逐行拷贝数据
            ori_conn = sqlite3.connect(ori_db)
            if sys.version_info[0] == 3:
                ori_conn.text_factory = lambda x: str(x, encoding="utf-8", errors='ignore')
            else:
                ori_conn.text_factory = lambda x: unicode(x, "utf-8", "ignore")
            ori_cur = ori_conn.cursor()

            new_conn = sqlite3.connect(new_db)
            new_cur = new_conn.cursor()
            new_cur.execute("BEGIN TRANSACTION")

            data_sql = "select * from {};".format(table)
            selector = ori_cur.execute(data_sql)
            data_line = selector.fetchone()
            while data_line:
                # params = ",".join(["\'"+str(field).replace("\'", "\\\'")+"\'" for field in data_line])
                params = ""
                for field in data_line:
                    if params:
                        params += ","
                    if type(field) == str:
                        field = "\'" + field.replace("\'", "\”") + "\'"
                    params += str(field)
                    
                insert_sql = "INSERT INTO {} VALUES({})".format(table, params)
                new_cur.execute(insert_sql)

                data_line = selector.fetchone()
            new_conn.commit()
            print("统计数据: {} 已迁移完成。".format(table))
        except Exception as e:
            print("统计数据: {} 迁移失败: {}".format(table, e))
            print(insert_sql)
            return False
        finally:
            ori_cur and ori_cur.close()
            ori_conn and ori_conn.close() 
            new_cur and new_cur.close()
            new_conn and new_conn.close()
    return True

def split_site_data(site_name, query_date="today"):
    """分离原日志数据库(logs.db)成两部分:
        历史日志(history_logs.db): 只包含今天以前的日志
        统计、今日日志(logs.db): 包含所有统计数据和今天的日志

        分离过程：
        从原logs.db中提取出所有统计数据和今天的日志数据,输出到new_logs.db
        重命名logs.db为history_logs.db,
        重命名new_logs.db为logs.db

        说明：
        分离只适合在用户首次升级时进行，不进行对历史部分的数据整理操作。

        @author: linxiao
        @time: 2021/12/3
    """
    query_start, query_end = tool.get_query_timestamp(query_date)
    data_dir = "/www/server/total/logs/%s/" % (site_name)
    ori_db_path = data_dir + "logs.db" 
    if not os.path.exists(ori_db_path):
        return public.returnMsg(True, "数据库未初始化。")

    new_logs_db = data_dir + "new_logs.db"
    history_logs_db = data_dir + "history_logs.db"

    new_conn = None
    new_cur = None
    conn = None
    cur = None
    
    insert_sql = ""
    try:
        import sqlite3

        # 只供测试
        # if os.path.exists(new_logs_db):
        #     os.remove(new_logs_db)

        new_conn = sqlite3.connect(new_logs_db)
        new_cur = new_conn.cursor()
        new_cur.execute("PRAGMA synchronous = 0")
        new_cur.execute("PRAGMA page_size = 4096")
        new_cur.execute("PRAGMA journal_mode = wal")
        new_cur.close()
        new_conn.close()

        # TODO: 处理失败情况
        # 1. 迁移统计数据
        if not split_total_data(ori_db_path, new_logs_db):
            return tool.returnMsg(False, "统计数据迁移失败！")

        # 2. 迁移当天日志数据
        # 初始化日志表
        if not tool.init_db_from(ori_db_path, new_logs_db, tables="site_logs"):
            return tool.returnMsg(False, "日志表初始化失败！")

        # 迁移日志
        new_conn = sqlite3.connect(new_logs_db)
        new_cur = new_conn.cursor()

        new_cur.execute("CREATE INDEX time_inx ON site_logs(time)")

        conn = sqlite3.connect(ori_db_path)
        if sys.version_info[0] == 3:
            conn.text_factory = lambda x: str(x, encoding="utf-8", errors='ignore')
        else:
            conn.text_factory = lambda x: unicode(x, "utf-8", "ignore")
        cur =  conn.cursor()
        logs_sql = "select * from site_logs where time>={} and time<={}".format(query_start, query_end)
        selector = cur.execute(logs_sql)
        log = selector.fetchone()
        while log:
            # params = ",".join(("\'" +str(field)+ "\'" for field in log))
            params = ""
            # p = False
            for field in log:
                if params:
                    params += ","
                if field is None:
                    field = "\'\'"
                    # p = True
                elif type(field) == str:
                    field = "\'" + field.replace("\'", "\”") + "\'"
                params += str(field)
            insert_sql = "INSERT INTO site_logs values("+params+")"
            # if p:
            #     print(insert_sql)
            new_cur.execute(insert_sql)
            log = selector.fetchone()
        new_conn.commit()

        # 删除已迁移过的日志
        cur.execute("delete from site_logs where time>={} and time<={}".format(query_start, query_end))
        conn.commit()

        cur and cur.close()
        conn and conn.close()
        new_cur and new_cur.close()
        new_conn and new_conn.close()

        cur = None
        conn = None
        new_cur = None
        new_conn = None
        print("网站:{} 日志和统计数据已分离完成。".format(site_name))

        # 3. 调换日志文件
        public.ExecShell("mv {} {}".format(ori_db_path, history_logs_db))
        public.ExecShell("mv {} {}".format(new_logs_db, ori_db_path))

        public.ExecShell("chown -R www:www "+ history_logs_db)
        public.ExecShell("chown -R www:www "+ ori_db_path)

        if os.path.exists(ori_db_path) and os.path.exists(history_logs_db):
            return public.returnMsg(True, "迁移数据成功！")
    except Exception as e:
        if insert_sql:
            print(insert_sql)
        print("分隔数据库异常: {}".format(e))
    finally:
        cur and cur.close()
        conn and conn.close()
        new_cur and new_cur.close()
        new_conn and new_conn.close()
        
    return public.returnMsg(False, "迁移数据失败！")

def split_data():
    """分离所有站点数据库"""
    success_flag_file = "/www/server/panel/plugin/total/split_success.pl"
    if os.path.exists(success_flag_file):
        print("数据已分离成功。")
        return True

    flag_file = "/www/server/panel/plugin/total/split_failed.pl"
    split_status = False
    sites = public.M('sites').field('name').order("addtime").select()
    try:
        for site_info in sites:
            site = site_info["name"]
            print("正在分离网站: {}".format(site))
            split_res = split_site_data(site, query_date="today")
            if not split_res["status"]:
                public.WriteFile(flag_file, time.time())
                return False
        split_status = True
    except:
        public.WriteFile(flag_file, time.time())
        split_status = False
    finally:
        if split_status: 
            if os.path.exists(flag_file):
                os.remove(flag_file)
            public.WriteFile(success_flag_file, time.time())
    return split_status

def write_process_white():
    """往堡塔加固添加进程白名单"""
    try:
        sysafe_config = "/www/server/panel/plugin/syssafe/config.json"
        if os.path.isfile(sysafe_config):
            config = None
            config = json.loads(public.readFile(sysafe_config))
            process_white = config["process"]["process_white"]
            process_name = "total_bloomd"
            if process_name not in process_white:
                process_white.append(process_name)
                if config:
                    public.writeFile(sysafe_config, json.dumps(config))
        return True
    except Exception as e:
        print(tool.getMsg("WRITE_SETTINGS_ERROR", args=(str(e),)))
    return False

def set_monitor_status(status):
    close_file = "/www/server/total/closing"
    if status == True:
        if os.path.isfile(close_file):
            os.remove(close_file)
        if os.path.isfile("/www/server/nginx/sbin/nginx"):
            os.system("cp /www/server/total/total_nginx.conf /www/server/panel/vhost/nginx/total.conf")
        if os.path.isfile("/www/server/apache/bin/httpd"):
            os.system("cp /www/server/total/total_httpd.conf /www/server/panel/vhost/apache/total.conf")
    else:
        public.WriteFile(close_file, "closing")
        os.system("rm -f /www/server/panel/vhost/nginx/total.conf")
        os.system("rm -f /www/server/panel/vhost/apache/total.conf")
    public.serviceReload()


def get_site_settings(site):
    """获取站点配置"""

    config_path = "/www/server/total/config.json"
    config = json.loads(public.readFile(config_path))

    res_config = {}
    if site not in config.keys():
        res_config = config["global"]
    else:
        res_config = config[site]

    for k, v in config["global"].items():
        if k not in res_config:
            res_config[k] = v
    return res_config

def write_lua_config(config=None):
    if not config:
        config = json.loads(public.readFile("/www/server/total/config.json"))
    lua_config = LuaMaker.makeLuaTable(config)
    lua_config = "return " + lua_config
    public.WriteFile("/www/server/total/total_config.lua", lua_config)

if __name__ == "__main__":
    now = ""
    monitor_status = True 
    config_path = "/www/server/total/config.json"
    try:
        settings = {}
        global_settings = {}
        if os.path.isfile(config_path):
            settings = json.loads(public.readFile(config_path))
            # print(settings)
            if "global" in settings:
                global_settings = settings["global"]
                monitor_status = global_settings["monitor"]

        # print("原监控状态:"+str(monitor_status))
        if monitor_status and global_settings:
            global_settings["monitor"] = False
            public.writeFile(config_path, json.dumps(settings))
            write_lua_config(settings)
            set_monitor_status(False)
            # print("监控报表已关闭。")
            print(tool.getMsg("TIPS_MONITOR_CLOSED"))

        excute_res1 = check_database()  
        excute_res2 = alter_columns()
        excute_res3 = sync_config()
        excute_res4 = write_process_white()
        from total_task import create_background_task
        excute_res5 = create_background_task()
        excute_res6 = split_data()
        from total_report import init_db as init_report_db
        init_report_db()
        now = datetime.datetime.now().strftime("%Y%m%d %H:%M:%S")
        if excute_res1 and excute_res2 and excute_res3 and excute_res4 and excute_res5 and excute_res6:
            # print("[{}] 补丁执行成功。".format(now))
            print(tool.getMsg("TIPS_PATCH_SUCCESSFUL", args=(now,)))
        else:
            # print("优化数据结构:{}".format(excute_res1))
            print(tool.getMsg("TIPS_OPTIMIZE_RESULT", args=(excute_res1,)))
            # print("同步数据:{}".format(excute_res2))
            print(tool.getMsg("TIPS_SYNC_RESULT", args=(excute_res2,)))
            # print("同步配置:{}".format(excute_res3))
            print(tool.getMsg("TIPS_SYNC_SETTING_RESULT", args=(excute_res3,)))
            # print("写入白名单进程:{}".format(excute_res4))
            print(tool.getMsg("TIPS_WRITE_SETTINGS_RESULT", args=(excute_res4,)))
            # print("加入后台定时任务:{}".format(excute_res5))
            print(tool.getMsg("TIPS_ADD_BACKGROUND_TASK_RESULT", args=(excute_res5,)))
            # print("[{}] ******补丁执行失败！可能会影响到插件正常使用，请在https://www.bt.cn/bbs发帖或者联系开发者寻求支持。******".format(now))
            print(tool.getMsg("TIPS_SEPARATION_FAILURE", args=(excute_res6,)))
            print(tool.getMsg("TIPS_PATCH_FAILED", args=(now,)))
    except Exception as e:
        print(tool.getMsg("TIPS_PATCH_ERROR", args=(now, str(e),)))
    finally:
        if monitor_status and settings:
            settings = json.loads(public.readFile(config_path))
            global_settings = settings["global"]
            global_settings["monitor"] = True
            public.writeFile(config_path, json.dumps(settings))
            write_lua_config(settings)
            set_monitor_status(True)
            print(tool.getMsg("TIPS_MONITOR_OPENED"))